"""
Multi-Agent Orchestrator (Educational Visual Intelligence — Phase 3)
=====================================================================
Coordinates the 7-phase pipeline:

  Phase 1: Script Understanding (1 LLM call)
  Phase 2: Visual Reasoning (1 LLM call)
  Phase 2.5: Asset Retrieval (web search + Playwright screenshot)
  Phase 3: Human Review (CLI + file-based hybrid)
  Phase 4: Scene Structuring (1 LLM call)
  Phase 5: Visual Implementation (per-scene: Frontend + Critic)
  Phase 6: Rendering & Export (handled by main.py)
"""

import json
import logging
import time
from pathlib import Path

from .agent_script_understanding import run_script_understanding
from .agent_visual_reasoner import run_visual_reasoning
from .asset_retriever import retrieve_assets
from .agent_scene_structurer import run_scene_structuring
from .agent_frontend import generate_scene_html
from .agent_critic import review_scene, format_feedback_for_retry

logger = logging.getLogger("video_pipeline.agents.orchestrator")


def run_multi_agent_pipeline(
    alignment: dict,
    script_text: str,
    output_dir: Path,
    timestamps_dir: Path,
    api_key: str,
    model: str = "gpt-4o",
    max_critic_retries: int = 1,
    agent_temperature: float = 0.3,
    frontend_temperature: float = 0.2,
    auto_approve: bool = False,
    skip_search: bool = False,
    assets_dir: Path | None = None,
    search_provider: str = "duckduckgo",
    search_api_key: str = "",
    google_cse_id: str = "",
) -> tuple[list[dict], list[Path]]:
    """
    Run the full educational visual reasoning pipeline.

    Args:
        alignment:            WhisperX alignment data.
        script_text:          Original narration script text.
        output_dir:           Directory for scene HTML + scenes.json.
        timestamps_dir:       Directory for intermediate agent outputs.
        api_key:              OpenAI API key.
        model:                OpenAI model identifier.
        max_critic_retries:   Max re-generation attempts per scene.
        agent_temperature:    Temperature for reasoning agents.
        frontend_temperature: Temperature for code generation.
        auto_approve:         Skip human review if True.
        skip_search:          Skip asset retrieval if True.
        assets_dir:           Directory for downloaded assets.
        search_provider:      Search API provider.
        search_api_key:       Search API key.
        google_cse_id:        Google CSE ID.

    Returns:
        (scenes, html_file_paths) tuple.
    """
    t0 = time.time()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║   EDUCATIONAL MULTI-AGENT PIPELINE (Phase 3)           ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamps_dir.mkdir(parents=True, exist_ok=True)
    if assets_dir:
        assets_dir.mkdir(parents=True, exist_ok=True)

    # ==================================================================
    # PHASE 1 — Script Understanding
    # ==================================================================
    logger.info("")
    logger.info("── Phase 1: Script Understanding ──────────────────")

    understanding = run_script_understanding(
        alignment=alignment,
        script_text=script_text,
        api_key=api_key,
        model=model,
        temperature=agent_temperature,
    )

    _save_checkpoint(
        understanding,
        timestamps_dir / "script_understanding.json",
        "script understanding",
    )

    # ==================================================================
    # PHASE 2 — Visual Reasoning
    # ==================================================================
    logger.info("")
    logger.info("── Phase 2: Visual Reasoning ───────────────────────")

    visual_map = run_visual_reasoning(
        script_understanding=understanding,
        alignment=alignment,
        script_text=script_text,
        api_key=api_key,
        model=model,
        temperature=agent_temperature,
    )

    _save_checkpoint(
        visual_map,
        timestamps_dir / "visual_map_raw.json",
        "visual map (pre-assets)",
    )

    # ==================================================================
    # PHASE 2.5 — Asset Retrieval
    # ==================================================================
    if not skip_search and assets_dir:
        logger.info("")
        logger.info("── Phase 2.5: Asset Retrieval ──────────────────────")

        visual_map = retrieve_assets(
            visual_map=visual_map,
            assets_dir=assets_dir,
            search_provider=search_provider,
            search_api_key=search_api_key,
            google_cse_id=google_cse_id,
        )
    else:
        if skip_search:
            logger.info("")
            logger.info("── Phase 2.5: Asset Retrieval (SKIPPED — --skip-search) ──")
        # Mark all segments with fallback
        for seg in visual_map:
            seg.setdefault("assets", [])
            seg.setdefault("asset_fallback", "css_svg")

    # Save enriched visual map
    visual_map_path = timestamps_dir / "visual_map.json"
    _save_checkpoint(visual_map, visual_map_path, "visual map (with assets)")

    # ==================================================================
    # PHASE 3 — Human Review
    # ==================================================================
    logger.info("")
    logger.info("── Phase 3: Human Review ──────────────────────────")

    visual_map = _human_review(visual_map, visual_map_path, auto_approve)

    # ==================================================================
    # PHASE 4 — Scene Structuring
    # ==================================================================
    logger.info("")
    logger.info("── Phase 4: Scene Structuring ─────────────────────")

    scenes = run_scene_structuring(
        visual_map=visual_map,
        alignment=alignment,
        script_understanding=understanding,
        api_key=api_key,
        model=model,
        temperature=0.25,
    )

    _save_checkpoint(
        scenes,
        output_dir / "scenes.json",
        "scenes",
    )

    # ==================================================================
    # PHASE 5 — Visual Implementation (Frontend + Critic per scene)
    # ==================================================================
    logger.info("")
    logger.info("── Phase 5: Visual Implementation ─────────────────")

    html_files: list[Path] = []

    for scene in scenes:
        scene_id = scene["scene_id"]
        logger.info(
            f"\n  ▸ Implementing {scene_id} "
            f"({scene['duration']:.1f}s, strategy={scene.get('visual_strategy', '?')})"
        )

        # Extract layout and choreography from scene
        layout = scene.get("layout", {})
        choreography = scene.get("choreography", {})

        # --- Frontend Renderer ---
        html_code = None
        best_html = None
        best_review = None
        critic_feedback = None

        for attempt in range(1, max_critic_retries + 2):
            is_retry = attempt > 1

            html_code = generate_scene_html(
                scene=scene,
                layout=layout,
                choreography=choreography,
                api_key=api_key,
                model=model,
                temperature=frontend_temperature,
                critic_feedback=critic_feedback if is_retry else None,
            )

            if best_html is None:
                best_html = html_code

            # --- Critic Review ---
            review = review_scene(
                scene=scene,
                html_code=html_code,
                layout=layout,
                choreography=choreography,
                api_key=api_key,
                model=model,
                temperature=agent_temperature,
            )

            overall_score = review.get("scores", {}).get("overall", 0)

            if best_review is None or overall_score > best_review.get("scores", {}).get("overall", 0):
                best_html = html_code
                best_review = review

            if review.get("approved", True):
                logger.info(
                    f"    ✓ {scene_id} approved on attempt {attempt} "
                    f"(score: {overall_score:.2f})"
                )
                break

            if attempt <= max_critic_retries:
                critic_feedback = format_feedback_for_retry(review)
                logger.info(
                    f"    ↻ Regenerating {scene_id} with critic feedback "
                    f"(attempt {attempt}/{max_critic_retries + 1})"
                )
            else:
                logger.warning(
                    f"    ⚠ {scene_id}: max retries reached, "
                    f"using best version (score: "
                    f"{best_review.get('scores', {}).get('overall', 0):.2f})"
                )
                html_code = best_html

        # Save HTML file
        html_path = output_dir / f"{scene_id}.html"
        html_path.write_text(html_code, encoding="utf-8")
        html_files.append(html_path)
        logger.info(f"    Saved → {html_path.name}")

    # Save final scenes (clean copy)
    scenes_clean = []
    for s in scenes:
        s_copy = {k: v for k, v in s.items() if not k.startswith("_")}
        scenes_clean.append(s_copy)

    _save_checkpoint(scenes_clean, output_dir / "scenes.json", "final scenes")

    # Summary
    elapsed = time.time() - t0
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info(f"║  PIPELINE COMPLETE ({elapsed:.1f}s)                            ║")
    logger.info(f"║  Scenes: {len(scenes):<4} HTML files: {len(html_files):<4}                     ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    return scenes, html_files


# ======================================================================
# Human Review (hybrid: file + CLI)
# ======================================================================

def _human_review(
    visual_map: list[dict],
    visual_map_path: Path,
    auto_approve: bool,
) -> list[dict]:
    """
    Present the visual map for human review.
    Hybrid: saves to file AND prompts in CLI.
    """
    if auto_approve:
        logger.info("  Auto-approve enabled — skipping human review")
        return visual_map

    # Print summary to console
    logger.info("")
    logger.info("  ┌─────────────────────────────────────────────────┐")
    logger.info("  │           VISUAL MAP — REVIEW REQUIRED          │")
    logger.info("  └─────────────────────────────────────────────────┘")
    logger.info("")

    for seg in visual_map:
        sid = seg.get("segment_id", "?")
        start = seg.get("start_time", 0)
        end = seg.get("end_time", 0)
        strategy = seg.get("visual_strategy", "?")
        goal = seg.get("teaching_goal", "")[:70]
        assets = seg.get("assets", [])
        fallback = seg.get("asset_fallback", "css_svg")

        asset_status = f"🖼 {len(assets)} image(s)" if assets else "🎨 CSS/SVG"

        logger.info(f"  {sid} [{start:.1f}s–{end:.1f}s] {strategy}")
        logger.info(f"    Goal: {goal}")
        logger.info(f"    Assets: {asset_status}")
        logger.info(f"    Text: \"{seg.get('text_span', '')[:80]}…\"")
        logger.info("")

    logger.info(f"  📄 Full map saved to: {visual_map_path}")
    logger.info(f"     Edit this file to change strategies, images, or descriptions.")
    logger.info("")

    while True:
        try:
            response = input(
                "  [REVIEW] Edit the file if needed, then type 'approve' or 'reject': "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            logger.info("  Review interrupted — using current visual map")
            return visual_map

        if response == "approve":
            # Re-read the file in case user edited it
            try:
                with open(visual_map_path, "r", encoding="utf-8") as f:
                    edited_map = json.load(f)
                if isinstance(edited_map, list):
                    logger.info("  ✓ Visual map approved (re-loaded from file)")
                    return edited_map
                else:
                    logger.info("  ✓ Visual map approved")
                    return visual_map
            except Exception:
                logger.info("  ✓ Visual map approved (using in-memory version)")
                return visual_map

        elif response == "reject":
            logger.info("  ✗ Visual map rejected — re-running Phase 2")
            # Return None to signal re-run (handled by caller)
            # For now, just return the current map with a warning
            logger.warning("  ⚠ Re-run not yet implemented — using current map")
            return visual_map

        else:
            logger.info(f"  Unknown response: '{response}'. Type 'approve' or 'reject'.")


# ======================================================================
# Checkpoint
# ======================================================================

def _save_checkpoint(data, path: Path, name: str) -> None:
    """Save intermediate results as JSON checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"  Checkpoint saved: {name} → {path.name}")
