#!/usr/bin/env python3
"""
Merge Co-host Videos Utility
============================
Integrates co-host videos (e.g. hook and student questions) into the
speed-adjusted explanation video at specified timestamps.

Always renders co-host videos full screen and applies custom start/stop
frame padding (cloning) to create smooth pauses before/after speaking.
Optionally burns styled captions onto the co-host segments using ASS subtitles.
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

# Add project root to path so we can import config if needed
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    import config
    logger = config.logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("merge_cohost")


def probe_video(path: Path) -> dict:
    """Run ffprobe to extract stream details of a video."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-of", "json", str(path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Failed to probe video {path}: {e}")
        sys.exit(1)


def get_properties(probe_data: dict) -> dict:
    """Extract resolution, frame rate, audio sample rate, channels, and duration."""
    props = {
        "width": 1080,
        "height": 1920,
        "fps": 30.0,
        "sample_rate": 44100,
        "channels": 2,
        "duration": 0.0,
        "has_audio": False
    }

    fmt = probe_data.get("format", {})
    if "duration" in fmt:
        props["duration"] = float(fmt["duration"])

    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video":
            props["width"] = int(stream.get("width", props["width"]))
            props["height"] = int(stream.get("height", props["height"]))

            r_frame_rate = stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(int, r_frame_rate.split("/"))
                if den != 0:
                    props["fps"] = num / den
            except ValueError:
                pass

        elif stream.get("codec_type") == "audio":
            props["sample_rate"] = int(stream.get("sample_rate", props["sample_rate"]))
            props["channels"] = int(stream.get("channels", props["channels"]))
            props["has_audio"] = True

    return props


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS time format: H:MM:SS.CS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_ass_subtitles(captions: list, padding_start: float, output_path: Path):
    """Write temporary ASS subtitles file for the co-host segment."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        # Style details: opaque background box with Outfit font, centered at bottom
        f.write("Style: Default,Outfit,30,&H00FFFFFF,&H000000FF,&H00000000,&H4A0A0C18,-1,0,0,0,100,100,0,0,3,0,0,2,60,60,480,1\n\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for cap in captions:
            # Shift timings by padding_start since subtitles are applied after tpad
            start_t = cap["start"] + padding_start
            end_t = cap["end"] + padding_start
            start_str = format_ass_time(start_t)
            end_str = format_ass_time(end_t)
            text = cap["text"].replace("\n", "\\N")
            f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}\n")


def merge_cohosts(config_path: Path):
    """Execute co-host video merging based on configuration."""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    speed = cfg.get("speed", 1.0)
    exp_path = Path(cfg["explanation_video"]).resolve()
    out_path = Path(cfg["output_video"]).resolve()
    cohosts = cfg.get("cohosts", [])

    if not exp_path.exists():
        logger.error(f"Explanation video not found: {exp_path}")
        sys.exit(1)

    logger.info(f"Probing explanation video: {exp_path.name}")
    exp_probe = probe_video(exp_path)
    exp_props = get_properties(exp_probe)
    target_w = exp_props["width"]
    target_h = exp_props["height"]
    target_fps = exp_props["fps"]
    target_sr = exp_props["sample_rate"]
    target_cl = "stereo" if exp_props["channels"] == 2 else "mono"
    exp_duration = exp_props["duration"]

    logger.info(f"Target Video: {target_w}x{target_h} @ {target_fps:.2f} fps")
    logger.info(f"Target Audio: {target_sr} Hz, {target_cl}")
    logger.info(f"Explanation Duration: {exp_duration:.2f}s")

    # Filter and sort active cohosts
    active_cohosts = []
    for idx, ch in enumerate(cohosts):
        path = Path(ch["video_path"]).resolve()
        if not path.exists():
            logger.error(f"Co-host video not found: {path}")
            sys.exit(1)
        
        logger.info(f"Probing co-host video: {path.name}")
        ch_probe = probe_video(path)
        ch_props = get_properties(ch_probe)
        
        active_cohosts.append({
            "config_index": idx,
            "path": path,
            "insert_time_original": ch["insert_time_original"],
            "padding_start": ch.get("padding_start", 0.0),
            "padding_end": ch.get("padding_end", 0.0),
            "duration": ch_props["duration"],
            "has_audio": ch_props["has_audio"],
            "captions": ch.get("captions", [])
        })

    # Sort cohosts by insert time
    active_cohosts.sort(key=lambda x: x["insert_time_original"])

    # 1. Build segment list for visual/audio splitting and inserting
    segments = []
    current_exp_time = 0.0

    for idx, ch in enumerate(active_cohosts):
        insert_t = ch["insert_time_original"] / speed
        # Ensure insert time does not exceed explanation duration
        insert_t = min(insert_t, exp_duration)

        # Add explanation segment leading up to this co-host
        if insert_t > current_exp_time:
            segments.append({
                "type": "explanation",
                "start": current_exp_time,
                "end": insert_t
            })
            current_exp_time = insert_t

        # Add cohost segment
        segments.append({
            "type": "cohost",
            "cohost": ch
        })

    # Add remaining explanation segment
    if current_exp_time < exp_duration:
        segments.append({
            "type": "explanation",
            "start": current_exp_time,
            "end": exp_duration
        })

    # 2. Build FFmpeg command inputs
    cmd = [
        "ffmpeg", "-y",
        "-i", str(exp_path)
    ]

    # Map each cohost video to an input index
    for ch in active_cohosts:
        cmd.extend(["-i", str(ch["path"])])

    # Check if we need an nullsrc input for silent audio fallback
    silent_input_idx = None
    has_silent_audio_needed = any(not ch["has_audio"] for ch in active_cohosts)
    if has_silent_audio_needed:
        silent_input_idx = 1 + len(active_cohosts)
        cmd.extend([
            "-f", "lavfi",
            "-i", f"anullsrc=r={target_sr}:cl={target_cl}"
        ])

    # 3. Construct filter complex
    filter_parts = []
    temp_ass_files = []

    for idx, seg in enumerate(segments):
        if seg["type"] == "explanation":
            start = seg["start"]
            end = seg["end"]
            filter_parts.append(
                f"[0:v]trim=start={start:.4f}:end={end:.4f},setpts=PTS-STARTPTS[v_{idx}]"
            )
            filter_parts.append(
                f"[0:a]atrim=start={start:.4f}:end={end:.4f},asetpts=PTS-STARTPTS[a_{idx}]"
            )
        elif seg["type"] == "cohost":
            ch = seg["cohost"]
            # Co-host input index is 1 + index in sorted list
            cohost_input_idx = 1 + active_cohosts.index(ch)
            padding_start = ch["padding_start"]
            padding_end = ch["padding_end"]
            duration = ch["duration"]
            total_duration = duration + padding_start + padding_end

            # Subtitles handling
            subtitle_filter = ""
            if ch["captions"]:
                ass_filename = f"temp_cohost_{cohost_input_idx}.ass"
                ass_path = Path.cwd() / ass_filename
                write_ass_subtitles(ch["captions"], padding_start, ass_path)
                temp_ass_files.append(ass_path)
                # Escaping ASS file path for FFmpeg filter on Windows
                escaped_ass = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
                subtitle_filter = f",subtitles='{escaped_ass}'"

            # Video chain: scale and pad to match resolution, apply tpad clone, burn subtitles
            video_filters = (
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,"
                f"tpad=start_duration={padding_start}:start_mode=clone:"
                f"stop_duration={padding_end}:stop_mode=clone"
                f"{subtitle_filter},"
                f"setpts=PTS-STARTPTS"
            )
            filter_parts.append(
                f"[{cohost_input_idx}:v]{video_filters}[v_{idx}]"
            )

            # Audio chain: delay by padding_start, format and pad to exact duration
            delay_ms = int(padding_start * 1000)
            audio_source = f"[{cohost_input_idx}:a]" if ch["has_audio"] else f"[{silent_input_idx}:a]"
            
            audio_filters = f"aformat=sample_rates={target_sr}:channel_layouts={target_cl}"
            if delay_ms > 0:
                audio_filters += f",adelay={delay_ms}|{delay_ms}"
            audio_filters += f",apad,atrim=end={total_duration:.4f},asetpts=PTS-STARTPTS"

            filter_parts.append(
                f"{audio_source}{audio_filters}[a_{idx}]"
            )

    # 4. Concatenate all segments
    concat_inputs = []
    for idx in range(len(segments)):
        concat_inputs.append(f"[v_{idx}][a_{idx}]")
    
    concat_filter = f"{''.join(concat_inputs)}concat=n={len(segments)}:v=1:a=1[outv][outa]"
    filter_parts.append(concat_filter)

    # Compile final command
    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", str(target_fps),
        "-movflags", "+faststart",
        str(out_path)
    ])

    logger.info("Executing FFmpeg co-host merge...")
    logger.debug(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Successfully created co-host merged video at {out_path}")
    finally:
        # Clean up temporary ASS files
        for f in temp_ass_files:
            try:
                f.unlink(missing_ok=True)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Merge co-host videos fullscreen into speed-adjusted video with pauses and captions."
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="cohost_config.json",
        help="Path to co-host merge configuration JSON (default: cohost_config.json)"
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    merge_cohosts(config_path)


if __name__ == "__main__":
    main()
