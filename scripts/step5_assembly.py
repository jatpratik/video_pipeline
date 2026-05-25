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
    # 4. Pad to 1080 × 1920 + add narration audio + overlay face video
    # ------------------------------------------------------------------
    logger.info("Padding layout, overlaying face video, and adding narration audio…")

    import config

    face_video_path = None
    supported_extensions = [".mov", ".MOV", ".mp4", ".MP4", ".webm", ".avi", ".mkv"]
    for name in ["face_video", "face"]:
        for ext in supported_extensions:
            candidate = audio_path.parent / f"{name}{ext}"
            if candidate.exists():
                face_video_path = candidate
                break
        if face_video_path:
            break

    if face_video_path is not None:
        logger.info(
            f"Found face video: {face_video_path.name}. "
            f"Trimming {config.FACE_VIDEO_TRIM_START_S}s and overlaying in high quality "
            f"at {config.FACE_VIDEO_DELAY_S}s delay..."
        )
        delay_pts = config.FACE_VIDEO_DELAY_S
        trim_start = config.FACE_VIDEO_TRIM_START_S

        # Build face video filter chain dynamically
        face_filters = [
            f"trim=start={trim_start},setpts=PTS-STARTPTS",
            "crop=w='min(iw,ih)':h='min(iw,ih)',scale=400:400",
            "zscale=t=linear:npl=400,format=gbrpf32le,zscale=p=bt709",
            "tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv"
        ]

        if getattr(config, "FACE_BEAUTY_VIBRANCE", 0.0) > 0.0:
            face_filters.append(f"vibrance=intensity={config.FACE_BEAUTY_VIBRANCE}")

        if getattr(config, "FACE_BEAUTY_SHARPEN_DETAILS", False):
            amt = config.FACE_BEAUTY_SHARPEN_AMOUNT
            face_filters.append(f"unsharp=3:3:{amt}:3:3:0.0")

        if getattr(config, "FACE_BEAUTY_SMOOTH_SKIN", False):
            rad = config.FACE_BEAUTY_SMOOTH_RADIUS
            strg = config.FACE_BEAUTY_SMOOTH_STRENGTH
            th = config.FACE_BEAUTY_SMOOTH_THRESHOLD
            face_filters.append(f"smartblur={rad}:{strg}:{th}")

        face_filters.extend([
            "format=rgba",
            "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(pow(X-200,2)+pow(Y-200,2),40000),255,0)'",
            f"setpts=PTS+{delay_pts}/TB"
        ])

        face_filter_str = ",".join(face_filters)

        cmd_final = [
            "ffmpeg", "-y",
            "-i", str(concat_output),
            "-i", str(audio_path),
            "-i", str(face_video_path),
            "-filter_complex",
            f"[2:v]{face_filter_str}[face];"
            f"[0:v]pad={video_width}:{video_height}:0:0:black[bg];"
            f"[bg][face]overlay=x=80:y=1440:enable='gt(t,{delay_pts})':eof_action=pass[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_trc", "bt709",
            "-color_primaries", "bt709",
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            "-r", str(fps),
            "-shortest",
            "-movflags", "+faststart",
            str(output_path),
        ]
    else:
        logger.info("No face video found. Proceeding with standard layout assembly...")
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
