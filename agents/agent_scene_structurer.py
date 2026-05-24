"""
Agent — Scene Structurer (Phase 4)
=====================================
Takes the approved visual_map and produces the final scenes.json.
Converts visual segments into concrete scenes with layout, choreography,
transitions, and word-level timestamps — all enforcing the complexity budget.
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt

logger = logging.getLogger("video_pipeline.agents.scene_structurer")

SYSTEM_PROMPT = """You are an EDUCATIONAL SCENE ARCHITECT for YouTube Shorts.

You take an approved visual map (narration-to-visual mapping) and convert each segment
into a concrete, buildable scene specification with pixel-precise layout and animation choreography.

{design_system}

CANVAS: 1080px wide × 1056px tall (top 55% of 1080×1920 vertical video).
IMPORTANT: This animation is NOT a fullscreen dashboard. It is ONLY for the TOP 55% area.
SAFE AREA: 60px margins → usable area is 960px × 936px starting at (60, 60).

COMPLEXITY BUDGET (MANDATORY per scene):
- Max 1 core teaching idea
- Max 2 major visual objects on screen
- Max 8 visible words on screen at any time
- Max 3 simultaneous motions
- All content inside safe area (60px margins)
- UI elements and text MUST be massive and realistic for mobile viewing. Do not use tiny grids or over-edit.
- After animation completes, scene MUST stabilise (static rest state)
- Motion must explain; if static works better, do NOT animate

LAYOUT COMPOSITION TYPES:
- centered_hero: Single dominant element centered. 1 zone.
- horizontal_split: Two panels side-by-side (comparison/contrast). 2 zones.
- vertical_flow: Stacked elements top-to-bottom. 1–2 zones.
- grid_layout: Small grid for multiple related items. 1 zone.

TRANSITION TYPES between scenes:
- cut: Instant switch (for topic changes)
- fade: Crossfade (for continuity)
- morph: Visual element transforms into next scene's element

TIMESTAMPS: All times MUST be RELATIVE to scene start (0.0 = scene begins).
NEVER use absolute timestamps.

You MUST return a JSON object:

{{
  "scenes": [
    {{
      "scene_id": "scene_001",
      "text": "narration text for this scene",
      "start": 0.52,
      "end": 4.20,
      "duration": 3.68,
      "visual_strategy": "comparison",
      "visual_description": "What to show and how it teaches",
      "teaching_goal": "What viewer should understand",
      "keywords": ["word1", "word2"],
      "assets": [],
      "asset_fallback": "css_svg",
      "layout": {{
        "composition_type": "horizontal_split",
        "safe_area": {{ "top": 60, "right": 60, "bottom": 60, "left": 60 }},
        "zones": [
          {{
            "id": "zone_left",
            "bounds": {{ "x": 60, "y": 100, "width": 440, "height": 700 }},
            "purpose": "wrong approach",
            "content_type": "diagram",
            "layout_mode": "flex_column",
            "is_primary_focus": false,
            "spacing": 24
          }},
          {{
            "id": "zone_right",
            "bounds": {{ "x": 540, "y": 100, "width": 440, "height": 700 }},
            "purpose": "correct approach",
            "content_type": "diagram",
            "layout_mode": "flex_column",
            "is_primary_focus": true,
            "spacing": 24
          }}
        ]
      }},
      "choreography": {{
        "state_progression": ["initial", "reveal", "emphasis"],
        "motion_energy": "low",
        "beats": [
          {{ "t": 0.0, "type": "setup", "description": "Show initial state" }},
          {{ "t": 1.5, "type": "reveal", "description": "Highlight keyword" }}
        ],
        "elements": [
          {{
            "id": "el_main",
            "zone_id": "zone_left",
            "type": "text_block",
            "content": "Wrong Way",
            "enter_time": 0.2,
            "enter_animation": "fade_in",
            "enter_duration": 0.3,
            "emphasis_word": "search",
            "emphasis_time": 1.5,
            "emphasis_effect": "highlight_pulse"
          }}
        ]
      }},
      "transition_from_previous": "cut",
      "complexity_check": {{
        "teaching_ideas": 1,
        "major_objects": 2,
        "visible_words": 6,
        "simultaneous_motions": 2,
        "within_budget": true
      }}
    }}
  ]
}}

CRITICAL:
- Every zone bounds MUST stay within the safe area.
- Zones must NOT overlap.
- Element timing must use RELATIVE timestamps.
- Complexity_check must be honest — if over budget, simplify the scene.
"""


def run_scene_structuring(
    visual_map: list[dict],
    alignment: dict,
    script_understanding: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.25,
) -> list[dict]:
    """
    Convert approved visual_map into concrete scene specifications.

    Args:
        visual_map:           Approved visual map from Phase 2/3.
        alignment:            WhisperX alignment data.
        script_understanding: Output from Phase 1.
        api_key:              OpenAI API key.
        model:                Model identifier.
        temperature:          Sampling temperature.

    Returns:
        List of scene dicts ready for frontend rendering.
    """
    logger.info("Phase 4: Scene Structuring — building concrete scenes…")

    system = SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
    )

    user_prompt = f"""Convert this approved visual map into concrete scene specifications.

VISUAL MAP (approved by human):
{json.dumps(visual_map, indent=2)}

SCRIPT UNDERSTANDING:
Main concept: {script_understanding.get('main_concept', '?')}
Narrative type: {script_understanding.get('narrative_type', '?')}

INSTRUCTIONS:
1. Each visual segment becomes exactly one scene.
2. Set pixel-precise layout zones within the 1080×1056 canvas (60px margins).
3. Define element choreography with RELATIVE timestamps.
4. Verify complexity budget for each scene.
5. Choose appropriate transitions between scenes.
6. Preserve any asset references from the visual map.

Return a JSON object with a "scenes" key."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=6000,
        json_mode=True,
        agent_name="Scene Structurer",
    )

    scenes_raw = result.get("scenes", result if isinstance(result, list) else [])

    # Enrich with word-level timestamps
    scenes = _enrich_with_words(scenes_raw, alignment)

    # Validate layouts
    for scene in scenes:
        layout = scene.get("layout", {})
        _validate_layout(layout)

    # Log summary
    logger.info(f"  Structured {len(scenes)} scenes")
    for s in scenes:
        budget = s.get("complexity_check", {})
        budget_ok = budget.get("within_budget", True)
        logger.info(
            f"  {s['scene_id']}: [{s['start']:.2f}s–{s['end']:.2f}s] "
            f"({s['duration']:.2f}s) "
            f"strategy={s.get('visual_strategy', '?')} "
            f"budget={'✓' if budget_ok else '⚠ OVER'}"
        )

    return scenes


# ======================================================================
# Internal helpers
# ======================================================================

def _enrich_with_words(scenes_raw: list, alignment: dict) -> list:
    """Attach word-level timestamps (relative) to each scene."""
    all_words = []
    for seg in alignment.get("segments", []):
        all_words.extend(seg.get("words", []))

    enriched = []
    for idx, raw in enumerate(scenes_raw):
        scene_id = raw.get("scene_id", f"scene_{idx + 1:03d}")
        start = round(float(raw.get("start", 0)), 3)
        end = round(float(raw.get("end", 0)), 3)
        duration = round(end - start, 3)

        # Collect words within this scene's window
        kw_set = {
            k.lower().strip(".,!?;:'\"")
            for k in raw.get("keywords", [])
        }
        scene_words = []
        for w in all_words:
            if w["start"] >= (start - 0.05) and w["end"] <= (end + 0.05):
                word_clean = w["word"].lower().strip(".,!?;:'\"")
                scene_words.append({
                    "word": w["word"],
                    "start": round(w["start"] - start, 3),  # RELATIVE
                    "end": round(w["end"] - start, 3),       # RELATIVE
                    "emphasis": word_clean in kw_set,
                })

        scene = {
            "scene_id": scene_id,
            "text": raw.get("text", ""),
            "start": start,
            "end": end,
            "duration": duration,
            "visual_strategy": raw.get("visual_strategy", "kinetic_text"),
            "visual_description": raw.get("visual_description", ""),
            "teaching_goal": raw.get("teaching_goal", ""),
            "keywords": raw.get("keywords", []),
            "words": scene_words,
            "assets": raw.get("assets", []),
            "asset_fallback": raw.get("asset_fallback", "css_svg"),
            "layout": raw.get("layout", {}),
            "choreography": raw.get("choreography", {}),
            "transition_from_previous": raw.get("transition_from_previous", "fade"),
            "complexity_check": raw.get("complexity_check", {}),
        }
        enriched.append(scene)

    return enriched


def _validate_layout(layout: dict) -> dict:
    """Clamp layout zones to safe area."""
    zones = layout.get("zones", [])

    if "safe_area" not in layout:
        layout["safe_area"] = {"top": 60, "right": 60, "bottom": 60, "left": 60}

    sa = layout["safe_area"]

    for zone in zones:
        bounds = zone.get("bounds", {})
        x = max(bounds.get("x", 60), sa["left"])
        y = max(bounds.get("y", 60), sa["top"])
        w = bounds.get("width", 400)
        h = bounds.get("height", 300)

        if x + w > 1080 - sa["right"]:
            w = 1080 - sa["right"] - x
        if y + h > 1056 - sa["bottom"]:
            h = 1056 - sa["bottom"] - y

        zone["bounds"] = {
            "x": x, "y": y,
            "width": max(w, 50), "height": max(h, 50),
        }

    layout["zones"] = zones
    return layout
