"""
Agent — Animation Architect (Pedagogical Choreography)
==========================================================
Converts layout zones + storyboard into precise educational animation choreography.
Defines pedagogical motion, temporal beats, state progression, and focus progression.

Does NOT specify raw CSS positions. Produces a choreography that a renderer implements.
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt
from .visual_patterns import (
    get_motion_energy_prompt,
    get_depth_layers_prompt,
    get_camera_prompt,
    get_beats_prompt,
)

logger = logging.getLogger("video_pipeline.agents.architect")

SYSTEM_PROMPT = """You are an EDUCATIONAL ANIMATION CHOREOGRAPHER for explainer videos.

You define the EXACT sequence of events that happen in a scene to teach a concept.
Your motion design must be strictly PEDAGOGICAL. If motion does not improve understanding, remove it.

{design_system}

{motion_energy}

{depth_layers}

{camera}

CHOREOGRAPHY PHILOSOPHY:

1. 1-SECOND COMPREHENSION.
   The viewer must understand the scene instantly. Do not build up complexity slowly
   if it confuses the viewer. Keep it simple.

2. AVOID ALL DECORATIVE MOTION.
   No ambient floating. No decorative drift. No continuous motion loops.
   No cinematic pans. No layered atmospheric animation.

3. MOTION MUST EXPLAIN.
   Arrow follows data flow. Highlight appears on keyword. 
   Object transforms during explanation.
   Process steps appear sequentially.

4. EXACT NARRATION SYNCHRONIZATION.
   Major visual changes MUST align perfectly to narration timestamps.
   Avoid simultaneous unrelated movement.

5. FAST AND STABLE.
   Animations should complete quickly and clearly.
   Keep transitions under the cognitive load threshold.
   Once an animation finishes, the screen must remain completely STABLE for reading.

RETURN a JSON object with "scene_id" and "choreography" keys:

{{
  "scene_id": "scene_XXX",
  "choreography": {{
    "camera": {{
      "behavior": "static",
      "gsap_implementation": "tl.set('.canvas', {{scale: 1}});"
    }},
    "state_progression": ["state_1", "state_2"],
    "beats": [
      {{
        "t": 0.0,
        "type": "setup",
        "description": "Initial state",
        "elements_visible": 1
      }}
    ],
    "motion_energy": "low",
    "focus_progression": [
      {{ "t": 0.0, "focus_zone": "zone_main", "focus_element": "hero_node" }}
    ],
    "zone_choreography": [
      {{
        "zone_id": "zone_main",
        "elements": [
          {{
            "id": "element_id",
            "type": "node|text_block|connection_line|icon_badge|svg_shape|label",
            "content": "text content or label",
            "visual_description": "What this element LOOKS like. Keep it massive and simple.",
            "enter": {{
              "time": 0.3,
              "animation": "fade_in|scale_focus|sequential_reveal",
              "duration": 0.3,
              "ease": "power2.out"
            }},
            "emphasis": {{
              "trigger_word": "keyword",
              "trigger_time": 1.5,
              "effect": "highlight_pulse|simple_transform",
              "duration": 0.3
            }},
            "exit": {{
              "time": null,
              "animation": "none|fade_out",
              "duration": 0.3
            }},
            "style_hints": {{
              "accent_color": "#3b82f6",
              "size": "massive",
              "font": "primary",
              "border_style": "solid|none"
            }}
          }}
        ],
        "connections": [
          {{
            "from_element": "node_1",
            "to_element": "node_2",
            "type": "solid_arrow|dashed_line",
            "draw_time": 0.8,
            "draw_duration": 0.3,
            "color": "#3b82f6"
          }}
        ]
      }}
    ],
    "depth_layer_effects": {{
      "background": {{ "effect": "none" }},
      "fx": {{ "effect": "none" }}
    }},
    "transitions": {{
      "enter": {{ "type": "fade_in", "duration": 0.3 }},
      "exit": {{ "type": "fade_out", "duration": 0.3 }}
    }}
  }}
}}

QUALITY CHECKLIST (verify before outputting):
□ Is the camera 100% static?
□ Are all decorative and continuous animations removed?
□ Does every emphasis map exactly to a spoken keyword?
□ Is the scene visually calm and stable most of the time?
"""


def run_animation_architecture(
    scene: dict,
    concept_analysis: dict,
    layout: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.25,
) -> dict:
    """
    Create pedagogical animation choreography for a single scene.
    """
    scene_id = scene["scene_id"]
    logger.info(f"  Agent (Architect): Choreographing {scene_id}…")

    system = SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
        motion_energy=get_motion_energy_prompt(),
        depth_layers=get_depth_layers_prompt(),
        camera=get_camera_prompt(),
    )

    storyboard = scene.get("storyboard", {})

    scene_context = {
        "scene_id": scene["scene_id"],
        "text": scene["text"],
        "duration": scene["duration"],
        "importance": scene.get("importance", 0.5),
        "keywords": scene.get("keywords", []),
        "words": scene.get("words", []),
    }

    user_prompt = f"""Create pedagogical animation choreography for this scene:

SCENE (duration: {scene['duration']:.2f}s):
{json.dumps(scene_context, indent=2)}

STORYBOARD DIRECTION (follow this precisely):
{json.dumps(storyboard, indent=2)}

LAYOUT ZONES (reference by zone_id — do NOT invent positions):
{json.dumps(layout, indent=2)}

Main concept: {concept_analysis.get('main_concept', 'unknown')}

MOTION ENERGY: {storyboard.get('motion_energy', 'low')}
STATE PROGRESSION: {json.dumps(storyboard.get('state_progression', []))}

TEMPORAL BEATS from storyboard: {json.dumps(storyboard.get('beats', []))}

THINK LIKE A TEACHER:
1. Ensure the layout and objects are massive.
2. Synchronize visual reveals/highlights EXACTLY with spoken words.
3. Eliminate all unnecessary motion. Keep the screen stable.

Return a JSON object with "scene_id" and "choreography" keys."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=4000,
        json_mode=True,
        agent_name="Architect",
    )

    choreography = result.get("choreography", result)

    # Log summary
    zones = choreography.get("zone_choreography", [])
    beats = choreography.get("beats", [])
    energy = choreography.get("motion_energy", "?")
    camera = choreography.get("camera", {}).get("behavior", "static")
    elem_count = sum(len(z.get("elements", [])) for z in zones)
    logger.info(
        f"    Choreography: {elem_count} elements, {len(zones)} zones, "
        f"{len(beats)} beats, camera={camera}, energy={energy}"
    )

    return choreography
