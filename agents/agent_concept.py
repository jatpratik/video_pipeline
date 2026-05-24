"""
Agent 1 — Concept Understanding
===================================
Deeply analyzes the narration to extract educational meaning,
teaching objectives, concept relationships, and emotional arc.

Thinks like a teacher and educational designer.
"""

import logging
from pathlib import Path

from .llm_client import call_llm

logger = logging.getLogger("video_pipeline.agents.concept")

SYSTEM_PROMPT = """You are an expert EDUCATIONAL CONTENT ANALYST.

Your job is to deeply understand a narration script for an educational explainer video.

Think like:
- A great teacher preparing a lesson
- An instructional designer mapping learning objectives
- A cognitive scientist understanding how people learn

ANALYZE the script and produce a comprehensive concept analysis.

You MUST return a JSON object with these fields:

{
  "main_concept": "The primary topic being taught",
  "viewer_goal": "What the viewer should understand after watching",
  "teaching_structure": [
    "Step-by-step ordered list of ideas being taught"
  ],
  "core_relationships": [
    "Causal/logical connections between concepts (e.g., 'A causes B', 'A contrasts with B')"
  ],
  "difficult_concepts": [
    "Concepts that need extra visual simplification to be understood"
  ],
  "emotional_arc": [
    {
      "moment": "description of tonal shift",
      "tone": "question|problem|insight|solution|warning|revelation",
      "intensity": 0.0 to 1.0
    }
  ],
  "key_terms": [
    {
      "term": "important term",
      "definition": "what it means in this context",
      "visual_hint": "how this could be shown visually"
    }
  ],
  "narrative_type": "problem_solution|comparison|process_explanation|concept_introduction|warning_lesson"
}

IMPORTANT:
- Focus on EDUCATIONAL MEANING, not just content extraction.
- Identify what is HARD to understand and why.
- Identify what RELATIONSHIPS exist between ideas.
- Think about what VISUAL APPROACH would best teach each idea.
"""


def run_concept_analysis(
    alignment: dict,
    script_text: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> dict:
    """
    Analyze narration to extract educational meaning.

    Args:
        alignment:   WhisperX alignment data.
        script_text: Original narration script.
        api_key:     OpenAI API key.
        model:       Model identifier.
        temperature: Sampling temperature.

    Returns:
        Concept analysis dict.
    """
    logger.info("Agent 1: Analyzing educational concepts…")

    # Build context from alignment segments
    segments_text = "\n".join(
        f"[{seg['start']:.2f}s–{seg['end']:.2f}s] {seg['text']}"
        for seg in alignment.get("segments", [])
    )

    total_duration = alignment["segments"][-1]["end"] if alignment.get("segments") else 0

    user_prompt = f"""Here is the narration script for an educational explainer video:

SCRIPT:
{script_text}

ALIGNED SEGMENTS (with timestamps):
{segments_text}

Total duration: {total_duration:.2f} seconds

Analyze this script deeply. What is being taught? What should the viewer understand?
What concepts are difficult? What relationships exist between ideas?
What is the emotional/tonal arc?

Return your analysis as a JSON object."""

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2048,
        json_mode=True,
        agent_name="Concept",
    )

    # Log summary
    logger.info(f"  Main concept: {result.get('main_concept', '?')}")
    logger.info(f"  Viewer goal: {result.get('viewer_goal', '?')}")
    logger.info(f"  Narrative type: {result.get('narrative_type', '?')}")
    logger.info(
        f"  Teaching steps: {len(result.get('teaching_structure', []))}, "
        f"Difficult concepts: {len(result.get('difficult_concepts', []))}"
    )

    return result
