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
    parser_align.add_argument("--scene", type=str, default=None, help="Scene ID (e.g. agent_scene_05), auto-detected if omitted")
    
    # RENDER
    parser_render = subparsers.add_parser("render", help="Render HTML scenes to MP4")
    parser_render.add_argument("--parallel", type=int, default=config.RENDER_BATCH_SIZE)

    # ASSEMBLE
    parser_assemble = subparsers.add_parser("assemble", help="Assemble clips into final video")

    # SPEED
    parser_speed = subparsers.add_parser("speed", help="Adjust speed of assembled video")
    parser_speed.add_argument("-s", "--speed", type=float, required=True, help="Speed multiplier (e.g. 1.25)")
    parser_speed.add_argument("-i", "--input", type=str, default="output/final_video.mp4", help="Input video path")
    parser_speed.add_argument("-o", "--output", type=str, default="output/final_video_speed.mp4", help="Output video path")
    parser_speed.add_argument("-m", "--method", choices=["transcode", "lossless"], default="transcode", help="Method (transcode or lossless)")
    parser_speed.add_argument("--crf", type=int, default=12, help="CRF value for transcode")

    # MERGE
    parser_merge = subparsers.add_parser("merge", help="Merge co-host videos (hook, student speaking) into speed-adjusted video")
    parser_merge.add_argument("-c", "--config", type=str, default="cohost_config.json", help="Path to cohost_config.json")

    # SCAFFOLD
    parser_scaffold = subparsers.add_parser("scaffold", help="Scaffold a new visual scene HTML template based on agent_scene_03.html layout")
    parser_scaffold.add_argument("-s", "--scene", type=str, default=None, help="Scene ID (e.g. agent_scene_05), auto-detected if omitted")

    args = parser.parse_args()

    log = config.logger
    log.info("=" * 62)
    log.info("   AI VIDEO GENERATION PIPELINE")
    log.info(f"   Command: {args.command}")
    log.info("=" * 62)

    if args.command == "align":
        audio_path = _find_audio(config.INPUT_DIR)
        if audio_path is None:
            log.error(f"No audio file found in {config.INPUT_DIR}")
            sys.exit(1)
        script_path = config.INPUT_DIR / "script.txt"
        if not script_path.exists():
            log.error(f"Script not found: {script_path}")
            sys.exit(1)
        alignment_path = config.TIMESTAMPS_DIR / "alignment.json"

        scene_id = args.scene
        if scene_id is None:
            import re
            max_num = 0
            pattern = re.compile(r"agent_scene_(\d+)\.html")
            if config.SCENES_DIR.exists():
                for f in config.SCENES_DIR.iterdir():
                    match = pattern.match(f.name)
                    if match:
                        num = int(match.group(1))
                        if num > max_num:
                            max_num = num
            next_num = max_num + 1 if max_num > 0 else 1
            scene_id = f"agent_scene_{next_num:02d}"
            log.info(f"Auto-detected next Scene ID: {scene_id}")

        log.info("Running Step 1: Forced Alignment...")
        run_alignment(
            audio_path=audio_path,
            script_path=script_path,
            output_path=alignment_path,
            device=config.DEVICE,
            model_name=config.WHISPERX_MODEL,
            compute_type=config.WHISPERX_COMPUTE_TYPE,
            batch_size=config.WHISPERX_BATCH_SIZE,
            scene_id=scene_id,
            scenes_dir=config.SCENES_DIR,
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
        audio_path = _find_audio(config.INPUT_DIR)
        if audio_path is None:
            log.error(f"No audio file found in {config.INPUT_DIR}")
            sys.exit(1)
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

    elif args.command == "speed":
        from scripts.adjust_speed import adjust_speed_transcode, adjust_speed_lossless
        input_path = Path(args.input).resolve()
        output_path = Path(args.output).resolve()
        log.info(f"Adjusting speed of {input_path.name} to {args.speed}x...")
        if args.method == "lossless":
            adjust_speed_lossless(input_path, output_path, args.speed)
        else:
            adjust_speed_transcode(input_path, output_path, args.speed, args.crf)
        log.info(f"Speed adjustment complete. Output: {output_path}")

    elif args.command == "merge":
        from scripts.merge_cohost import merge_cohosts
        config_path = Path(args.config).resolve()
        log.info(f"Merging co-host videos based on configuration: {config_path}")
        merge_cohosts(config_path)
        log.info("Co-host merging complete.")

    elif args.command == "scaffold":
        from scripts.scaffold import scaffold_scene
        scene_id = args.scene
        if scene_id is None:
            import re
            max_num = 0
            pattern = re.compile(r"agent_scene_(\d+)\.html")
            if config.SCENES_DIR.exists():
                for f in config.SCENES_DIR.iterdir():
                    match = pattern.match(f.name)
                    if match:
                        num = int(match.group(1))
                        if num > max_num:
                            max_num = num
            next_num = max_num + 1 if max_num > 0 else 1
            scene_id = f"agent_scene_{next_num:02d}"
            log.info(f"Auto-detected next Scene ID for scaffolding: {scene_id}")

        scaffold_scene(scene_id, config.SCENES_DIR)
        log.info("Scaffolding complete.")

if __name__ == "__main__":
    main()
