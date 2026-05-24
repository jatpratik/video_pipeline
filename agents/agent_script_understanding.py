"""
Agent — Script Understanding (Phase 1)
==========================================
Deeply analyzes the narration script to extract educational meaning,
teaching objectives, concept relationships, visual metaphors, and
educational animation patterns.

Merges the old Agent 1 (Concept) and Agent 2 (Research) into a single
LLM call for efficiency.
"""

import json
import logging
from .llm_client import call_llm

logger = logging.getLogger("video_pipeline.agents.script_understanding")

SYSTEM_PROMPT = """You are an expert EDUCATIONAL CONTENT ANALYST and VISUAL RESEARCH SPECIALIST.

Your job is to deeply understand a narration script for an educational YouTube Short,
then identify the best visual strategies, metaphors, and teaching patterns.

Think like:
- A great teacher preparing a lesson
- An instructional designer mapping learning objectives
- A cognitive scientist understanding how people learn
- A motion designer who knows how to visually explain concepts

ANALYZE the script and produce a comprehensive understanding.

You MUST return a JSON object with these fields:

{
  "main_concept": "The primary topic being taught",
  "viewer_goal": "What the viewer should understand after watching",
  "narrative_type": "problem_solution|comparison|process_explanation|concept_introduction|warning_lesson",
  "teaching_structure": [
    "Step-by-step ordered list of ideas being taught"
  ],
  "core_relationships": [
    "Causal/logical connections between concepts (e.g., 'A causes B', 'A contrasts with B')"
  ],
  "difficult_concepts": [
    {
      "concept": "the difficult idea",
      "why_difficult": "why viewers might struggle",
      "visual_hint": "how to simplify it visually"
    }
  ],
  "emotional_arc": [
    {
      "moment": "description of tonal shift",
      "tone": "question|problem|insight|solution|warning|revelation",
      "intensity": 0.0
    }
  ],
  "key_terms": [
    {
      "term": "important term",
      "definition": "what it means in this context",
      "visual_hint": "how this could be shown visually"
    }
  ],
  "visual_metaphors": [
    {
      "concept": "the concept being visualized",
      "metaphor": "the visual metaphor to use",
      "why": "why this metaphor works for teaching this concept"
    }
  ],
  "educational_patterns": [
    {
      "pattern": "progressive_reveal|comparison|transformation|cause_effect|accumulation|zoom_focus",
      "apply_to": "which part of the narration this applies to",
      "why": "why this pattern is effective here"
    }
  ],
  "visual_warnings": [
    "things to AVOID in the visual design for this topic"
  ]
}

IMPORTANT:
- Focus on EDUCATIONAL MEANING, not just content extraction.
- Identify what is HARD to understand and why.
- Identify what RELATIONSHIPS exist between ideas.
- Choose visual metaphors that viewers will INSTANTLY understand.
- Prioritize CLARITY over creativity.
- Avoid overly abstract or artistic representations.
"""


def run_script_understanding(
    alignment: dict,
    script_text: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> dict:
    """
    Analyze narration to extract educational meaning and visual strategies.

    Combines the old Agent 1 (Concept Understanding) and Agent 2 (Research)
    into a single LLM call.

    Args:
        alignment:   WhisperX alignment data.
        script_text: Original narration script.
        api_key:     OpenAI API key.
        model:       Model identifier.
        temperature: Sampling temperature.

    Returns:
        Script understanding dict with concept analysis + visual research.
    """
    logger.info("Phase 1: Analyzing educational concepts and visual strategies…")

    # Build context from alignment segments
    segments_text = "\n".join(
        f"[{seg['start']:.2f}s–{seg['end']:.2f}s] {seg['text']}"
        for seg in alignment.get("segments", [])
    )

    total_duration = (
        alignment["segments"][-1]["end"]
        if alignment.get("segments")
        else 0
    )

    user_prompt = f"""Here is the narration script for an educational YouTube Short:

SCRIPT:
{script_text}

ALIGNED SEGMENTS (with timestamps):
{segments_text}

Total duration: {total_duration:.2f} seconds

Analyze this script deeply:
1. What is being taught? What should the viewer understand?
2. What concepts are difficult and why?
3. What relationships exist between ideas?
4. What is the emotional/tonal arc?
5. What are the BEST visual metaphors for each concept?
6. What educational animation patterns fit this narration?
7. What visual pitfalls should we avoid?

Return your analysis as a JSON object."""

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=3000,
        json_mode=True,
        agent_name="Script Understanding",
    )

    # Log summary
    logger.info(f"  Main concept: {result.get('main_concept', '?')}")
    logger.info(f"  Viewer goal: {result.get('viewer_goal', '?')}")
    logger.info(f"  Narrative type: {result.get('narrative_type', '?')}")
    logger.info(
        f"  Teaching steps: {len(result.get('teaching_structure', []))}, "
        f"Difficult concepts: {len(result.get('difficult_concepts', []))}"
    )
    metaphors = result.get("visual_metaphors", [])
    logger.info(f"  Visual metaphors: {len(metaphors)}")
    for m in metaphors[:3]:
        logger.info(f"    • {m.get('concept', '?')} → {m.get('metaphor', '?')}")

    return result
