"""
Step 4 — Render HTML Animations to MP4
=========================================
Opens each scene HTML in headless Chromium via Playwright,
records the GSAP animation, and exports normalised MP4 clips.

Each clip is post-processed with FFmpeg to guarantee:
  • constant 30 fps
  • exact target duration
  • h264 / yuv420p codec
  • correct resolution (1080 × 960)

Validation is run after rendering; clips that exceed drift
tolerance are automatically re-rendered (up to MAX_RE_RENDER_ATTEMPTS).

Output: rendered_scenes/scene_001.mp4, scene_002.mp4, …
"""

import asyncio
import json
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger("video_pipeline.render")

# Imported lazily inside async functions so the module can still be
# introspected without installing playwright.


# ======================================================================
# Public API
# ======================================================================

def render_all_scenes(
    html_files: list[Path],
    scenes: list[dict],
    output_dir: Path,
    batch_size: int = 3,
    visual_width: int = 1080,
    visual_height: int = 1920,
    fps: int = 30,
    timeout_buffer_ms: int = 2000,
    max_drift: float = 0.15,
    max_retries: int = 3,
) -> list[Path]:
    """
    Render all scene HTML files to MP4 (sync wrapper around async impl).

    Returns:
        Ordered list of MP4 paths.
    """

    return asyncio.run(
        _render_all_async(
            html_files, scenes, output_dir,
            batch_size=batch_size,
            visual_width=visual_width,
            visual_height=visual_height,
            fps=fps,
            timeout_buffer_ms=timeout_buffer_ms,
            max_drift=max_drift,
            max_retries=max_retries,
        )
    )


# ======================================================================
# Async rendering engine
# ======================================================================

async def _render_all_async(
    html_files: list[Path],
    scenes: list[dict],
    output_dir: Path,
    *,
    batch_size: int,
    visual_width: int,
    visual_height: int,
    fps: int,
    timeout_buffer_ms: int,
    max_drift: float,
    max_retries: int,
) -> list[Path]:
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "_raw"
    raw_dir.mkdir(exist_ok=True)

    results: list[Path] = [Path()] * len(html_files)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--allow-file-access-from-files"],
        )

        # Process in batches to limit memory pressure
        for batch_start in range(0, len(html_files), batch_size):
            batch_end = min(batch_start + batch_size, len(html_files))
            tasks = []
            for idx in range(batch_start, batch_end):
                tasks.append(
                    _render_single(
                        browser,
                        html_files[idx],
                        scenes[idx],
                        output_dir,
                        raw_dir,
                        visual_width=visual_width,
                        visual_height=visual_height,
                        fps=fps,
                        timeout_buffer_ms=timeout_buffer_ms,
                        max_drift=max_drift,
                        max_retries=max_retries,
                    )
                )
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                global_idx = batch_start + i
                if isinstance(result, Exception):
                    logger.error(
                        f"Failed to render {scenes[global_idx]['scene_id']}: "
                        f"{result}"
                    )
                    raise result
                results[global_idx] = result

            logger.info(
                f"  Batch {batch_start // batch_size + 1} complete "
                f"({batch_end}/{len(html_files)} scenes)"
            )

        await browser.close()

    # Clean up raw directory
    shutil.rmtree(raw_dir, ignore_errors=True)

    logger.info(f"Rendering complete → {len(results)} clips in {output_dir}")
    return results


async def _render_single(
    browser,
    html_file: Path,
    scene: dict,
    output_dir: Path,
    raw_dir: Path,
    *,
    visual_width: int,
    visual_height: int,
    fps: int,
    timeout_buffer_ms: int,
    max_drift: float,
    max_retries: int,
) -> Path:
    """Render one scene HTML → MP4 with validation & retry."""
    scene_id = scene["scene_id"]
    duration = scene["duration"]
    output_file = output_dir / f"{scene_id}.mp4"

    for attempt in range(1, max_retries + 1):
        logger.info(
            f"  Rendering {scene_id} "
            f"({duration:.2f}s, attempt {attempt}/{max_retries})…"
        )

        # Each attempt gets its own recording directory to avoid
        # filename collisions from concurrent renders.
        attempt_dir = raw_dir / f"{scene_id}_a{attempt}"
        attempt_dir.mkdir(exist_ok=True)

        try:
            context = await browser.new_context(
                viewport={"width": visual_width, "height": visual_height},
                record_video_dir=str(attempt_dir),
                record_video_size={
                    "width": visual_width,
                    "height": visual_height,
                },
            )

            # Prevent initial white screen flash by styling the root element of all loaded pages
            await context.add_init_script(
                "document.documentElement.style.background = '#05050a';"
            )

            page = await context.new_page()

            # Navigate to the HTML file
            file_url = html_file.resolve().as_uri()
            await page.goto(file_url, wait_until="networkidle")

            # Wait for fonts to load before animation starts
            await page.wait_for_function(
                "document.fonts.ready.then(() => true)",
                timeout=10_000,
            )

            # Wait for the full animation + buffer
            wait_ms = int(duration * 1000) + timeout_buffer_ms
            await page.wait_for_timeout(wait_ms)

            # Playwright requires the page/context to be closed before the video
            # file is finalised. If we await save_as() before closing, it deadlocks.
            video = page.video
            await page.close()
            await context.close()

            # Now it is safe to save the video
            raw_video = attempt_dir / f"{scene_id}_raw.webm"
            await video.save_as(str(raw_video))

        except Exception as exc:
            logger.warning(f"  Playwright error for {scene_id}: {exc}")
            if attempt == max_retries:
                raise
            continue

        # Normalise with FFmpeg
        _normalise_clip(
            raw_video, output_file,
            duration=duration,
            width=visual_width,
            height=visual_height,
            fps=fps,
        )

        # Validate
        valid, info = _validate_clip(
            output_file,
            target_duration=duration,
            target_width=visual_width,
            target_height=visual_height,
            max_drift=max_drift,
            fps=fps,
        )

        if valid:
            logger.info(
                f"  ✓ {scene_id} validated "
                f"(actual={info['actual_duration']:.3f}s, "
                f"drift={info['drift']:.3f}s, "
                f"frames={info.get('frames', '?')})"
            )
            return output_file

        logger.warning(
            f"  ✗ {scene_id} validation failed "
            f"(drift={info['drift']:.3f}s) — "
            f"{'retrying' if attempt < max_retries else 'giving up'}"
        )

    # All retries exhausted — return the last attempt anyway
    logger.error(f"  {scene_id}: exceeded max retries, using last render")
    return output_file


# ======================================================================
# FFmpeg post-processing
# ======================================================================

def _normalise_clip(
    src: Path,
    dst: Path,
    duration: float,
    width: int,
    height: int,
    fps: int,
) -> None:
    """
    Normalise a raw Playwright WebM recording into a clean h264 MP4
    with exact duration, framerate, and resolution.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-t", f"{duration:.3f}",
        "-r", str(fps),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=disable",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-an",                       # Strip audio (scene clips are silent)
        "-movflags", "+faststart",
        str(dst),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg normalisation failed for {src.name}:\n{result.stderr}"
        )


# ======================================================================
# Validation
# ======================================================================

def _validate_clip(
    path: Path,
    target_duration: float,
    target_width: int,
    target_height: int,
    max_drift: float,
    fps: int,
) -> tuple[bool, dict]:
    """
    Validate a rendered clip meets spec.

    Returns:
        (is_valid, info_dict)
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return False, {"error": result.stderr, "drift": 999}

    probe = json.loads(result.stdout)

    actual_duration = float(probe.get("format", {}).get("duration", 0))
    drift = abs(actual_duration - target_duration)

    stream = probe.get("streams", [{}])[0]
    actual_w = int(stream.get("width", 0))
    actual_h = int(stream.get("height", 0))
    frames = stream.get("nb_frames", "?")

    expected_frames = int(target_duration * fps)

    info = {
        "actual_duration": actual_duration,
        "drift": drift,
        "width": actual_w,
        "height": actual_h,
        "frames": frames,
        "expected_frames": expected_frames,
    }

    # Check duration drift
    if drift > max_drift:
        return False, info

    # Check resolution
    if actual_w != target_width or actual_h != target_height:
        logger.warning(
            f"Resolution mismatch: {actual_w}×{actual_h} "
            f"(expected {target_width}×{target_height})"
        )
        return False, info

    # Check frame count (soft check)
    if frames != "?" and frames != "N/A":
        frame_diff = abs(int(frames) - expected_frames)
        if frame_diff > 3:
            logger.warning(
                f"Frame count off: {frames} (expected ~{expected_frames})"
            )

    return True, info
