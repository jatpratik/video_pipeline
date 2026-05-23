"""
AI Video Generation Pipeline — Main Orchestrator
====================================================
Fully automated pipeline:

  voice.mp3 + script.txt
       ↓
  Step 1: WhisperX Forced Alignment (word-level timestamps)
       ↓
  Step 2: LLM Scene Segmentation (OpenAI GPT-4o)
       ↓
  Step 3: Visual Generation (HTML/CSS/GSAP with word emphasis)
       ↓
  Step 4: Headless Rendering (Playwright → FFmpeg normalisation)
       ↓
  Step 5: Video Assembly (FFmpeg concat + narration audio)
       ↓
  Step 6: Export Validation (resolution, fps, duration, audio sync)
       ↓
  final_video.mp4 (1080 × 1920, 30 fps)

Usage:
  python main.py                   # Full pipeline
  python main.py --skip-to 3       # Resume from Step 3
  python main.py --parallel 5      # 5 concurrent renders
  python main.py --help
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
from scripts.step2_segmentation import run_segmentation
from scripts.step3_visual_gen import generate_visuals
from scripts.step4_render import render_all_scenes
from scripts.step5_assembly import assemble_video
from scripts.step6_export import validate_export


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI Video Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--skip-to",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5, 6],
        help="Resume from step N (default: 1 = full pipeline)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=config.RENDER_BATCH_SIZE,
        help=f"Concurrent Playwright renders (default: {config.RENDER_BATCH_SIZE})",
    )
    args = parser.parse_args()

    log = config.logger
    log.info("=" * 62)
    log.info("   AI VIDEO GENERATION PIPELINE")
    log.info("=" * 62)
    log.info(f"  Device         : {config.DEVICE}")
    log.info(f"  WhisperX model : {config.WHISPERX_MODEL}")
    log.info(f"  OpenAI model   : {config.OPENAI_MODEL}")
    log.info(f"  Parallel       : {args.parallel}")
    log.info(f"  Starting step  : {args.skip_to}")
    log.info(f"  Output         : {config.OUTPUT_DIR / 'final_video.mp4'}")
    log.info("=" * 62)

    start_time = time.time()

    # ---- Validate inputs ----------------------------------------------
    audio_path = _find_audio(config.INPUT_DIR)
    script_path = config.INPUT_DIR / "script.txt"

    if audio_path is None:
        log.error(f"No audio file found in {config.INPUT_DIR}")
        log.error("Place your narration audio as: input/voice.wav (or .mp3, .m4a, .ogg, .flac)")
        sys.exit(1)
    log.info(f"  Audio input: {audio_path.name}")
    if not script_path.exists():
        log.error(f"Script not found: {script_path}")
        log.error("Place your narration script at: input/script.txt")
        sys.exit(1)

    alignment_path = config.TIMESTAMPS_DIR / "alignment.json"
    scenes_path = config.SCENES_DIR / "scenes.json"

    # ==================================================================
    # STEP 1 — Forced Alignment
    # ==================================================================
    if args.skip_to <= 1:
        _banner(log, 1, "FORCED ALIGNMENT (WhisperX)")
        alignment = run_alignment(
            audio_path=audio_path,
            script_path=script_path,
            output_path=alignment_path,
            device=config.DEVICE,
            model_name=config.WHISPERX_MODEL,
            compute_type=config.WHISPERX_COMPUTE_TYPE,
            batch_size=config.WHISPERX_BATCH_SIZE,
        )
    else:
        alignment = _load_json(alignment_path, "alignment")

    # ==================================================================
    # STEP 2 — Scene Segmentation
    # ==================================================================
    if args.skip_to <= 2:
        _banner(log, 2, "SCENE SEGMENTATION (OpenAI)")
        scenes = run_segmentation(
            alignment=alignment,
            output_path=scenes_path,
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
        )
    else:
        scenes = _load_json(scenes_path, "scenes")

    # ==================================================================
    # STEP 3 — Visual Generation
    # ==================================================================
    if args.skip_to <= 3:
        _banner(log, 3, "VISUAL GENERATION (HTML/CSS/GSAP)")
        html_files = generate_visuals(
            scenes=scenes,
            templates_dir=config.TEMPLATES_DIR,
            output_dir=config.SCENES_DIR,
        )
    else:
        html_files = [
            config.SCENES_DIR / f"{s['scene_id']}.html"
            for s in scenes
        ]

    # ==================================================================
    # STEP 4 — Headless Rendering
    # ==================================================================
    if args.skip_to <= 4:
        _banner(log, 4, "RENDERING SCENES (Playwright + FFmpeg)")
        video_clips = render_all_scenes(
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
    else:
        video_clips = [
            config.RENDERED_DIR / f"{s['scene_id']}.mp4"
            for s in scenes
        ]

    # ==================================================================
    # STEP 5 — Video Assembly
    # ==================================================================
    if args.skip_to <= 5:
        _banner(log, 5, "VIDEO ASSEMBLY (FFmpeg)")
        final_path = config.OUTPUT_DIR / "final_video.mp4"
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
    else:
        final_path = config.OUTPUT_DIR / "final_video.mp4"

    # ==================================================================
    # STEP 6 — Export Validation
    # ==================================================================
    _banner(log, 6, "EXPORT VALIDATION")
    report = validate_export(
        video_path=final_path,
        audio_path=audio_path,
        video_width=config.VIDEO_WIDTH,
        video_height=config.VIDEO_HEIGHT,
        fps=config.FPS,
    )

    # ---- Summary ------------------------------------------------------
    elapsed = time.time() - start_time
    log.info("")
    log.info("=" * 62)
    if report["passed"]:
        log.info("   ✅  PIPELINE COMPLETE — ALL CHECKS PASSED")
    else:
        log.info("   ⚠️  PIPELINE COMPLETE — SOME CHECKS FAILED")
    log.info(f"   Time   : {elapsed:.1f}s ({elapsed / 60:.1f} min)")
    log.info(f"   Output : {final_path}")
    log.info("=" * 62)


# ======================================================================
# Utilities
# ======================================================================

def _find_audio(input_dir: Path) -> Path | None:
    """Find the narration audio file in the input directory.
    Supports: .wav, .mp3, .m4a, .ogg, .flac
    Prioritises files named 'voice.*'.
    """
    supported = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}

    # First look for voice.* specifically
    for ext in supported:
        candidate = input_dir / f"voice{ext}"
        if candidate.exists():
            return candidate

    # Fall back to any supported audio file
    for f in sorted(input_dir.iterdir()):
        if f.suffix.lower() in supported:
            return f

    return None


def _banner(log, step: int, title: str) -> None:
    log.info("")
    log.info(f"┌{'─' * 58}┐")
    log.info(f"│  STEP {step} — {title:<49}│")
    log.info(f"└{'─' * 58}┘")


def _load_json(path: Path, name: str) -> dict | list:
    """Load a checkpoint JSON file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Cannot --skip-to past step: {name} file not found at {path}"
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    config.logger.info(f"  Loaded {name} checkpoint from {path}")
    return data


if __name__ == "__main__":
    main()
