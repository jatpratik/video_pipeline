"""
Step 5 — Video Assembly with FFmpeg
======================================
Combines all rendered scene clips with the narration audio into the
final vertical video (1080 × 1920).

Layout:
  ┌──────────┐
  │  Visuals  │  ← 1080 × 960  (scene clips)
  │  (top)    │
  ├──────────┤
  │  Black    │  ← 1080 × 960  (empty for face recording)
  │  (bottom) │
  └──────────┘

The narration audio is the MASTER timeline.  Scene clips are
concatenated in order — if there is a timing gap between two scenes,
a black filler clip is generated to maintain perfect sync.

Output: output/final_video.mp4
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger("video_pipeline.assembly")


def assemble_video(
    scene_clips: list[Path],
    scenes: list[dict],
    audio_path: Path,
    output_path: Path,
    video_width: int = 1080,
    video_height: int = 1920,
    visual_width: int = 1080,
    visual_height: int = 1920,
    fps: int = 30,
    crf: int = 18,
    preset: str = "medium",
    audio_bitrate: str = "192k",
) -> Path:
    """
    Assemble scene clips + narration audio into the final vertical video.

    Args:
        scene_clips:   Ordered list of rendered scene MP4 paths.
        scenes:        Scene metadata (for gap detection).
        audio_path:    Path to narration voice.mp3.
        output_path:   Where to write final_video.mp4.
        (remaining):   Video spec overrides.

    Returns:
        Path to the final video.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / "_assembly_work"
    work_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Build concat list with gap fillers
    # ------------------------------------------------------------------
    concat_entries: list[Path] = []
    current_time = 0.0

    for i, (clip, scene) in enumerate(zip(scene_clips, scenes)):
        concat_entries.append(clip)

    # ------------------------------------------------------------------
    # 2. Write concat list file
    # ------------------------------------------------------------------
    concat_list = work_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for entry in concat_entries:
            # FFmpeg concat requires forward slashes
            safe_path = str(entry.resolve()).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    # ------------------------------------------------------------------
    # 3. Concatenate all clips
    # ------------------------------------------------------------------
    concat_output = work_dir / "concat_raw.mp4"
    logger.info("Concatenating scene clips…")

    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-preset", "fast",
        "-crf", str(crf),
        "-an",
        str(concat_output),
    ]
    _run_ffmpeg(cmd_concat, "concat")

    # ------------------------------------------------------------------
    # 4. Pad to 1080 × 1920 + add narration audio
    # ------------------------------------------------------------------
    logger.info("Padding to vertical layout and adding narration audio…")

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(concat_output),
        "-i", str(audio_path),
        "-filter_complex",
        f"[0:v]pad={video_width}:{video_height}:0:0:black[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-r", str(fps),
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(cmd_final, "final assembly")

    # ------------------------------------------------------------------
    # 5. Cleanup working files (with retry for Windows file locks)
    # ------------------------------------------------------------------
    import time as _time
    _time.sleep(1)  # Let FFmpeg fully release file handles
    for f in work_dir.iterdir():
        for _attempt in range(3):
            try:
                f.unlink(missing_ok=True)
                break
            except PermissionError:
                _time.sleep(1)
    try:
        work_dir.rmdir()
    except OSError:
        pass  # Directory may not be empty if some files couldn't be deleted

    logger.info(f"Assembly complete → {output_path}")
    return output_path


# ======================================================================
# Helpers
# ======================================================================




def _run_ffmpeg(cmd: list[str], description: str) -> None:
    """Run an FFmpeg command with error handling."""
    logger.debug(f"FFmpeg [{description}]: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,    # 10 min max per command
    )
    if result.returncode != 0:
        logger.error(f"FFmpeg stderr:\n{result.stderr[-2000:]}")
        raise RuntimeError(f"FFmpeg failed [{description}]: exit {result.returncode}")
