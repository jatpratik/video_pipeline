"""
Agent — Visual Reasoner (Phase 2)
=====================================
Reads the entire script + understanding and produces a narration-to-visual map.
Thinks like a human educator deciding the best visual approach for each part
of the script. Uses a dynamic strategy toolbox — NO rigid hierarchy.

Outputs visual segments covering 4–12 seconds each, targeting 8–15 segments
for a 60-second video. Each segment has ONE core teaching idea.
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt

logger = logging.getLogger("video_pipeline.agents.visual_reasoner")

SYSTEM_PROMPT = """You are a MASTER EDUCATIONAL VISUAL DESIGNER planning an explainer YouTube Short.

You think like a human educator deciding how to visually represent each part of a narration.
Your PRIMARY goal: lowest cognitive load for the viewer. Every visual must be instantly understandable.

{design_system}

YOUR PROCESS:
1. Read the ENTIRE script end-to-end.
2. For each logical section, decide: what is the BEST visual strategy to teach this?
3. Group sentences that share ONE teaching idea into a SINGLE visual segment.
4. Map each segment to exact text spans with start/end timestamps.

VISUAL STRATEGY TOOLBOX (choose the BEST fit — there is NO fixed order or hierarchy):
- story_sequence: A multi-beat visual story that unfolds across the span.
- diagram_flow: Process/pipeline/flow diagram with nodes and connections.
- metaphor_animation: Real-world metaphor brought to life (e.g., funnel, conveyor belt).
- ui_mockup: Interface or app screen mockup showing the concept in context.
- kinetic_text: Typographic emphasis of spoken words — massive text, reveals, highlights.
- comparison: Side-by-side or before/after contrast showing differences.
- transformation: Input visually morphing into output to show a process.
- image_montage: Key images with Ken Burns effect or reveal animations.
- code_display: Terminal/code with typing animation and syntax highlighting.
- data_visualization: Charts, counters, metrics, progress indicators.
- highlight_focus: Zooming into or highlighting a specific part of an existing visual.

RULES:
1. Think in MACRO-SCENES. Group related sentences into large, cohesive scenes.
2. Target 4–8 macro-scenes for a 60-second video.
3. Each scene should span 8–15 seconds.
4. Segments must be CONTIGUOUS (end of N == start of N+1) and cover the ENTIRE script.
5. Do NOT over-edit. Keep objects BIG. Align with the script sequence simply. The visuals must look realistic and easily understandable.
6. Choose the strategy that BEST teaches the concept — do NOT default to text.
7. If a concept is abstract, find a CONCRETE metaphor or diagram.
8. If a concept is a process, use diagram_flow or transformation.
9. Only use kinetic_text as a LAST RESORT when no visual representation improves understanding.

You MUST return a JSON object:

{{
  "global_visual_theme": "A high-level description of the consistent visual aesthetic across all scenes (e.g., 'Sleek Dark Mode Dashboard', 'Clean Flat Light UI').",
  "visual_map": [
    {{
      "segment_id": "vs_001",
      "text_span": "The exact narration text this segment covers",
      "start_time": 0.52,
      "end_time": 4.20,
      "visual_strategy": "comparison",
      "visual_description": "Detailed description of what to show and HOW it teaches the concept. Be specific about objects, layout, and motion.",
      "key_elements": ["element_1", "element_2"],
      "keywords_to_emphasize": ["word1", "word2"],
      "teaching_goal": "What the viewer should understand after seeing this segment",
      "complexity_estimate": "low|medium|high"
    }}
  ]
}}

CRITICAL:
- Think like a TEACHER, not a designer. Every choice must serve comprehension.
- Be SPECIFIC in visual_description — describe exact objects, positions, and transformations.
- Keep descriptions concise (2–3 sentences max per visual_description).
- Ensure visual_strategy MATCHES the concept. Do not assign random strategies.
"""


def run_visual_reasoning(
    script_understanding: dict,
    alignment: dict,
    script_text: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> list[dict]:
    """
    Produce a narration-to-visual map for the entire script.

    Args:
        script_understanding: Output from Phase 1.
        alignment:            WhisperX alignment data.
        script_text:          Original narration script text.
        api_key:              OpenAI API key.
        model:                Model identifier.
        temperature:          Sampling temperature.

    Returns:
        List of visual segment dicts (the visual_map).
    """
    logger.info("Phase 2: Visual Reasoning — building narration-to-visual map…")

    segments = alignment.get("segments", [])
    if not segments:
        return []

    total_duration = segments[-1]["end"]

    # Build aligned narration for the prompt
    narration_block = "\n".join(
        f"[{seg['start']:.2f}s–{seg['end']:.2f}s] {seg['text']}"
        for seg in segments
    )

    system = SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
    )

    user_prompt = f"""Plan the visual map for this educational video.

SCRIPT UNDERSTANDING (from Phase 1):
{json.dumps(script_understanding, indent=2)}

FULL SCRIPT:
{script_text}

ALIGNED NARRATION (with timestamps):
{narration_block}

Total duration: {total_duration:.2f} seconds

INSTRUCTIONS:
1. Read the entire script and identify the overarching global visual theme.
2. Group related sentences into large macro-scenes (each 8–15 seconds).
3. For each scene, choose the BEST visual strategy from the toolbox.
4. Ensure scenes are contiguous and cover the full duration.
5. Target 4–8 macro-scenes total to avoid chaotic over-editing.
6. Keep visuals realistic, simple, and easily understandable.

Return a JSON object with "global_visual_theme" and "visual_map" keys."""

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=4000,
        json_mode=True,
        agent_name="Visual Reasoner",
    )

    visual_map = result.get("visual_map", result if isinstance(result, list) else [])

    if visual_map:
        # Hardcode gap closing to ensure perfectly contiguous scenes (solves audio/video duration mismatch)
        visual_map[0]["start_time"] = 0.0
        for i in range(len(visual_map) - 1):
            # Ensure the current scene's end exactly matches the next scene's start
            visual_map[i]["end_time"] = visual_map[i+1].get("start_time", 0.0)
        # Ensure the final scene ends exactly at the total duration
        visual_map[-1]["end_time"] = total_duration

    # Validate and fix segment IDs
    for idx, seg in enumerate(visual_map):
        if "segment_id" not in seg:
            seg["segment_id"] = f"vs_{idx + 1:03d}"
        # Ensure required fields have defaults
        seg.setdefault("visual_strategy", "kinetic_text")
        seg.setdefault("visual_description", "")
        seg.setdefault("key_elements", [])
        seg.setdefault("keywords_to_emphasize", [])
        seg.setdefault("teaching_goal", "")
        seg.setdefault("complexity_estimate", "medium")

    # Log summary
    logger.info(f"  Generated {len(visual_map)} visual segments")
    strategy_counts = {}
    for seg in visual_map:
        s = seg.get("visual_strategy", "unknown")
        strategy_counts[s] = strategy_counts.get(s, 0) + 1

    for strategy, count in sorted(strategy_counts.items()):
        logger.info(f"    {strategy}: {count} segments")

    for seg in visual_map:
        start = seg.get("start_time", 0)
        end = seg.get("end_time", 0)
        logger.info(
            f"  {seg['segment_id']}: [{start:.2f}s–{end:.2f}s] "
            f"strategy={seg['visual_strategy']} "
            f"goal=\"{seg.get('teaching_goal', '?')[:60]}…\""
        )

    return visual_map
