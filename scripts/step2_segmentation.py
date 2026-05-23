"""
Step 2 — Scene Segmentation using OpenAI LLM
===============================================
Divides aligned narration into visual scenes.
The LLM chooses template types, identifies keywords for word-level
emphasis, and describes visual concepts — all optimised for educational
explainer content.

Output: scenes/scenes.json
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("video_pipeline.segmentation")

# ------------------------------------------------------------------
# Available visual templates the LLM may choose from
# ------------------------------------------------------------------
AVAILABLE_TEMPLATES = [
    {
        "name": "text_reveal",
        "description": (
            "Words appear sequentially with glow effects and emphasis "
            "animations. Best for introductions, key statements, questions, "
            "and definitions."
        ),
    },
    {
        "name": "node_diagram",
        "description": (
            "Pipeline/process nodes with animated connections. Best for "
            "explaining systems, multi-step processes, workflows, and "
            "architectures."
        ),
    },
    {
        "name": "code_terminal",
        "description": (
            "Terminal window with code typing effect and syntax highlighting. "
            "Best for technical concepts, code examples, API calls, and "
            "commands."
        ),
    },
    {
        "name": "data_flow",
        "description": (
            "Animated data packets flowing between nodes with glowing trails. "
            "Best for data processing, input/output flows, and "
            "transformations."
        ),
    },
    {
        "name": "comparison",
        "description": (
            "Side-by-side panels showing before/after or contrasting "
            "concepts. Best for pros/cons, old vs new, wrong vs right."
        ),
    },
    {
        "name": "metric_counter",
        "description": (
            "Large animated numbers and statistics with supporting text. "
            "Best for statistics, measurements, percentages, and "
            "quantitative data."
        ),
    },
]

# ------------------------------------------------------------------
# System prompt sent to the LLM
# ------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert AI video scene planner for EDUCATIONAL explainer videos.

Your job is to divide a narration script (with word-level timestamps) into visual scenes for an animated explainer video.

DESIGN PRINCIPLES:
- SIMPLE, CLEAN, and EDUCATIONAL — every visual must help the viewer understand ONE concept clearly.
- Do NOT overload the design. Use minimal elements.
- Think like a great teacher: one idea per scene, clear diagrams, readable text.

AVAILABLE VISUAL TEMPLATES:
{templates}

RULES:
1. Each scene should be 2–8 seconds.
2. Merge very short sentences (< 2 s) with adjacent content.
3. Split long segments (> 8 s) at natural sentence/idea boundaries.
4. Each scene gets exactly ONE template type — choose the best fit.
5. Identify 1–3 KEYWORDS per scene that should trigger word-level visual emphasis (glow, highlight, pulse).
6. Write a brief "visual_concept" — describe what to animate so the viewer understands the concept.
7. Provide an "elements" array — the concrete labels, code lines, node names, metric values, etc. the template should display.

OUTPUT FORMAT — return a JSON object:
{{
  "scenes": [
    {{
      "scene_id": "scene_001",
      "text": "narration text for this scene",
      "start": 0.52,
      "end": 3.84,
      "template": "text_reveal",
      "visual_concept": "Words appear one-by-one with emphasis on 'AI' and 'fail'",
      "keywords": ["AI", "fail"],
      "elements": []
    }}
  ]
}}

IMPORTANT:
- Scenes MUST be contiguous — end of scene N == start of scene N+1.
- Scenes MUST cover the ENTIRE narration from first word to last word.
- Prefer smooth, clean transitions — avoid jarring jumps.
"""


def run_segmentation(
    alignment: dict,
    output_path: Path,
    api_key: str,
    model: str = "gpt-4o",
) -> list:
    """
    Segment aligned narration into visual scenes using OpenAI.

    Args:
        alignment:   WhisperX alignment output (dict with "segments").
        output_path: Where to save scenes.json.
        api_key:     OpenAI API key.
        model:       OpenAI model name.

    Returns:
        List of enriched scene dicts.
    """
    from openai import OpenAI

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Please add it to .env or set the environment variable."
        )

    logger.info("Starting LLM-powered scene segmentation...")
    client = OpenAI(api_key=api_key)

    # Format template descriptions for the prompt
    templates_str = "\n".join(
        f"- {t['name']}: {t['description']}" for t in AVAILABLE_TEMPLATES
    )

    # Prepare narration data
    narration_block = _format_narration(alignment)
    total_duration = _total_duration(alignment)
    logger.info(f"Narration duration: {total_duration:.2f}s")

    # ---- Call OpenAI --------------------------------------------------
    logger.info(f"Calling OpenAI {model}...")
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(templates=templates_str),
            },
            {
                "role": "user",
                "content": (
                    f"Here is the narration with word-level timestamps "
                    f"(total duration: {total_duration:.2f}s):\n\n"
                    f"{narration_block}\n\n"
                    f"Divide this into visual scenes. "
                    f"Return a JSON object with a \"scenes\" key."
                ),
            },
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content
    logger.debug(f"LLM raw response:\n{raw}")

    # ---- Parse & validate ---------------------------------------------
    parsed = json.loads(raw)
    scenes_raw = parsed.get("scenes", parsed if isinstance(parsed, list) else [])
    scenes = _validate_and_enrich(scenes_raw, alignment)

    # ---- Save ----------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)

    logger.info(f"Scene segmentation complete → {output_path}")
    for s in scenes:
        logger.info(
            f"  {s['scene_id']}: [{s['start']:.2f}s–{s['end']:.2f}s] "
            f"({s['duration']:.2f}s) template={s['template']}"
        )

    return scenes


# ======================================================================
# Internal helpers
# ======================================================================

def _format_narration(alignment: dict) -> str:
    """
    Format alignment data into a readable block for the LLM.
    Shows segment text + word-level timestamps.
    """
    lines: list[str] = []
    for seg in alignment["segments"]:
        lines.append(
            f"[{seg['start']:.2f}s – {seg['end']:.2f}s] {seg['text']}"
        )
        word_parts = [
            f"{w['word']}({w['start']:.2f}–{w['end']:.2f})"
            for w in seg["words"]
        ]
        lines.append(f"  Words: {' | '.join(word_parts)}")
        lines.append("")
    return "\n".join(lines)


def _total_duration(alignment: dict) -> float:
    segs = alignment.get("segments", [])
    if not segs:
        return 0.0
    return segs[-1]["end"]


def _validate_and_enrich(scenes_raw: list, alignment: dict) -> list:
    """
    Validate scene boundaries, attach word-level timestamps with
    emphasis flags, and ensure all required fields are present.
    """
    # Flatten all words from alignment
    all_words: list[dict] = []
    for seg in alignment["segments"]:
        all_words.extend(seg["words"])

    valid_names = {t["name"] for t in AVAILABLE_TEMPLATES}
    enriched: list[dict] = []

    for idx, raw in enumerate(scenes_raw):
        scene_id = raw.get("scene_id", f"scene_{idx + 1:03d}")
        start = round(float(raw.get("start", 0)), 3)
        end = round(float(raw.get("end", 0)), 3)
        duration = round(end - start, 3)

        # Sanitise template choice
        template = raw.get("template", "text_reveal")
        if template not in valid_names:
            logger.warning(
                f"Scene {scene_id}: unknown template '{template}', "
                f"falling back to 'text_reveal'"
            )
            template = "text_reveal"

        # Collect words within this scene's window (±50 ms tolerance)
        kw_set = {k.lower().strip(".,!?;:'\"") for k in raw.get("keywords", [])}
        scene_words: list[dict] = []
        for w in all_words:
            if w["start"] >= (start - 0.05) and w["end"] <= (end + 0.05):
                word_clean = w["word"].lower().strip(".,!?;:'\"")
                scene_words.append({
                    "word": w["word"],
                    "start": round(w["start"] - start, 3),   # relative
                    "end": round(w["end"] - start, 3),        # relative
                    "abs_start": w["start"],
                    "abs_end": w["end"],
                    "emphasis": word_clean in kw_set,
                })

        enriched.append({
            "scene_id": scene_id,
            "text": raw.get("text", ""),
            "start": start,
            "end": end,
            "duration": duration,
            "template": template,
            "visual_concept": raw.get("visual_concept", ""),
            "keywords": raw.get("keywords", []),
            "elements": raw.get("elements", []),
            "words": scene_words,
        })

    return enriched
