#!/usr/bin/env python3
"""
Adjust Video Speed Utility
===========================
Adjusts the speed of a completed MP4 video (both video and audio) 
without losing visual quality.

Supports two methods:
1. 'transcode' (Visually Lossless Re-encoding):
   Re-encodes the video with high quality (low CRF like 12) while shifting speed.
   Pros: Extremely reliable, perfect audio/video sync, works on all platforms.
   Cons: Requires a short processing time.

2. 'lossless' (100% Lossless Video Stream Copy):
   Extracts the raw H264 bitstream and remuxes it at a different frame rate.
   Only the audio is transcoded. Video packets are untouched (0.0% visual loss).
   Pros: Instantaneous, absolutely zero video quality loss.
   Cons: Relies on container-level timestamp changes; less common.
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
    # Fallback to standard logging if run standalone
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("adjust_speed")


def get_video_metadata(video_path: Path) -> dict:
    """Probes the video to find FPS and duration."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json",
        str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Failed to probe video: {e}")
        sys.exit(1)


def get_video_rotation(metadata: dict) -> int:
    """Extracts rotation angle from probed metadata."""
    # Check stream tags
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            tags = stream.get("tags", {})
            if "rotate" in tags:
                try:
                    return int(float(tags["rotate"]))
                except ValueError:
                    pass
            # Check side data list
            side_data_list = stream.get("side_data_list", [])
            for sd in side_data_list:
                if sd.get("side_data_type") == "Display Matrix":
                    rotation = sd.get("rotation")
                    if rotation is not None:
                        return int(float(rotation))
    # Check format tags
    tags = metadata.get("format", {}).get("tags", {})
    if "rotate" in tags:
        try:
            return int(float(tags["rotate"]))
        except ValueError:
            pass
    return 0


def get_fps_and_duration(metadata: dict) -> tuple[float, float]:
    """Extracts FPS and duration from probed metadata."""
    fps = 30.0  # default fallback
    duration = 0.0
    
    # Check video streams
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            # fps is usually represented as a fraction, e.g. "30/1" or "30000/1001"
            r_frame_rate = stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(int, r_frame_rate.split("/"))
                if den != 0:
                    fps = num / den
            except ValueError:
                pass
            
            duration = float(stream.get("duration", 0))
            if duration > 0:
                return fps, duration
                
    # Check format duration if stream duration wasn't found
    duration = float(metadata.get("format", {}).get("duration", 0))
    return fps, duration


def get_atempo_filter(speed: float) -> str:
    """
    Generates a chain of atempo filters.
    FFmpeg's atempo filter only supports values between 0.5 and 2.0.
    For speeds outside this range, we chain multiple filters (e.g. 2.0 * 1.5 = 3.0).
    """
    filters = []
    temp = speed
    while temp > 2.0:
        filters.append("atempo=2.0")
        temp /= 2.0
    while temp < 0.5:
        filters.append("atempo=0.5")
        temp /= 0.5
    if temp != 1.0:
        filters.append(f"atempo={temp:.4f}")
    return ",".join(filters)


def adjust_speed_transcode(input_path: Path, output_path: Path, speed: float, crf: int) -> None:
    """Adjusts video speed by re-encoding with high-quality visually lossless settings."""
    logger.info(f"Method: Transcoding (CRF={crf}) to adjust speed to {speed}x...")
    
    metadata = get_video_metadata(input_path)
    rot = get_video_rotation(metadata)
    
    video_pts_factor = 1.0 / speed
    audio_filter = get_atempo_filter(speed)
    
    # Build filter complex
    filter_complex = f"[0:v]setpts={video_pts_factor:.6f}*PTS[v]"
    if audio_filter:
        filter_complex += f";[0:a]{audio_filter}[a]"
        
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
    ]
    
    if audio_filter:
        cmd.extend(["-map", "[a]"])
    else:
        cmd.extend(["-map", "0:a?"])
        
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
    ])
    if rot != 0:
        cmd.extend(["-metadata:s:v:0", f"rotate={rot}"])
    cmd.append(str(output_path))
    
    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def adjust_speed_lossless(input_path: Path, output_path: Path, speed: float) -> None:
    """
    Adjusts video speed without re-encoding video. 
    Muxes video frames at a different FPS, transcodes only the audio, and merges them.
    """
    logger.info(f"Method: Lossless Video Copy to adjust speed to {speed}x...")
    
    metadata = get_video_metadata(input_path)
    rot = get_video_rotation(metadata)
    orig_fps, orig_dur = get_fps_and_duration(metadata)
    target_fps = orig_fps * speed
    
    # Identify video codec
    codec = ""
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            codec = stream.get("codec_name", "").lower()
            break
            
    if not codec:
        raise ValueError("Could not find video stream codec in metadata.")
        
    if codec in ("h264", "hevc", "h265"):
        bsf = "hevc_mp4toannexb" if codec in ("hevc", "h265") else "h264_mp4toannexb"
        ext = "hevc" if codec in ("hevc", "h265") else "h264"
    else:
        raise ValueError(
            f"Lossless method only supports H.264 and HEVC (H.265) codecs. "
            f"Detected codec: {codec}. Please use the 'transcode' method instead."
        )
        
    logger.info(f"Detected codec: {codec.upper()}. Using bitstream filter: {bsf}")
    logger.info(f"Original video: {orig_dur:.2f}s, {orig_fps:.2f} fps")
    logger.info(f"Target video:   {orig_dur / speed:.2f}s, {target_fps:.2f} fps")
    
    work_dir = output_path.parent / "_speed_work"
    work_dir.mkdir(exist_ok=True)
    
    raw_bitstream = work_dir / f"temp_raw.{ext}"
    temp_video = work_dir / "temp_video.mp4"
    temp_audio = work_dir / "temp_audio.aac"
    
    try:
        # 1. Demux video to raw bitstream (0% visual loss, copies raw packets)
        logger.info("Step 1: Extracting raw video bitstream...")
        cmd_extract = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c:v", "copy",
            "-an",
            "-bsf:v", bsf,
            str(raw_bitstream)
        ]
        subprocess.run(cmd_extract, check=True, capture_output=True)
        
        # 2. Remux raw bitstream back at the new target frame rate (0% quality loss)
        logger.info(f"Step 2: Remuxing video at {target_fps:.3f} fps...")
        cmd_remux = [
            "ffmpeg", "-y",
            "-fflags", "+genpts",
            "-r", f"{target_fps:.4f}",
            "-i", str(raw_bitstream),
            "-c:v", "copy",
            str(temp_video)
        ]
        subprocess.run(cmd_remux, check=True, capture_output=True)
        
        # 3. Process audio separately (requires decoding/encoding anyway for tempo shift)
        audio_filter = get_atempo_filter(speed)
        if audio_filter:
            logger.info("Step 3: Processing and speed-shifting audio...")
            cmd_audio = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-filter:a", audio_filter,
                "-vn",
                "-c:a", "aac",
                "-b:a", "192k",
                str(temp_audio)
            ]
            subprocess.run(cmd_audio, check=True, capture_output=True)
            
            # 4. Merge speed-shifted video and speed-shifted audio (stream copy both)
            logger.info("Step 4: Merging video and audio tracks...")
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(temp_audio),
                "-c:v", "copy",
                "-c:a", "copy",
                "-movflags", "+faststart",
            ]
            if rot != 0:
                cmd_merge.extend(["-metadata:s:v:0", f"rotate={rot}"])
            cmd_merge.append(str(output_path))
        else:
            # No audio filter needed (speed=1.0) or audio-less
            logger.info("Step 3: Merging without audio adjustments...")
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", str(temp_video),
                "-i", str(input_path),
                "-map", "0:v",
                "-map", "1:a?",
                "-c:v", "copy",
                "-c:a", "copy",
                "-movflags", "+faststart",
            ]
            if rot != 0:
                cmd_merge.extend(["-metadata:s:v:0", f"rotate={rot}"])
            cmd_merge.append(str(output_path))
            
        subprocess.run(cmd_merge, check=True, capture_output=True)
        logger.info("Speed adjustment complete!")
        
    finally:
        # Cleanup work directory
        for f in [raw_bitstream, temp_video, temp_audio]:
            if f.exists():
                try:
                    f.unlink()
                except OSError:
                    pass
        if work_dir.exists():
            try:
                work_dir.rmdir()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Adjust video speed after assembly without losing quality."
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="output/final_video.mp4",
        help="Path to input video (default: output/final_video.mp4)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output/final_video_speed.mp4",
        help="Path to output video (default: output/final_video_speed.mp4)"
    )
    parser.add_argument(
        "-s", "--speed",
        type=float,
        required=True,
        help="Speed multiplier (e.g. 1.2 for 20% faster, 0.8 for 20% slower)"
    )
    parser.add_argument(
        "-m", "--method",
        choices=["transcode", "lossless"],
        default="transcode",
        help="Method to use. 'lossless' copies video packets (0% loss, very fast), 'transcode' re-encodes (CRF=12, highly compatible) (default: transcode)"
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=12,
        help="CRF value for 'transcode' method. Lower is higher quality. 12 is visually lossless. (default: 12)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    
    if not input_path.exists():
        logger.error(f"Input video file not found: {input_path}")
        sys.exit(1)
        
    if args.speed <= 0:
        logger.error("Speed multiplier must be greater than 0.")
        sys.exit(1)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Input:  {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Speed:  {args.speed}x")
    
    try:
        if args.method == "lossless":
            adjust_speed_lossless(input_path, output_path, args.speed)
        else:
            adjust_speed_transcode(input_path, output_path, args.speed, args.crf)
        logger.info(f"Successfully created speed-adjusted video at {output_path}")
    except Exception as e:
        logger.error(f"Speed adjustment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
