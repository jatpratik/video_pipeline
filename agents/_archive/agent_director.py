"""
Agent 3 — Visual Director
============================
Decides HOW the explanation should look visually.
Segments narration into "visual teaching moments" and assigns
importance scores, visual approaches, and composition strategies.

Thinks like a motion designer and cinematic explainer director.
"""

import json
import logging
from .llm_client import call_llm
from .design_system import get_design_system_prompt, get_visual_language_prompt

logger = logging.getLogger("video_pipeline.agents.director")

SYSTEM_PROMPT = """You are an expert VISUAL DIRECTOR for educational explainer videos.

You think like:
- A cinematic motion designer
- An educational animator
- A visual storytelling expert

Your job is to divide a narration into VISUAL TEACHING MOMENTS and decide
exactly how each moment should be visually presented.

This is NOT "choose a template." This is:
"What is the CLEAREST visual explanation for this narration?"

{design_system}

{visual_language}

CONCEPT ANALYSIS:
{concept_analysis}

RESEARCH INSIGHTS:
{research_insights}

SCENE RULES:
1. Each scene should be 2–8 seconds
2. Merge very short sentences (< 2s) with adjacent content
3. Split long segments (> 8s) at natural idea boundaries
4. Scenes MUST be contiguous (end of N == start of N+1)
5. Scenes MUST cover the ENTIRE narration

IMPORTANCE SCORING (0.0 to 1.0):
- 0.8–1.0: HIGH — Key revelation, critical concept, dramatic moment
  → Rich visual treatment, more animation, cinematic motion
- 0.5–0.7: MEDIUM — Supporting explanation, context
  → Clean visual, standard animation
- 0.2–0.4: LOW — Setup, transition, simple statement
  → Minimal visual, simple text or fade

VISUAL APPROACH TYPES (not fixed templates — describe freely):
- text_emphasis: Words appearing with glow/scale emphasis
- process_flow: Sequential nodes/steps with connections
- transformation: Input transforms through process to output
- comparison: Side-by-side or before/after contrast
- data_visualization: Metrics, counters, progress indicators
- diagram: Structural relationship visualization
- code_display: Terminal/code with typing animation
- metaphor_animation: Visual metaphor brought to life
- highlight_reveal: Progressive disclosure with spotlight

You MUST return a JSON object:

{{
  "scenes": [
    {{
      "scene_id": "scene_001",
      "text": "narration text for this scene",
      "start": 0.52,
      "end": 3.84,
      "importance": 0.8,
      "visual_approach": "process_flow",
      "visual_concept": "Detailed description of what to show and why it teaches the concept",
      "composition": {{
        "layout": "centered|split|stacked|scattered",
        "focal_point": "where the viewer's eye should go",
        "element_count": 3,
        "text_placement": "where text appears relative to graphics"
      }},
      "motion_style": {{
        "energy": "calm|moderate|dynamic",
        "camera": "static|slow_zoom|pan|none",
        "pacing": "steady|building|dramatic_pause"
      }},
      "color_intent": {{
        "concept_name": "semantic_color_reason"
      }},
      "visual_metaphor": "the metaphor being used if any",
      "keywords": ["word1", "word2"],
      "elements": ["label1", "label2"],
      "transition_from_previous": "cut|fade|morph|build_on"
    }}
  ]
}}

CRITICAL:
- Think in VISUAL TEACHING MOMENTS, not just "scenes"
- Each scene should HELP THE VIEWER UNDERSTAND one thing clearly
- Higher importance = richer treatment, not more clutter
- Maintain visual consistency across scenes
- Prioritize: clarity > beauty > complexity
- Keep all text descriptions (especially visual_concept) brief and concise. Use 1-2 sentences maximum for visual_concept. This is essential to stay under the output token limit.
"""


def run_visual_direction(
    alignment: dict,
    concept_analysis: dict,
    research_insights: dict,
    visual_language: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> list[dict]:
    """
    Segment narration into visual teaching moments with importance scoring.

    Args:
        alignment:         WhisperX alignment data.
        concept_analysis:  Output from Agent 1.
        research_insights: Output from Agent 2.
        visual_language:   Current visual language state.
        api_key:           OpenAI API key.
        model:             Model identifier.
        temperature:       Sampling temperature.

    Returns:
        List of enriched scene dicts with visual direction.
    """
    logger.info("Agent 3: Directing visual storytelling…")

    segments = alignment.get("segments", [])
    if not segments:
        return []

    # Chunking: split segments into groups of 8 to avoid LLM output token limits (4096 tokens)
    chunk_size = 8
    chunks = [segments[i:i + chunk_size] for i in range(0, len(segments), chunk_size)]
    scenes_raw = []

    for chunk_idx, chunk in enumerate(chunks):
        logger.info(f"  Director: Processing chunk {chunk_idx + 1}/{len(chunks)} ({len(chunk)} segments)…")
        chunk_alignment = {"segments": chunk}
        narration_block = _format_narration(chunk_alignment)
        chunk_start = chunk[0]["start"]
        chunk_end = chunk[-1]["end"]
        chunk_duration = chunk_end - chunk_start

        system = SYSTEM_PROMPT.format(
            design_system=get_design_system_prompt(),
            visual_language=get_visual_language_prompt(visual_language),
            concept_analysis=json.dumps(concept_analysis, indent=2),
            research_insights=json.dumps(research_insights, indent=2),
        )

        history_context = ""
        if scenes_raw:
            # Include the last few scenes for visual continuity and sequence tracking
            recent_scenes = []
            for s in scenes_raw[-3:]:
                # Extract a lightweight version to save prompt tokens
                recent_scenes.append({
                    "scene_id": s.get("scene_id"),
                    "end": s.get("end"),
                    "visual_approach": s.get("visual_approach"),
                    "visual_concept": s.get("visual_concept")
                })
            history_context = f"\nPREVIOUSLY GENERATED SCENES (for continuity):\n{json.dumps(recent_scenes, indent=2)}\n"

        user_prompt = f"""{history_context}
You are analyzing a CHUNK of the narration (Chunk {chunk_idx + 1} of {len(chunks)}).
Narration start time: {chunk_start:.2f}s, end time: {chunk_end:.2f}s, duration: {chunk_duration:.2f}s.

Here is the narration chunk with word-level timestamps:
{narration_block}

Divide this chunk into VISUAL TEACHING MOMENTS.
RULES FOR CHUNK PROCESSING:
1. Start your first scene in this chunk at exactly {chunk_start:.2f}s.
2. End your last scene in this chunk at exactly {chunk_end:.2f}s.
3. The scenes in this chunk must be contiguous (the end time of one scene must equal the start time of the next).
4. Continue the scene numbering from the previous chunk. The next scene ID should be 'scene_{len(scenes_raw) + 1:03d}'.
5. For each scene, return the complete JSON object format specified in the system prompt.
6. Keep descriptions concise (visual_concept should be 1-2 sentences maximum).

Return a JSON object with a "scenes" key containing the scenes for this chunk."""

        result = call_llm(
            system_prompt=system,
            user_prompt=user_prompt,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=3000,
            json_mode=True,
            agent_name=f"Director (Chunk {chunk_idx + 1})",
        )

        chunk_scenes = result.get("scenes", result if isinstance(result, list) else [])
        if isinstance(chunk_scenes, list):
            scenes_raw.extend(chunk_scenes)
        else:
            logger.error(f"  Director: Unexpected output format in chunk {chunk_idx + 1}: {result}")

    # Extract and enrich all scenes
    scenes = _enrich_scenes(scenes_raw, alignment)

    # Log summary
    for s in scenes:
        imp = s.get("importance", 0.5)
        imp_label = "HIGH" if imp >= 0.8 else "MED" if imp >= 0.5 else "LOW"
        logger.info(
            f"  {s['scene_id']}: [{s['start']:.2f}s–{s['end']:.2f}s] "
            f"({s['duration']:.2f}s) "
            f"importance={imp_label}({imp:.1f}) "
            f"approach={s.get('visual_approach', '?')}"
        )

    return scenes


# ======================================================================
# Internal helpers
# ======================================================================

def _format_narration(alignment: dict) -> str:
    """Format alignment data for the LLM prompt."""
    lines = []
    for seg in alignment["segments"]:
        lines.append(f"[{seg['start']:.2f}s – {seg['end']:.2f}s] {seg['text']}")
        word_parts = [
            f"{w['word']}({w['start']:.2f}–{w['end']:.2f})"
            for w in seg["words"]
        ]
        lines.append(f"  Words: {' | '.join(word_parts)}")
        lines.append("")
    return "\n".join(lines)


def _enrich_scenes(scenes_raw: list, alignment: dict) -> list:
    """
    Validate and enrich scenes with word-level timestamps.
    Preserves all Phase 1 compatibility fields.
    """
    # Flatten all words
    all_words = []
    for seg in alignment["segments"]:
        all_words.extend(seg["words"])

    enriched = []
    current_time = 0.0

    for idx, raw in enumerate(scenes_raw):
        scene_id = raw.get("scene_id", f"scene_{idx + 1:03d}")
        
        # Enforce exactly contiguous scenes to naturally eliminate audio gaps
        start = current_time
        
        # Read the raw end time, but ensure the scene has a minimum positive duration
        raw_end = round(float(raw.get("end", 0)), 3)
        end = max(start + 0.1, raw_end)
        
        duration = round(end - start, 3)
        current_time = end

        # Collect words within this scene
        kw_set = {k.lower().strip(".,!?;:'\"") for k in raw.get("keywords", [])}
        scene_words = []
        for w in all_words:
            if w["start"] >= (start - 0.05) and w["end"] <= (end + 0.05):
                word_clean = w["word"].lower().strip(".,!?;:'\"")
                scene_words.append({
                    "word": w["word"],
                    "start": round(w["start"] - start, 3),
                    "end": round(w["end"] - start, 3),
                    "emphasis": word_clean in kw_set,
                })

        scene = {
            # Core fields (Phase 1 compatible)
            "scene_id": scene_id,
            "text": raw.get("text", ""),
            "start": start,
            "end": end,
            "duration": duration,
            "keywords": raw.get("keywords", []),
            "elements": raw.get("elements", []),
            "words": scene_words,

            # Phase 2 enrichments
            "importance": raw.get("importance", 0.5),
            "visual_approach": raw.get("visual_approach", "text_emphasis"),
            "visual_concept": raw.get("visual_concept", ""),
            "visual_metaphor": raw.get("visual_metaphor", ""),
            "composition": raw.get("composition", {}),
            "motion_style": raw.get("motion_style", {}),
            "color_intent": raw.get("color_intent", {}),
            "transition_from_previous": raw.get("transition_from_previous", "fade"),
        }
        enriched.append(scene)

    return enriched
