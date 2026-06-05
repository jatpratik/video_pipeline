"""
Step 6 — Export Validation
============================
Validates the final video against all required specifications:
  • Duration matches narration audio (± tolerance)
  • Resolution is 1080 × 1920
  • Frame rate is 30 fps
  • Audio stream is present
  • File size is reasonable

Output: validation report logged + returned as dict.
"""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("video_pipeline.export")


def validate_export(
    video_path: Path,
    audio_path: Path,
    video_width: int = 1080,
    video_height: int = 1920,
    fps: int = 30,
    duration_tolerance: float = 0.5,
    scenes: list[dict] = None,
) -> dict:
    """
    Run comprehensive validation checks on the final video.

    Args:
        video_path:          Path to final_video.mp4.
        audio_path:          Path to the original narration audio.
        video_width:         Expected width.
        video_height:        Expected height.
        fps:                 Expected frame rate.
        duration_tolerance:  Max allowed duration difference vs audio (seconds).

    Returns:
        dict with validation results and pass/fail status.
    """
    logger.info(f"Validating final video: {video_path}")

    report: dict = {
        "video_path": str(video_path),
        "checks": {},
        "passed": True,
    }

    if not video_path.exists():
        report["passed"] = False
        report["checks"]["file_exists"] = {"pass": False, "detail": "File not found"}
        logger.error("VALIDATION FAILED — final video file does not exist")
        return report

    # ------------------------------------------------------------------
    # Probe the final video
    # ------------------------------------------------------------------
    video_info = _probe(video_path)
    if not video_info:
        report["passed"] = False
        report["checks"]["probe"] = {"pass": False, "detail": "ffprobe failed"}
        return report

    # ------------------------------------------------------------------
    # 1. File size
    # ------------------------------------------------------------------
    file_size = video_path.stat().st_size
    size_mb = file_size / (1024 * 1024)
    report["checks"]["file_size"] = {
        "pass": size_mb > 0.1,
        "detail": f"{size_mb:.1f} MB",
    }
    logger.info(f"  File size: {size_mb:.1f} MB")

    # ------------------------------------------------------------------
    # 2. Duration vs audio
    # ------------------------------------------------------------------
    video_duration = float(video_info.get("format", {}).get("duration", 0))
    audio_duration = _get_audio_duration(audio_path)

    # Calculate overlay durations dynamically
    overlay_shift = 0.0
    if scenes is not None:
        for scene in scenes:
            for ov in scene.get("overlays", []):
                overlay_shift += ov["duration"] + ov.get("padding_start", 0.0) + ov.get("padding_end", 0.0)
    else:
        # Fallback to the old hardcoded logic if scenes is not passed
        student_video_path = audio_path.parent / "student_speaking.mp4"
        if student_video_path.exists():
            overlay_shift = 8.5

    audio_duration += overlay_shift

    duration_diff = abs(video_duration - audio_duration)
    dur_pass = duration_diff <= duration_tolerance

    report["checks"]["duration"] = {
        "pass": dur_pass,
        "detail": (
            f"video={video_duration:.2f}s, "
            f"audio={audio_duration:.2f}s, "
            f"diff={duration_diff:.2f}s "
            f"(tolerance={duration_tolerance}s)"
        ),
    }
    if not dur_pass:
        report["passed"] = False
    logger.info(
        f"  Duration: video={video_duration:.2f}s, audio={audio_duration:.2f}s, "
        f"diff={duration_diff:.2f}s → {'✓' if dur_pass else '✗'}"
    )

    # ------------------------------------------------------------------
    # 3. Resolution
    # ------------------------------------------------------------------
    v_stream = _get_video_stream(video_info)
    actual_w = int(v_stream.get("width", 0))
    actual_h = int(v_stream.get("height", 0))
    res_pass = actual_w == video_width and actual_h == video_height

    report["checks"]["resolution"] = {
        "pass": res_pass,
        "detail": f"{actual_w}×{actual_h} (expected {video_width}×{video_height})",
    }
    if not res_pass:
        report["passed"] = False
    logger.info(
        f"  Resolution: {actual_w}×{actual_h} → {'✓' if res_pass else '✗'}"
    )

    # ------------------------------------------------------------------
    # 4. Frame rate
    # ------------------------------------------------------------------
    r_frame_rate = v_stream.get("r_frame_rate", "0/1")
    try:
        num, den = map(int, r_frame_rate.split("/"))
        actual_fps = round(num / den) if den else 0
    except (ValueError, ZeroDivisionError):
        actual_fps = 0

    fps_pass = actual_fps == fps
    report["checks"]["fps"] = {
        "pass": fps_pass,
        "detail": f"{actual_fps} fps (expected {fps})",
    }
    if not fps_pass:
        report["passed"] = False
    logger.info(f"  FPS: {actual_fps} → {'✓' if fps_pass else '✗'}")

    # ------------------------------------------------------------------
    # 5. Audio stream present
    # ------------------------------------------------------------------
    a_stream = _get_audio_stream(video_info)
    audio_pass = a_stream is not None
    report["checks"]["audio_stream"] = {
        "pass": audio_pass,
        "detail": (
            f"codec={a_stream.get('codec_name', '?')}, "
            f"channels={a_stream.get('channels', '?')}"
            if a_stream else "No audio stream found"
        ),
    }
    if not audio_pass:
        report["passed"] = False
    logger.info(f"  Audio stream: {'✓' if audio_pass else '✗'}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total = len(report["checks"])
    passed = sum(1 for c in report["checks"].values() if c["pass"])

    if report["passed"]:
        logger.info(f"  ══ VALIDATION PASSED ({passed}/{total} checks) ══")
    else:
        logger.error(f"  ══ VALIDATION FAILED ({passed}/{total} checks) ══")
        for name, check in report["checks"].items():
            if not check["pass"]:
                logger.error(f"    ✗ {name}: {check['detail']}")

    return report


# ======================================================================
# Helpers
# ======================================================================

def _probe(path: Path) -> dict | None:
    """Run ffprobe and return parsed JSON."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as exc:
        logger.error(f"ffprobe error: {exc}")
    return None


def _get_audio_duration(path: Path) -> float:
    """Get the duration of an audio file via ffprobe."""
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


def _get_video_stream(info: dict) -> dict:
    """Extract the first video stream from ffprobe output."""
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            return s
    return {}


def _get_audio_stream(info: dict) -> dict | None:
    """Extract the first audio stream from ffprobe output."""
    for s in info.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return None
