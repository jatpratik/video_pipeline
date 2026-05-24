"""
Agent — Layout Engine
========================
Produces DETERMINISTIC scene layout JSON with:
- Safe areas and composition zones
- STRICT Top-55% boundaries (1080x1056 visual render area)
- Mobile-first, large-typography focus
- Clean hierarchy with no decorative clutter
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt
from .visual_patterns import (
    get_pattern_details,
    get_shot_details,
)

logger = logging.getLogger("video_pipeline.agents.layout")

SYSTEM_PROMPT = """You are an EDUCATIONAL LAYOUT ENGINE for a vertical YouTube Short.

You produce DETERMINISTIC, pixel-precise layout specifications for a 1080×1056 canvas.
This canvas represents the TOP 55% of a 1080x1920 video (the safe area for mobile viewers).
Your layouts must prioritize INSTANT COMPREHENSION.

{design_system}

CANVAS: 1080px wide × 1056px tall.
SAFE AREA: 60px margins on all sides → usable content area is 960px × 936px.
The safe area starts at (60, 60) and ends at (1020, 996).

COMPOSITION RULES:
1. Primary focus must occupy massive space (50–80% of the usable canvas area).
2. Maximum 1-2 major elements on screen. DO NOT CLUTTER.
3. Typography must be massive. Minimum text size constraints apply.
4. Clean hierarchy: Center the main idea or use clean symmetrical horizontal splits for comparisons.
5. NO overlapping animated regions.
6. AVOID edge placement. Keep everything comfortably within the 60px margins.
7. DO NOT use "asymmetry" for artistic sake. Use symmetry or simple alignment for readability.

You MUST return a JSON object:

{{
  "layout": {{
    "safe_area": {{ "top": 60, "right": 60, "bottom": 60, "left": 60 }},
    "composition_type": "vertical_flow|horizontal_split|centered_hero|grid_layout",
    "zones": [
      {{
        "id": "zone_main",
        "bounds": {{ "x": 60, "y": 100, "width": 960, "height": 600 }},
        "purpose": "primary visual content",
        "content_type": "diagram|text|code|svg|mixed",
        "layout_mode": "flex_column|flex_row|grid|absolute",
        "is_primary_focus": true,
        "spacing": 40
      }}
    ],
    "screen_utilization_percent": 75,
    "primary_focus_percent": 70,
    "negative_space_percent": 25,
    "total_elements": 2
  }}
}}

ZONE RULES:
- Every zone must have unique id and pixel-precise bounds.
- Zones must NOT overlap.
- Zones must stay within the safe area (60px margins).
- At least one zone must be marked is_primary_focus: true.
- Keep the number of zones to an absolute minimum. 1-2 zones is ideal.
"""


def run_layout_engine(
    scene: dict,
    storyboard: dict,
    global_storyboard: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.2,
) -> dict:
    """
    Generate deterministic layout zones for a scene.

    Args:
        scene:             Scene dict with metadata.
        storyboard:        Per-scene storyboard with selected_pattern and educational_shot_type.
        global_storyboard: Global storyboard context.
        api_key:           OpenAI API key.
        model:             Model identifier.
        temperature:       Sampling temperature.

    Returns:
        Layout specification dict.
    """
    scene_id = scene["scene_id"]
    logger.info(f"  Agent (Layout Engine): Composing {scene_id}…")

    system = SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
    )

    # Get pattern and shot details
    pattern_name = storyboard.get("selected_pattern", "progressive_reveal")
    shot_name = storyboard.get("educational_shot_type", "hero_focus")
    pattern = get_pattern_details(pattern_name)
    shot = get_shot_details(shot_name)

    scene_context = {
        "scene_id": scene["scene_id"],
        "text": scene["text"],
        "duration": scene["duration"],
        "importance": scene.get("importance", 0.5),
    }

    user_prompt = f"""Design the educational layout for this scene:

SCENE:
{json.dumps(scene_context, indent=2)}

STORYBOARD DIRECTION:
{json.dumps(storyboard, indent=2)}

SELECTED VISUAL PATTERN: {pattern_name}
Pattern details: {pattern['description']}
Element structure: {json.dumps(pattern.get('element_structure', dict()))}

EDUCATIONAL SHOT TYPE: {shot_name}
Shot details: {shot['description']}
Shot layout: {shot['layout_strategy']}

GLOBAL VISUAL IDENTITY:
{json.dumps(global_storyboard, indent=2)}

REQUIREMENTS:
1. Keep the layout MASSIVE and SIMPLE.
2. Ensure everything fits entirely within the top 1080x1056 canvas.
3. Total elements must be 1-2 if possible.
4. Maximum 3 zones. Ideally 1 primary zone.

Return a JSON object with a "layout" key."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2000,
        json_mode=True,
        agent_name=f"Layout Engine ({scene_id})",
    )

    layout = result.get("layout", result)

    # Validate and fix basic constraints
    layout = _validate_layout(layout)

    # Log summary
    zones = layout.get("zones", [])
    util = layout.get("screen_utilization_percent", 0)
    focus = layout.get("primary_focus_percent", 0)
    logger.info(
        f"    Layout: {len(zones)} zones, "
        f"utilization={util}%, "
        f"primary_focus={focus}%, "
        f"type={layout.get('composition_type', '?')}"
    )

    return layout


def _validate_layout(layout: dict) -> dict:
    """Apply hard constraints to the layout."""
    zones = layout.get("zones", [])

    # Ensure safe area exists
    if "safe_area" not in layout:
        layout["safe_area"] = {"top": 60, "right": 60, "bottom": 60, "left": 60}

    sa = layout["safe_area"]

    # Clamp zones to safe area
    for zone in zones:
        bounds = zone.get("bounds", {})
        x = max(bounds.get("x", 60), sa["left"])
        y = max(bounds.get("y", 60), sa["top"])
        w = bounds.get("width", 400)
        h = bounds.get("height", 300)

        # Clamp right edge
        if x + w > 1080 - sa["right"]:
            w = 1080 - sa["right"] - x

        # Clamp bottom edge
        if y + h > 1056 - sa["bottom"]:
            h = 1056 - sa["bottom"] - y

        zone["bounds"] = {"x": x, "y": y, "width": max(w, 50), "height": max(h, 50)}

    layout["zones"] = zones
    return layout
