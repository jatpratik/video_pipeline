"""
AI Video Generation Pipeline — Main Orchestrator (Manual Workflow)
=============================================================
A hybrid pipeline for generating educational videos:
  Step 1: Align audio & script (main.py align)
  Step 2: Generate Visuals (Manual / AI Assistant to scenes/)
  Step 3: Render HTML to MP4 (main.py render)
  Step 4: Assemble final video (main.py assemble)
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path so config and scripts are importable
sys.path.insert(0, str(Path(__file__).parent))

import config
from scripts.step1_alignment import run_alignment
from scripts.step4_render import render_all_scenes
from scripts.step5_assembly import assemble_video
from scripts.step6_export import validate_export

def _find_audio(input_dir: Path) -> Path | None:
    supported = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}
    for ext in supported:
        candidate = input_dir / f"voice{ext}"
        if candidate.exists():
            return candidate
    for f in sorted(input_dir.iterdir()):
        if f.suffix.lower() in supported:
            return f
    return None

def main():
    parser = argparse.ArgumentParser(
        description="AI Video Generation Pipeline (Manual/Hybrid Workflow)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ALIGN
    parser_align = subparsers.add_parser("align", help="Run WhisperX forced alignment")
    
    # RENDER
    parser_render = subparsers.add_parser("render", help="Render HTML scenes to MP4")
    parser_render.add_argument("--parallel", type=int, default=config.RENDER_BATCH_SIZE)

    # ASSEMBLE
    parser_assemble = subparsers.add_parser("assemble", help="Assemble clips into final video")

    args = parser.parse_args()

    log = config.logger
    log.info("=" * 62)
    log.info("   AI VIDEO GENERATION PIPELINE")
    log.info(f"   Command: {args.command}")
    log.info("=" * 62)

    audio_path = _find_audio(config.INPUT_DIR)
    if audio_path is None:
        log.error(f"No audio file found in {config.INPUT_DIR}")
        sys.exit(1)

    if args.command == "align":
        script_path = config.INPUT_DIR / "script.txt"
        if not script_path.exists():
            log.error(f"Script not found: {script_path}")
            sys.exit(1)
        alignment_path = config.TIMESTAMPS_DIR / "alignment.json"
        log.info("Running Step 1: Forced Alignment...")
        run_alignment(
            audio_path=audio_path,
            script_path=script_path,
            output_path=alignment_path,
            device=config.DEVICE,
            model_name=config.WHISPERX_MODEL,
            compute_type=config.WHISPERX_COMPUTE_TYPE,
            batch_size=config.WHISPERX_BATCH_SIZE,
        )
        log.info(f"Alignment complete. Output: {alignment_path}")

    elif args.command == "render":
        scenes_path = config.SCENES_DIR / "scenes.json"
        if not scenes_path.exists():
            log.error(f"Scenes metadata not found: {scenes_path}")
            sys.exit(1)
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
        
        html_files = [config.SCENES_DIR / f"{s['scene_id']}.html" for s in scenes]
        log.info(f"Running Step 3: Rendering {len(scenes)} scenes...")
        
        render_all_scenes(
            html_files=html_files,
            scenes=scenes,
            output_dir=config.RENDERED_DIR,
            batch_size=args.parallel,
            visual_width=config.VISUAL_WIDTH,
            visual_height=config.VISUAL_HEIGHT,
            fps=config.FPS,
            timeout_buffer_ms=config.RENDER_TIMEOUT_BUFFER_MS,
            max_drift=config.MAX_DRIFT_TOLERANCE_S,
            max_retries=config.MAX_RE_RENDER_ATTEMPTS,
        )
        log.info("Rendering complete.")

    elif args.command == "assemble":
        scenes_path = config.SCENES_DIR / "scenes.json"
        if not scenes_path.exists():
            log.error(f"Scenes metadata not found: {scenes_path}")
            sys.exit(1)
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes = json.load(f)
        
        video_clips = [config.RENDERED_DIR / f"{s['scene_id']}.mp4" for s in scenes]
        final_path = config.OUTPUT_DIR / "final_video.mp4"
        
        log.info("Running Step 4: Video Assembly...")
        assemble_video(
            scene_clips=video_clips,
            scenes=scenes,
            audio_path=audio_path,
            output_path=final_path,
            video_width=config.VIDEO_WIDTH,
            video_height=config.VIDEO_HEIGHT,
            visual_width=config.VISUAL_WIDTH,
            visual_height=config.VISUAL_HEIGHT,
            fps=config.FPS,
            crf=config.FFMPEG_CRF,
            preset=config.FFMPEG_PRESET,
            audio_bitrate=config.FFMPEG_AUDIO_BITRATE,
        )
        
        log.info("Running Step 5: Export Validation...")
        report = validate_export(
            video_path=final_path,
            audio_path=audio_path,
            video_width=config.VIDEO_WIDTH,
            video_height=config.VIDEO_HEIGHT,
            fps=config.FPS,
            scenes=scenes,
        )
        
        if report["passed"]:
            log.info("   ✅  PIPELINE COMPLETE — ALL CHECKS PASSED")
        else:
            log.info("   ⚠️  PIPELINE COMPLETE — SOME CHECKS FAILED")
        log.info(f"   Output : {final_path}")

if __name__ == "__main__":
    main()
