"""
Step 1 — Forced Alignment using WhisperX
==========================================
Generates word-level and sentence-level timestamps from narration audio.
Uses the provided script text for guided alignment.

Output: timestamps/alignment.json
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("video_pipeline.alignment")


def run_alignment(
    audio_path: Path,
    script_path: Path,
    output_path: Path,
    device: str = "cpu",
    model_name: str = "large-v3-turbo",
    compute_type: str = "float32",
    batch_size: int = 4,
    scene_id: str = None,
    scenes_dir: Path = None,
) -> dict:
    """
    Run WhisperX forced alignment on narration audio.

    Args:
        audio_path:   Path to voice.mp3
        script_path:  Path to script.txt (used for reference / validation)
        output_path:  Path to save alignment.json
        device:       "cpu" or "cuda"
        model_name:   WhisperX model identifier
        compute_type: "float32" (CPU) or "float16" (CUDA)
        batch_size:   Transcription batch size
        scene_id:     Scene ID (e.g. agent_scene_05)
        scenes_dir:   Directory where scenes are stored

    Returns:
        Structured alignment dict with segments and word timestamps.
    """
    import whisperx

    # ------------------------------------------------------------------
    # Load audio
    # ------------------------------------------------------------------
    logger.info(f"Loading audio: {audio_path}")
    audio = whisperx.load_audio(str(audio_path))

    # ------------------------------------------------------------------
    # 1. Transcribe
    # ------------------------------------------------------------------
    logger.info(f"Loading WhisperX model '{model_name}' on {device} "
                f"(compute_type={compute_type})")
    model = whisperx.load_model(
        model_name, device,
        compute_type=compute_type,
    )

    logger.info("Transcribing audio...")
    result = model.transcribe(audio, batch_size=batch_size)
    detected_language = result.get("language", "en")
    logger.info(f"Detected language: {detected_language}")
    logger.info(f"Raw segments: {len(result.get('segments', []))}")

    # Free model memory
    del model
    _free_gpu(device)

    # ------------------------------------------------------------------
    # 2. Forced alignment (word-level)
    # ------------------------------------------------------------------
    logger.info("Loading alignment model...")
    model_a, metadata = whisperx.load_align_model(
        language_code=detected_language,
        device=device,
    )

    logger.info("Running forced alignment for word-level timestamps...")
    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    # Free alignment model memory
    del model_a
    _free_gpu(device)

    # ------------------------------------------------------------------
    # 3. Structure & save
    # ------------------------------------------------------------------
    alignment = _structure_alignment(result)

    # Read the original script for reference logging
    if script_path.exists():
        script_text = script_path.read_text(encoding="utf-8").strip()
        alignment["original_script"] = script_text
        logger.info(f"Script length: {len(script_text)} chars")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(alignment, f, indent=2, ensure_ascii=False)

    # Get exact audio duration via ffprobe
    audio_duration = _get_audio_duration(audio_path)
    if audio_duration == 0.0 and alignment["segments"]:
        audio_duration = alignment["segments"][-1]["end"]

    # Summary
    seg_count = len(alignment["segments"])
    word_count = sum(len(s["words"]) for s in alignment["segments"])
    logger.info(f"Alignment saved → {output_path}")
    logger.info(f"  Segments : {seg_count}")
    logger.info(f"  Words    : {word_count}")
    logger.info(f"  Duration : {audio_duration:.2f}s")

    # If scene_id and scenes_dir are provided, update metadata and generate JS captions
    if scene_id and scenes_dir:
        _update_scenes_metadata(scenes_dir, scene_id, audio_duration)
        _write_js_captions(scenes_dir, scene_id, alignment)

    return alignment


# ======================================================================
# Internal helpers
# ======================================================================

def _get_audio_duration(path: Path) -> float:
    """Get exact duration of audio using ffprobe."""
    import subprocess
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            return float(info.get("format", {}).get("duration", 0))
    except Exception:
        pass
    return 0.0


def _update_scenes_metadata(scenes_dir: Path, scene_id: str, duration: float) -> None:
    """Update scenes.json metadata file automatically."""
    scenes_json_path = scenes_dir / "scenes.json"
    scenes = []
    if scenes_json_path.exists():
        try:
            with open(scenes_json_path, "r", encoding="utf-8") as f:
                scenes = json.load(f)
        except Exception:
            pass

    found = False
    for s in scenes:
        if s.get("scene_id") == scene_id:
            s["duration"] = round(duration, 3)
            found = True
            break
    if not found:
        scenes.append({
            "scene_id": scene_id,
            "duration": round(duration, 3),
            "overlays": []
        })

    with open(scenes_json_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)
    logger.info(f"Updated scenes.json metadata for scene '{scene_id}'")


def chunk_alignment_segments(segments: list, max_words: int = 8, max_gap: float = 0.4) -> list:
    """
    Split long segments into smaller sub-segments (chunks) based on:
    - Maximum word count per chunk (max_words).
    - Large silence gaps between words (max_gap).
    - Punctuation marks at the end of words.
    """
    chunked_segments = []
    punctuation_marks = {".", ",", "?", "!", ";", ":"}

    for seg in segments:
        words = seg.get("words", [])
        if not words:
            continue

        current_chunk = []
        for w in words:
            should_split = False
            if current_chunk:
                # 1. Check max words constraint
                if len(current_chunk) >= max_words:
                    should_split = True

                # 2. Check time gap constraint
                prev_word = current_chunk[-1]
                gap = w["start"] - prev_word["end"]
                if gap >= max_gap:
                    should_split = True

                # 3. Check punctuation constraint on the previous word
                prev_text = prev_word.get("word", "").strip()
                if prev_text and prev_text[-1] in punctuation_marks:
                    should_split = True

            if should_split and current_chunk:
                chunk_text = " ".join([cw["word"] for cw in current_chunk])
                chunked_segments.append({
                    "text": chunk_text,
                    "start": current_chunk[0]["start"],
                    "end": current_chunk[-1]["end"],
                    "words": list(current_chunk)
                })
                current_chunk = []

            current_chunk.append(w)

        if current_chunk:
            chunk_text = " ".join([cw["word"] for cw in current_chunk])
            chunked_segments.append({
                "text": chunk_text,
                "start": current_chunk[0]["start"],
                "end": current_chunk[-1]["end"],
                "words": list(current_chunk)
            })

    return chunked_segments


def _write_js_captions(scenes_dir: Path, scene_id: str, alignment: dict) -> Path:
    """Write browser-ready captions JS array after chunking long segments."""
    js_output_path = scenes_dir / f"{scene_id}_captions.js"
    
    # Chunk long segments to prevent boundary overflow
    original_segments = alignment.get("segments", [])
    chunked_segments = chunk_alignment_segments(original_segments)
    
    js_segments = []
    for seg in chunked_segments:
        js_words = []
        for w in seg["words"]:
            js_words.append({
                "text": w["word"],
                "start": w["start"],
                "end": w["end"]
            })
        js_segments.append({
            "text": seg["text"],
            "start": seg["start"],
            "end": seg["end"],
            "words": js_words
        })

    js_content = f"window.{scene_id}_captions = {json.dumps(js_segments, indent=2, ensure_ascii=False)};\n"
    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    logger.info(f"Saved chunked captions array to {js_output_path}")
    return js_output_path


def _structure_alignment(result: dict) -> dict:
    """
    Clean WhisperX output into a structured format.
    Drops words without timestamps (alignment failures).
    """
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


def _free_gpu(device: str) -> None:
    """Release GPU memory if using CUDA."""
    if device == "cuda":
        try:
            import torch
            torch.cuda.empty_cache()
            logger.debug("GPU memory released")
        except Exception:
            pass
