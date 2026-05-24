"""
Agent — Critic / Review Agent (Educational Comprehension Evaluator)
=============================================================
Reviews generated HTML scenes with strict focus on instant comprehension,
mobile readability, and educational clarity. Cinematic quality is completely ignored.
"""

import json
import logging
import re
from .llm_client import call_llm

logger = logging.getLogger("video_pipeline.agents.critic")

SYSTEM_PROMPT = """You are an EDUCATIONAL COMPREHENSION EVALUATOR for YouTube Shorts.

You are the final gatekeeper. Your ONLY objective is:
"Can a mobile viewer understand the spoken sentence within 1 second without cognitive overload?"

IMPORTANT CONTEXT:
The code is injected into a guaranteed HTML shell that provides:
- 1080x960 canvas dimensions (This is the TOP 50% safe area for a vertical Short)
- Dark background (#050505)
- Pre-positioned zone containers
- GSAP timeline with duration cap

REVIEW FRAMEWORK (evaluate ALL of these):

1. 1-SECOND COMPREHENSION TEST (MANDATORY)
   - REJECT if the viewer needs more than 1 second to interpret the visuals.
   - REJECT if the visuals require complex reading or eye movement.

2. MOBILE READABILITY
   - REJECT if any text font-size is below 32px (48px+ is preferred).
   - REJECT if important elements are cut off or placed at the absolute edges.
   - Check: Are the objects and text MASSIVE and easy to see on a phone?

3. CLARITY OF CORE IDEA
   - REJECT if the scene tries to teach more than ONE concept.
   - REJECT if the visual metaphor is confusing or abstract (e.g. floating generic nodes).

4. COGNITIVE LOAD & SIMPLICITY
   - REJECT if there are unnecessary decorative elements, gradients, or borders.
   - REJECT if there are more than 1-2 major focal points.
   - REJECT if there is continuous background animation or ambient "drifting".
   - Ask: "Would removing any object improve clarity?" If YES, REJECT.

5. NARRATION SYNC ACCURACY & TIMING PRECISION
   - REJECT if visual transformations do not align exactly with spoken keywords.
   - Check: Is `w.start` being used correctly for emphasis timing?
   - REJECT if the animation takes too long to complete.

6. VISUAL FOCUS & HIERARCHY
   - REJECT if it's unclear what the user should look at first.
   - Check: Is the primary object centered or positioned dominantly?

7. EDUCATIONAL EFFECTIVENESS
   - REJECT if the visual is just text on screen without any structural or metaphorical value.
   - Check: Does the visual actually help explain the spoken sentence?

SCORING RUBRIC:
You must score the following 10 metrics from 0.0 to 1.0:
1. clarity_of_core_idea
2. mobile_readability
3. narration_sync_accuracy
4. cognitive_load (higher is better meaning less cognitive load)
5. visual_focus
6. educational_effectiveness
7. simplicity
8. timing_precision
9. visual_hierarchy
10. viewer_comprehension_speed

REJECTION THRESHOLD: overall < 0.70 → REJECT.

Return a JSON object:
{{
  "approved": true or false,
  "scores": {{
    "clarity_of_core_idea": 0.0 to 1.0,
    "mobile_readability": 0.0 to 1.0,
    "narration_sync_accuracy": 0.0 to 1.0,
    "cognitive_load": 0.0 to 1.0,
    "visual_focus": 0.0 to 1.0,
    "educational_effectiveness": 0.0 to 1.0,
    "simplicity": 0.0 to 1.0,
    "timing_precision": 0.0 to 1.0,
    "visual_hierarchy": 0.0 to 1.0,
    "viewer_comprehension_speed": 0.0 to 1.0,
    "overall": 0.0 to 1.0
  }},
  "strengths": [
    "what works well — be specific"
  ],
  "issues": [
    "specific problems found — reference exact CSS/GSAP issues"
  ],
  "suggestions": [
    "concrete, actionable improvement instructions"
  ]
}}
"""


def review_scene(
    scene: dict,
    html_code: str,
    layout: dict,
    choreography: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
) -> dict:
    """
    Review a generated HTML scene with strict educational clarity standards.
    """
    scene_id = scene["scene_id"]
    logger.info(f"  Agent (Critic): Reviewing {scene_id}…")

    scene_context = {
        "scene_id": scene["scene_id"],
        "text": scene["text"],
        "duration": scene["duration"],
        "importance": scene.get("importance", 0.5),
        "visual_approach": scene.get("visual_approach", ""),
        "visual_concept": scene.get("visual_concept", ""),
        "keywords": scene.get("keywords", []),
        "storyboard": scene.get("storyboard", {}),
    }

    # Truncate HTML for the prompt if extremely long
    html_for_review = html_code
    if len(html_code) > 12000:
        html_for_review = html_code[:12000] + "\n... [truncated]"

    # Build choreography summary for context
    beats_count = len(choreography.get("beats", []))
    energy = choreography.get("motion_energy", "unknown")

    user_prompt = f"""Review this generated HTML animation scene for EDUCATIONAL CLARITY:

SCENE CONTEXT:
{json.dumps(scene_context, indent=2)}

EXPECTED FROM CHOREOGRAPHY:
- Motion energy: {energy}
- Temporal beats: {beats_count} beats defined

LAYOUT ZONES:
{json.dumps(layout, indent=2)}

GENERATED HTML CODE:
{html_for_review}

REVIEW CHECKLIST (evaluate each point):
1. 1-SECOND COMPREHENSION: Is this immediately understandable?
2. MOBILE READABILITY: Are texts massive (32px+)? Are objects large and central?
3. COGNITIVE LOAD: Are there unnecessary background elements or decorations?
4. CAMERA: Did they accidentally use camera drift or scale? (MUST BE REJECTED IF YES)
5. EDUCATIONAL VALUE: Does the transformation directly teach the spoken sentence?
6. SYNC: Do animations trigger on `w.start` timestamps correctly?

Score each dimension honestly. Reject if overall < 0.70.

Return your review as a JSON object."""

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2048,
        json_mode=True,
        agent_name="Critic",
    )

    approved = result.get("approved", True)
    overall = result.get("scores", {}).get("overall", 0)

    # Hard override: reject if overall < 0.70
    if overall < 0.70 and approved:
        result["approved"] = False
        result["issues"] = result.get("issues", [])
        result["issues"].append(f"Auto-rejected: overall score {overall:.2f} < 0.70 threshold")
        approved = False

    # Hard programmatic checks
    hard_issues = _hard_check(html_code)
    if hard_issues:
        result["approved"] = False
        result["issues"] = result.get("issues", []) + hard_issues
        result["suggestions"] = result.get("suggestions", [])
        result["suggestions"].append(
            "Fix the hard-check failures above. These are strict rendering rules."
        )
        approved = False
        logger.warning(f"    ⚠ Hard-check found {len(hard_issues)} issue(s)")

    if result.get("approved", False):
        logger.info(
            f"    ✓ APPROVED (overall: {overall:.2f})"
        )
    else:
        issues = result.get("issues", [])
        logger.warning(
            f"    ✗ REJECTED (overall: {overall:.2f}) — "
            f"{len(issues)} issue(s)"
        )
        for issue in issues[:3]:
            logger.warning(f"      • {issue}")

    return result


def _hard_check(html_code: str) -> list[str]:
    """
    Programmatic checks for known rendering bugs and educational constraints.
    """
    issues = []

    # Check for backdrop-filter
    if re.search(r'backdrop-filter\s*:', html_code):
        issues.append(
            "BANNED: backdrop-filter found in CSS. Causes unreadable text. "
            "Use solid backgrounds."
        )

    # Check for scale on .canvas
    if re.search(r"['\"]\.canvas['\"].*scale", html_code):
        issues.append(
            "BANNED: scale transform on .canvas found. "
            "Camera scaling is banned to prevent white overflow."
        )



    # Check for CSS @keyframes
    if re.search(r'@keyframes\s', html_code):
        issues.append(
            "BANNED: CSS @keyframes animation found. Use GSAP."
        )

    # Check for tiny font sizes (< 32px is banned for Shorts)
    small_fonts = re.findall(r'font-size\s*:\s*(\d+)px', html_code)
    for size_str in small_fonts:
        if int(size_str) < 32:
            issues.append(
                f"BUG: font-size: {size_str}px is too small for YouTube Shorts. "
                f"Minimum font-size is 32px. Preferred is 48px+."
            )
            break

    # Check for overflow: visible (must be hidden on canvas)
    if re.search(r'overflow\s*:\s*visible', html_code):
        issues.append(
            "BANNED: overflow: visible found. All containers must use "
            "overflow: hidden to prevent content bleeding outside the canvas."
        )

    # Check for elements positioned outside 1080×1056 bounds
    large_positions = re.findall(r'(?:left|top)\s*:\s*(\d+)px', html_code)
    for pos_str in large_positions:
        pos = int(pos_str)
        if pos > 1056:
            issues.append(
                f"BUG: Element positioned at {pos}px exceeds the 1080×1056 "
                f"canvas boundary. All content must stay within bounds."
            )
            break

    # Check for infinite animation loops
    if re.search(r'repeat\s*:\s*-1', html_code):
        issues.append(
            "BANNED: repeat: -1 (infinite loop) found. All animations must "
            "have a finite duration. Scene must stabilise after animation."
        )
    if re.search(r'yoyo\s*:\s*true', html_code) and not re.search(r'repeat\s*:\s*[0-9]', html_code):
        issues.append(
            "BANNED: yoyo: true without finite repeat count. Animations must "
            "end and the scene must reach a stable rest state."
        )

    return issues


def format_feedback_for_retry(review: dict) -> str:
    """
    Format critic review into actionable feedback for regeneration.
    """
    parts = []

    issues = review.get("issues", [])
    if issues:
        parts.append("ISSUES TO FIX (these caused rejection):")
        for i, issue in enumerate(issues, 1):
            parts.append(f"  {i}. {issue}")

    suggestions = review.get("suggestions", [])
    if suggestions:
        parts.append("\nIMPROVEMENT INSTRUCTIONS:")
        for i, sug in enumerate(suggestions, 1):
            parts.append(f"  {i}. {sug}")

    scores = review.get("scores", {})
    weak_areas = [
        (k, v) for k, v in scores.items()
        if isinstance(v, (int, float)) and v < 0.70 and k != "overall"
    ]
    if weak_areas:
        parts.append("\nWEAK EDUCATIONAL METRICS (score < 0.70 — fix these):")
        for area, score in weak_areas:
            parts.append(f"  - {area}: {score:.2f}")

    return "\n".join(parts) if parts else "Educational clarity improvement needed."
