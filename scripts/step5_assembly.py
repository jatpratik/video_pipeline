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
import time as _time
from pathlib import Path

logger = logging.getLogger("video_pipeline.assembly")


def resolve_overlay_path(video_name: str, audio_path: Path) -> Path | None:
    """Find the overlay video file in known locations."""
    p = Path(video_name)
    if p.is_absolute() and p.exists():
        return p
    import config
    p1 = config.INPUT_DIR / video_name
    if p1.exists():
        return p1
    p2 = audio_path.parent / video_name
    if p2.exists():
        return p2
    p3 = Path.cwd() / video_name
    if p3.exists():
        return p3
    return None


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
    for clip in scene_clips:
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
    # 4. Resolve overlays and build timelines
    # ------------------------------------------------------------------
    overlays_meta = []
    scene_start_visual = 0.0
    for scene in scenes:
        scene_dur = scene["duration"]
        if "overlays" in scene:
            for ov in scene["overlays"]:
                resolved = resolve_overlay_path(ov["video"], audio_path)
                if resolved is None:
                    raise FileNotFoundError(f"Overlay video not found: {ov['video']}")
                
                overlays_meta.append({
                    "resolved_path": resolved,
                    "insert_time": ov["insert_time"],
                    "global_insert_visual_time": scene_start_visual + ov["insert_time"],
                    "duration": ov["duration"],
                    "padding_start": ov.get("padding_start", 0.0),
                    "position": ov["position"],
                    "crop": ov.get("crop"),
                    "fade_in": ov.get("fade_in", 0.5),
                    "fade_out": ov.get("fade_out", 0.5),
                })
        scene_start_visual += scene_dur

    # Sort overlays by visual start time to ensure logical progression
    overlays_meta.sort(key=lambda x: x["global_insert_visual_time"])

    # Calculate narrator timeline split points and visual shifts
    cumulative_shift = 0.0
    for ov in overlays_meta:
        ov["global_insert_narrator_time"] = ov["global_insert_visual_time"] - cumulative_shift
        ov["shift"] = ov["duration"] + ov["padding_start"]
        cumulative_shift += ov["shift"]

    # ------------------------------------------------------------------
    # 5. Build FFmpeg command and filter graph
    # ------------------------------------------------------------------
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

    # FFmpeg inputs listing
    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(concat_output),
        "-i", str(audio_path),
    ]

    first_overlay_index = 2
    if face_video_path is not None:
        cmd_final.extend(["-i", str(face_video_path)])
        first_overlay_index = 3

    for ov in overlays_meta:
        cmd_final.extend(["-i", str(ov["resolved_path"])])

    # Construct the filter complex list
    filter_parts = []
    
    M = len(overlays_meta)

    # 5a. Build background/face video filter chains
    bg_label = "bg"
    if M == 0 and face_video_path is None:
        bg_label = "v"

    if getattr(config, "FULL_SCREEN_PRESENTER", False) and face_video_path is not None:
        logger.info(
            f"FULL_SCREEN_PRESENTER enabled. Found face video: {face_video_path.name}. "
            f"Scaling/cropping to {video_width}x{video_height} for full-screen background..."
        )
        trim_start = config.FACE_VIDEO_TRIM_START_S
        delay_pts = config.FACE_VIDEO_DELAY_S

        # Build presenter video enhancement and full-screen scaling filters
        face_filters = [
            f"scale={video_width}:{video_height}:force_original_aspect_ratio=increase",
            f"crop={video_width}:{video_height}",
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
        
        face_filters.append("format=yuv420p")
        face_filter_str = ",".join(face_filters)

        # Process the presenter video stream as a full-screen base track
        filter_parts.append(
            f"[2:v]trim=start={trim_start},setpts=PTS-STARTPTS,{face_filter_str},setpts=PTS+{delay_pts}/TB[presenter_bg]"
        )

        # Apply chroma key to key out green background from HTML visuals (0:v)
        filter_parts.append(
            f"[0:v]colorkey=0x00ff00:0.3:0.1,format=rgba[visuals_keyed]"
        )

        # Overlay keyed visuals on presenter background
        next_bg = "bg_face_final" if M > 0 else "v"
        filter_parts.append(
            f"[presenter_bg][visuals_keyed]overlay=x=0:y=0:eof_action=pass[{next_bg}]"
        )
        bg_label = next_bg

    else:
        # Fallback to padded visuals with circle-cropped face video
        filter_parts.append(f"[0:v]pad={video_width}:{video_height}:0:0:black[{bg_label}]")

        if face_video_path is not None:
            logger.info(
                f"Found face video: {face_video_path.name}. "
                f"Trimming {config.FACE_VIDEO_TRIM_START_S}s and overlaying circle crop..."
            )
            trim_start = config.FACE_VIDEO_TRIM_START_S
            delay_pts = config.FACE_VIDEO_DELAY_S

            # Build circle-cropped face video filters
            face_filters = [
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
                "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(pow(X-200,2)+pow(Y-200,2),40000),255,0)'"
            ])
            face_filter_str = ",".join(face_filters)

            # Process the face video stream as a circular overlay
            filter_parts.append(
                f"[2:v]trim=start={trim_start},setpts=PTS-STARTPTS,{face_filter_str},setpts=PTS+{delay_pts}/TB[face_clean]"
            )

            # Build enable condition to hide during student overlays
            enable_conds = [f"gt(t,{delay_pts})"]
            for ov in overlays_meta:
                ov_start = ov["global_insert_visual_time"]
                ov_end = ov_start + ov["duration"] + ov["padding_start"]
                enable_conds.append(f"not(between(t,{ov_start},{ov_end}))")
            enable_cond = "*".join(enable_conds)

            next_bg = "bg_face_final" if M > 0 else "v"
            filter_parts.append(
                f"[{bg_label}][face_clean]overlay=x=80:y=1440:enable='{enable_cond}':eof_action=pass[{next_bg}]"
            )
            bg_label = next_bg

    # 5b. Build student/overlay video filter chains
    for idx, ov in enumerate(overlays_meta):
        ov_idx = first_overlay_index + idx
        padding_start = ov["padding_start"]
        duration = ov["duration"]
        fade_in = ov["fade_in"]
        fade_out = ov["fade_out"]
        global_insert_visual = ov["global_insert_visual_time"]
        w = ov["position"]["w"]
        h = ov["position"]["h"]
        crop_param = ov["crop"]

        crop_filter = f"crop={crop_param}," if crop_param else ""

        filter_parts.append(
            f"[{ov_idx}:v]tpad=start_duration={padding_start}:start_mode=clone,"
            f"{crop_filter}scale={w}:{h},fade=t=in:st=0:d={fade_in},"
            f"fade=t=out:st={duration}:d={fade_out},setpts=PTS-STARTPTS+{global_insert_visual}/TB[ov_{idx}_v]"
        )

    # Chain overlay videos onto background
    if M > 0:
        for idx, ov in enumerate(overlays_meta):
            ov_start = ov["global_insert_visual_time"]
            ov_end = ov_start + ov["duration"] + ov["padding_start"]
            x = ov["position"]["x"]
            y = ov["position"]["y"]
            enable_cond = f"between(t,{ov_start},{ov_end})"

            next_bg = f"bg_ov_{idx}" if idx < M - 1 else "v"

            filter_parts.append(
                f"[{bg_label}][ov_{idx}_v]overlay=x={x}:y={y}:enable='{enable_cond}':eof_action=pass[{next_bg}]"
            )
            bg_label = next_bg

    # 5c. Build split and concat filter chains for audio
    for i in range(M + 1):
        narrator_start_t = 0.0 if i == 0 else overlays_meta[i - 1]["global_insert_narrator_time"]
        narrator_end_t = overlays_meta[i]["global_insert_narrator_time"] if i < M else None

        trim_str = f"start={narrator_start_t}"
        if narrator_end_t is not None:
            trim_str += f":end={narrator_end_t}"

        filter_parts.append(
            f"[1:a]atrim={trim_str},asetpts=PTS-STARTPTS,aformat=sample_rates=44100:channel_layouts=stereo[narr_a_{i}]"
        )

    for idx, ov in enumerate(overlays_meta):
        ov_idx = first_overlay_index + idx
        duration = ov["duration"]
        padding_start = ov["padding_start"]
        delay_ms = int(padding_start * 1000)
        delay_filter = f",adelay={delay_ms}|{delay_ms}" if delay_ms > 0 else ""

        filter_parts.append(
            f"[{ov_idx}:a]atrim=end={duration},asetpts=PTS-STARTPTS{delay_filter},"
            f"aformat=sample_rates=44100:channel_layouts=stereo[ov_{idx}_a]"
        )

    # Concatenate all audio slices in interleaved order
    concat_inputs = []
    for i in range(M):
        concat_inputs.append(f"[narr_a_{i}]")
        concat_inputs.append(f"[ov_{i}_a]")
    concat_inputs.append(f"[narr_a_{M}]")

    concat_inputs_str = "".join(concat_inputs)
    filter_parts.append(f"{concat_inputs_str}concat=n={2*M+1}:v=0:a=1[a]")

    filter_complex_str = ";".join(filter_parts)

    cmd_final.extend([
        "-filter_complex", filter_complex_str,
        "-map", "[v]",
        "-map", "[a]" if M > 0 or face_video_path is not None else "1:a",
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
    ])

    if face_video_path is not None:
        # Include color specifications for video containing face video overlays
        cmd_final.insert(-1, "-color_range")
        cmd_final.insert(-1, "tv")
        cmd_final.insert(-1, "-colorspace")
        cmd_final.insert(-1, "bt709")
        cmd_final.insert(-1, "-color_trc")
        cmd_final.insert(-1, "bt709")
        cmd_final.insert(-1, "-color_primaries")
        cmd_final.insert(-1, "bt709")

    logger.info("Executing final assembly filter graph...")
    _run_ffmpeg(cmd_final, "final assembly")

    # ------------------------------------------------------------------
    # 6. Cleanup working files (with retry for Windows file locks)
    # ------------------------------------------------------------------
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
