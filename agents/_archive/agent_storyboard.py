"""
Agent — Storyboard Planner (Educational Visual Intelligence Architecture)
========================================================
Pass 1: Global Storyboard
Analyzes the entire script and concept to define the overarching narrative arc,
visual identity, educational pacing, and teaching philosophy.

Pass 2: Per-Scene Storyboard
Takes the global storyboard context, SELECTS a visual pattern, educational shot type,
and pedagogical motion. Optimizes for 1-second comprehension.
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt
from .visual_patterns import (
    get_patterns_prompt,
    get_shots_prompt,
    get_camera_prompt,
    get_beats_prompt,
    get_state_progressions_prompt,
    get_motion_energy_prompt,
)

logger = logging.getLogger("video_pipeline.agents.storyboard")

GLOBAL_SYSTEM_PROMPT = """You are a MASTER EDUCATIONAL VISUAL COMMUNICATOR planning an explainer video.

You think like a teacher. Every choice you make serves ONE goal: 
"Can a mobile viewer understand the spoken sentence within 1 second without cognitive overload?"

{design_system}

You must read the entire script and concept analysis and produce a cohesive educational strategy.
The video must feel like ONE directed educational film — not random AI-generated slides.

GLOBAL VISUAL PRINCIPLES:
1. ONE CORE IDEA PER SCENE
2. SPEECH-FIRST VISUALIZATION (Visuals exist only to support the narration sentence)
3. LARGE MOBILE-READABLE ELEMENTS
4. TOP-55% SAFE AREA ONLY
5. INSTANT RECOGNIZABILITY (1-second comprehension)
6. MOTION MUST EXPLAIN (Remove decorative motion, cinematic camera movement, ambient particles)
7. CLEAR VISUAL HIERARCHY (One primary focus point only)
8. VISUAL TIMING MUST MATCH SPOKEN WORDS
9. TRANSFORMATIONS OVER TRANSITIONS (Prefer step-by-step reveals, highlights, morphing)
10. EDUCATIONAL CONTRAST (before/after, wrong/right)
11. COGNITIVE LOAD MINIMIZATION

Return a JSON object:
{{
  "global_storyboard": {{
    "visual_identity": "The overall visual personality. Be specific: 'dark technical with massive text blocks and green/red educational contrast' NOT 'modern and clean'",
    "educational_pacing": "How pacing evolves. e.g. 'Slow concept reveals, pausing for viewer comprehension, rapid failure comparisons'",
    "recurring_objects": [
      "2-4 specific visual objects that persist across scenes. Must be huge and instantly recognizable."
    ],
    "motion_language": "The dominant motion style. e.g. 'Stable frame, direct highlights on keywords, morphing nodes, no camera drift.'",
    "visual_teaching_philosophy": "HOW we teach visually. e.g. 'We build understanding by showing a huge system first, then breaking it, then highlighting the fix.'",
    "dominant_contrast_style": "How we show right vs wrong. e.g. 'Red broken JSON vs Green validated JSON'",
    "energy_arc": "How motion energy evolves strictly to support the teaching."
  }}
}}
"""

SCENE_SYSTEM_PROMPT = """You are an EDUCATIONAL VISUAL DESIGNER creating frame-by-frame visual plans
for an educational YouTube Short.

You are NOT designing cinema. You are designing INSTANT COMPREHENSION.
Every visual choice must TEACH. Every motion must EXPLAIN.

{design_system}

{patterns}

{shots}

{camera}

{beats}

{state_progressions}

{motion_energy}

YOUR THINKING PROCESS (follow this order):

1. READ the narration text. What is being SAID?
2. What should the viewer UNDERSTAND after seeing this scene (in < 1 second)?
3. What is the ONE CORE IDEA for this scene?
4. What VISUAL METAPHOR best teaches this using massive mobile-readable objects?
5. How can we minimize cognitive load (remove anything unnecessary)?
6. How does the motion map EXACTLY to the spoken words?

ANTI-PATTERNS (things you must NEVER do):
- Cinematic camera drift, orbital movement, pull-outs.
- Layered parallax, atmospheric effects, floating particles.
- More than one core concept per scene.
- Small UI cards, dense dashboards, tiny text.
- Random glassmorphism/neon effects that don't teach anything.

Return a JSON object:
{{
  "storyboard": {{
    "scene_goal": "What exact mental model should the viewer have after this scene?",
    "core_visual": "The ONE dominant object or transformation. Be specific and massive.",
    "viewer_takeaway": "The one sentence the viewer realizes.",
    "visual_focus": "The exact element that gets 100% of the attention.",
    "sync_keywords": [
      {{"word": "spoken word", "action": "exact visual transformation that happens when this word is spoken"}}
    ],
    "selected_pattern": "pattern_name from EDUCATIONAL VISUAL PATTERNS library",
    "educational_shot_type": "shot_name from EDUCATIONAL SHOT TYPES library",
    "camera_behavior": "camera_name from PEDAGOGICAL MOTION BEHAVIORS library (must be stable)",
    "motion_energy": "low | medium (no intense or chaotic motion)",
    "state_progression": ["state_1", "state_2"],
    "beats": [
      {{ "t_ratio": 0.0, "type": "setup", "description": "Start stable" }},
      {{ "t_ratio": 0.5, "type": "emphasis", "description": "Highlight exactly when word is spoken" }}
    ],
    "continuity": {{
      "inherits_from_previous": "What visual elements carry over from previous scene",
      "persistent_elements": ["element names that should persist"]
    }},
    "primary_motion": "The main teaching action. e.g. 'Node splits into three smaller nodes.' NOT 'camera drifts'",
    "transformation_logic": "How does the visual STATE change to explain the concept?",
    "pattern_customization": {{
      "node_labels": ["Massive Label 1"],
      "custom_notes": "Scene-specific overrides to ensure massive size and simplicity"
    }}
  }}
}}
"""


def run_global_storyboard(
    script_text: str,
    concept_analysis: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> dict:
    """Run the global storyboard pass over the entire video."""
    logger.info("  Agent (Storyboard): Planning Global Narrative Arc…")

    system = GLOBAL_SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt()
    )

    user_prompt = f"""Analyze this educational concept and script:

CONCEPT ANALYSIS:
{json.dumps(concept_analysis, indent=2)}

FULL SCRIPT:
{script_text}

Think like an educational visual designer. Plan the teaching arc.
What is the viewer's journey? What massive visual objects persist across scenes?

Provide the Global Storyboard as JSON."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2000,
        json_mode=True,
        agent_name="Global Storyboard",
    )

    return result.get("global_storyboard", result)


def run_scene_storyboard(
    scene: dict,
    global_storyboard: dict,
    concept_analysis: dict,
    previous_scenes_storyboards: list,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> dict:
    """
    Run the per-scene storyboard planning.
    Selects pattern, educational shot, pedagogical motion.
    Defines continuity with adjacent scenes.
    """
    logger.info(f"  Agent (Storyboard): Planning Scene {scene['scene_id']}…")

    system = SCENE_SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
        patterns=get_patterns_prompt(),
        shots=get_shots_prompt(),
        camera=get_camera_prompt(),
        beats=get_beats_prompt(),
        state_progressions=get_state_progressions_prompt(),
        motion_energy=get_motion_energy_prompt(),
    )

    # Build continuity context from previous scenes
    prev_context = ""
    if previous_scenes_storyboards:
        recent = previous_scenes_storyboards[-3:]
        prev_context = f"""
PREVIOUS SCENES (maintain continuity with these):
{json.dumps(recent, indent=2)}

The previous scene's visual state and elements should flow naturally into this scene."""

    scene_details = {
        "scene_id": scene.get("scene_id"),
        "text": scene.get("text"),
        "duration": scene.get("duration"),
        "importance": scene.get("importance"),
        "visual_approach": scene.get("visual_approach"),
        "visual_concept": scene.get("visual_concept"),
        "keywords": scene.get("keywords", []),
    }

    user_prompt = f"""Plan the educational storyboard for this scene:

GLOBAL STORYBOARD (follow this strictly):
{json.dumps(global_storyboard, indent=2)}
{prev_context}
CURRENT SCENE:
{json.dumps(scene_details, indent=2)}

THINK STEP BY STEP:
1. What is the narration SAYING in this scene?
2. What ONE CORE IDEA should the viewer UNDERSTAND visually in under 1 second?
3. What is the best EDUCATIONAL VISUAL PATTERN?
4. What EDUCATIONAL SHOT creates the most clarity?
5. What PEDAGOGICAL MOTION matches the spoken keywords perfectly?
6. How can we minimize cognitive load and ensure massive, mobile-readable objects?

Provide the per-scene Storyboard as JSON."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2500,
        json_mode=True,
        agent_name=f"Scene Storyboard ({scene['scene_id']})",
    )

    return result.get("storyboard", result)
