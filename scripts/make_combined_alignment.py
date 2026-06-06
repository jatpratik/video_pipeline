import json
import logging
import subprocess
import shutil
import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)-7s] %(message)s")
logger = logging.getLogger("video_pipeline.combined_alignment")

def _free_gpu(device: str):
    if device == "cuda":
        import gc
        import torch
        gc.collect()
        torch.cuda.empty_cache()

def extract_audio(video_path: Path, audio_output_path: Path):
    logger.info(f"Extracting audio from {video_path.name} to {audio_output_path.name}...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")

def run_alignment(
    audio_path: Path,
    device: str = "cpu",
    model_name: str = "large-v3-turbo",
    compute_type: str = "float32",
    batch_size: int = 4,
) -> dict:
    import whisperx

    logger.info(f"Loading audio: {audio_path}")
    audio = whisperx.load_audio(str(audio_path))

    logger.info(f"Loading WhisperX model '{model_name}' on {device} (compute_type={compute_type})")
    model = whisperx.load_model(model_name, device, compute_type=compute_type)

    logger.info("Transcribing audio...")
    result = model.transcribe(audio, batch_size=batch_size)
    detected_language = result.get("language", "en")
    logger.info(f"Detected language: {detected_language}")

    del model
    _free_gpu(device)

    logger.info("Loading alignment model...")
    model_a, metadata = whisperx.load_align_model(language_code=detected_language, device=device)

    logger.info("Running forced alignment for word-level timestamps...")
    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    del model_a
    _free_gpu(device)

    # Structure segments
    segments = []
    for seg in result.get("segments", []):
        words = []
        for w in seg.get("words", []):
            if "start" in w and "end" in w:
                words.append({
                    "word": w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3),
                    "score": round(w.get("score", 0.0), 3),
                })
        if not words:
            continue
        segments.append({
            "text": seg.get("text", "").strip(),
            "start": round(seg.get("start", words[0]["start"]), 3),
            "end": round(seg.get("end", words[-1]["end"]), 3),
            "words": words,
        })
    return {"segments": segments}

def main():
    device = config.DEVICE
    model_name = config.WHISPERX_MODEL
    compute_type = config.WHISPERX_COMPUTE_TYPE
    batch_size = config.WHISPERX_BATCH_SIZE

    # 1. Paths
    hook_video = config.INPUT_DIR / "start_hook.mp4"
    student_video = config.INPUT_DIR / "student_speaking.mp4"
    voice_audio = config.INPUT_DIR / "voice.wav"

    hook_wav = config.TIMESTAMPS_DIR / "start_hook.wav"
    student_wav = config.TIMESTAMPS_DIR / "student_speaking.wav"

    # 2. Extract audio
    extract_audio(hook_video, hook_wav)
    extract_audio(student_video, student_wav)

    # 3. Align each track
    logger.info("--- Aligning Hook Video Audio ---")
    hook_alignment = run_alignment(hook_wav, device, model_name, compute_type, batch_size)
    
    logger.info("--- Aligning Student Speaking Video Audio ---")
    student_alignment = run_alignment(student_wav, device, model_name, compute_type, batch_size)
    
    logger.info("--- Aligning Narrator Audio ---")
    voice_alignment = run_alignment(voice_audio, device, model_name, compute_type, batch_size)

    # Save individual alignments for debugging
    with open(config.TIMESTAMPS_DIR / "start_hook_alignment.json", "w", encoding="utf-8") as f:
        json.dump(hook_alignment, f, indent=2, ensure_ascii=False)
    with open(config.TIMESTAMPS_DIR / "student_speaking_alignment.json", "w", encoding="utf-8") as f:
        json.dump(student_alignment, f, indent=2, ensure_ascii=False)
    with open(config.TIMESTAMPS_DIR / "voice_alignment.json", "w", encoding="utf-8") as f:
        json.dump(voice_alignment, f, indent=2, ensure_ascii=False)

    # 4. Merge into combined timeline
    # Timing parameters:
    # Segment A: Hook (0.0s -> 9.5s)
    #   - hook alignment starts at visual 0.0s
    # Segment B: Narrator Part 1 (9.5s -> 101.115s)
    #   - voice alignment starts at visual 9.5s
    #   - split at unshifted narrator time 91.615s
    # Segment C: Student Speaking (101.115s -> 111.115s)
    #   - student alignment starts at visual 102.115s (due to 1.0s padding_start)
    # Segment D: Narrator Part 2 (111.115s -> 144.724s)
    #   - voice alignment after 91.615s starts at visual 111.115s (shift of 19.5s)

    combined_segments = []

    # A. Hook
    for seg in hook_alignment["segments"]:
        shifted_seg = {
            "text": seg["text"],
            "start": round(seg["start"] + 0.0, 3),
            "end": round(seg["end"] + 0.0, 3),
            "words": []
        }
        for w in seg["words"]:
            shifted_seg["words"].append({
                "word": w["word"],
                "start": round(w["start"] + 0.0, 3),
                "end": round(w["end"] + 0.0, 3)
            })
        combined_segments.append(shifted_seg)

    # B. Narrator Part 1 (start < 91.615)
    for seg in voice_alignment["segments"]:
        if seg["start"] < 91.615:
            shifted_seg = {
                "text": seg["text"],
                "start": round(seg["start"] + 9.5, 3),
                "end": round(seg["end"] + 9.5, 3),
                "words": []
            }
            for w in seg["words"]:
                shifted_seg["words"].append({
                    "word": w["word"],
                    "start": round(w["start"] + 9.5, 3),
                    "end": round(w["end"] + 9.5, 3)
                })
            combined_segments.append(shifted_seg)

    # C. Student Speaking
    for seg in student_alignment["segments"]:
        shifted_seg = {
            "text": seg["text"],
            "start": round(seg["start"] + 102.115, 3),
            "end": round(seg["end"] + 102.115, 3),
            "words": []
        }
        for w in seg["words"]:
            shifted_seg["words"].append({
                "word": w["word"],
                "start": round(w["start"] + 102.115, 3),
                "end": round(w["end"] + 102.115, 3)
            })
        combined_segments.append(shifted_seg)

    # D. Narrator Part 2 (start >= 91.615)
    for seg in voice_alignment["segments"]:
        if seg["start"] >= 91.615:
            shifted_seg = {
                "text": seg["text"],
                "start": round(seg["start"] + 19.5, 3),
                "end": round(seg["end"] + 19.5, 3),
                "words": []
            }
            for w in seg["words"]:
                shifted_seg["words"].append({
                    "word": w["word"],
                    "start": round(w["start"] + 19.5, 3),
                    "end": round(w["end"] + 19.5, 3)
                })
            combined_segments.append(shifted_seg)

    # Sort segments by start time
    combined_segments.sort(key=lambda x: x["start"])

    combined_data = {"segments": combined_segments}

    # Save to combined_alignment.json
    combined_json_path = config.TIMESTAMPS_DIR / "combined_alignment.json"
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved combined alignment JSON to {combined_json_path}")

    # Generate JS captions file
    js_segments = []
    for seg in combined_segments:
        js_seg = {
            "text": seg["text"],
            "start": seg["start"],
            "end": seg["end"],
            "words": []
        }
        for w in seg["words"]:
            js_seg["words"].append({
                "text": w["word"],
                "start": w["start"],
                "end": w["end"]
            })
        js_segments.append(js_seg)

    js_captions_path = config.SCENES_DIR / "agent_scene_03_captions.js"
    with open(js_captions_path, "w", encoding="utf-8") as f:
        f.write(f"window.agent_scene_03_captions = {json.dumps(js_segments, indent=2, ensure_ascii=False)};")
    logger.info(f"Saved JS captions file to {js_captions_path}")

    # Cleanup wav files
    hook_wav.unlink(missing_ok=True)
    student_wav.unlink(missing_ok=True)
    logger.info("Cleanup of temp WAV files complete.")

if __name__ == "__main__":
    main()
