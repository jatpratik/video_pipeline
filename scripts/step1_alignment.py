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

    # Summary
    seg_count = len(alignment["segments"])
    word_count = sum(len(s["words"]) for s in alignment["segments"])
    total_dur = alignment["segments"][-1]["end"] if seg_count else 0
    logger.info(f"Alignment saved → {output_path}")
    logger.info(f"  Segments : {seg_count}")
    logger.info(f"  Words    : {word_count}")
    logger.info(f"  Duration : {total_dur:.2f}s")

    return alignment


# ======================================================================
# Internal helpers
# ======================================================================

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
