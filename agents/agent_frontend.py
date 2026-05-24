"""
Agent — Frontend Renderer (Educational Explainer)
=========================================================
Renders layout zones + animation choreography into HTML/CSS/GSAP.
Prioritizes visual stability, extreme readability, and mobile-first sizing.
"""

import json
import logging
import re
from .llm_client import call_llm
from .design_system import get_design_system_prompt, DESIGN_SYSTEM
from .visual_patterns import PEDAGOGICAL_MOTION

logger = logging.getLogger("video_pipeline.agents.frontend")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{font_url}" rel="stylesheet">
    <script src="{gsap_cdn}"></script>
    <script src="{gsap_text_cdn}"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{
            width: 1080px;
            height: 1056px;
            overflow: hidden;
            background: #050505;
            font-family: 'Inter', sans-serif;
            color: rgba(255,255,255,0.92);
            position: relative;
        }}
        .bg {{
            position: absolute;
            inset: 0;
            background: #050505; /* Clean dark background, no distracting gradients */
        }}
        .grid-bg {{
            position: absolute;
            inset: 0;
            background-image:
                linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
            background-size: 80px 80px;
            opacity: 0;
        }}
        .educational-canvas {{
            width: 1080px;
            height: 1056px;
            position: absolute;
            top: 0;
            left: 0;
            overflow: hidden; /* Prevents anything from bleeding out */
            box-sizing: border-box; /* Ensures padding doesn't distort boundaries */
            background: #000000;
        }}
        /* Flat Layer System */
        .depth-background {{ position: absolute; inset: 0; z-index: 0; pointer-events: none; }}
        .depth-midground {{ position: absolute; inset: 0; z-index: 10; }}
        .depth-foreground {{ position: absolute; inset: 0; z-index: 20; }}
        .depth-fx {{ position: absolute; inset: 0; z-index: 30; pointer-events: none; }}
        /* Zone containers — positioned by layout engine */
{zone_css}
{custom_css}
    </style>
</head>
<body>
    <div class="bg"></div>
    <div class="grid-bg" id="grid"></div>
    <div class="educational-canvas">
        <div class="depth-background" id="layer-bg">
{bg_html}
        </div>
        <div class="depth-midground" id="layer-mid">
{zone_html}
        </div>
        <div class="depth-foreground" id="layer-fg">
{fg_html}
        </div>
        <div class="depth-fx" id="layer-fx">
{fx_html}
        </div>
    </div>
    <script>
        const S = {scene_data};
        const LAYOUT = {layout_data};

        document.fonts.ready.then(() => {{
            const tl = gsap.timeline({{
                onComplete: () => {{ document.title = 'DONE'; }}
            }});

            // Subtle grid fade
            tl.to('#grid', {{ opacity: 0.5, duration: 0.3 }}, 0);

{custom_js}

            // Cap timeline at exact scene duration
            tl.to({{}}, {{ duration: 0.001 }}, S.duration - 0.001);
        }});
    </script>
</body>
</html>"""


SYSTEM_PROMPT = """You are an EDUCATIONAL FRONTEND RENDERER for vertical YouTube Shorts.

You translate choreography scores into executable HTML/CSS/GSAP code.
Your job is to IMPLEMENT with technical precision to ensure 1-second comprehension on a mobile device.

{design_system}

WHAT YOU RECEIVE (already decided — do NOT override):
1. LAYOUT ZONES — pixel-precise zone containers already positioned in CSS
2. CHOREOGRAPHY — what elements, animations, timing
3. TEMPORAL BEATS — when things happen
4. STATE PROGRESSION — how the scene transforms

THE PRE-BUILT SHELL PROVIDES:
- Full HTML document (1080×1056 canvas). This represents the TOP 55% of the YouTube Short.
- GSAP CDN, Google Fonts (Inter, JetBrains Mono)
- Solid dark background (#050505)
- Grid overlay (.grid-bg with id="grid")
- FOUR flat layer containers: #layer-bg, #layer-mid, #layer-fg, #layer-fx
- Zone containers (with content already populated) positioned inside #layer-mid
- const S = <scene_data>, const LAYOUT = <layout_data>
- GSAP timeline `tl` already created

IMPORTANT — HOW THE TEMPLATE WORKS:
Zone containers like #zone_main, #zone_pipeline etc. are ALREADY created by the template.
Your "zone_content" output puts HTML INSIDE those containers — DO NOT recreate them.

YOU MUST RETURN a JSON object with these keys:
{{
  "planning_thought": "Briefly describe how you will apply the Antigravity Aesthetic Directive (glassmorphism, glows, camera shakes, gradients) to this scene to create a WOW factor.",
  "css": "Custom CSS rules (NO <style> tags). Style your elements here.",
  "zone_content": {{
    "zone_main": "<div id='node1' class='node'>Label</div>"
  }},
  "bg_html": "HTML for background layer (connection lines)",
  "fg_html": "HTML for foreground layer",
  "fx_html": "HTML for fx layer (highlights)",
  "js": "GSAP timeline code (use existing `tl` variable)"
}}

CRITICAL RENDERING RULES (MANDATORY):

1. MASSIVE TYPOGRAPHY (MOBILE FIRST)
   - Minimum font-size for any text: 32px
   - Normal body/labels: 40px - 48px
   - Hero/Key phrases: 64px - 80px+
   - font-weight: 600 or 800 (no thin fonts)
   - color: rgba(255,255,255,0.95) for primary text

2. CONCRETE TECH COMPONENT VOCABULARY (NO BLANK RECTANGLES)
   Never represent an abstract technical concept with a blank rectangle. Build a concrete visual representation using clean CSS/SVG layout structures.
   - JSON/Code: A dark code block container containing styled colored braces {{ }} and mock property lines.
   - Email: An envelope icon layout constructed with a sharp triangle overlay on top of a rectangular card.
   - Report/Doc: A page layout container with a bold header line and 3 horizontal text-mock line strips.
   - AI Model/LLM: A central circular hub with 4 radiating node connection lines.

3. PREMIUM VISUAL EFFECTS (THE "WOW" FACTOR)
   - You MUST use GSAP TextPlugin for typing effects! `gsap.registerPlugin(TextPlugin); tl.to('#element', {{duration: 2, text: "typing..."}})`
   - Use Heavy Glows: e.g. `box-shadow: 0 12px 64px rgba(239, 68, 68, 0.5)` for danger or `rgba(16, 185, 129, 0.5)` for success.
   - Use Text Gradients: `background: linear-gradient(90deg, #60a5fa, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;`
   - Use Glassmorphism: `backdrop-filter: blur(20px); background: rgba(255,255,255,0.03);`
   - For errors/overloads, use GSAP Camera Shake: `tl.to(".node", {{x: "random(-8, 8, 5)", duration: 0.05, repeat: 20, yoyo: true}})`
   - Create complex SVG pipelines with glowing paths using `stroke-dasharray` and `stroke-dashoffset`.

4. NO CINEMATIC CAMERA MOVEMENT
   - The camera is STATIC. Do not scale or translate the `.educational-canvas`.
   - Ensure elements do not extend past the 1080x1056 boundary.

4. EXACT SYNC WITH SPOKEN WORDS
   - Use `w.start` (relative to scene).
   - Animations MUST align with `w.start` of the relevant word.

5. FAST, STABLE ANIMATIONS
   - Animations should complete quickly (0.2s - 0.4s).
   - Once an animation finishes, the scene MUST remain completely stable.
   - NO ambient floating, shaking, or drifting in the background.

6. NO CSS ANIMATIONS
   - Use GSAP exclusively. No @keyframes.

7. ABSOLUTE TIMESTAMPS BANNED
   - NEVER use absolute timestamps. All `w.start` values are RELATIVE to scene start (0.0).
   - Do NOT add scene.start to word timestamps.

8. STATIC REST STATE (MANDATORY)
   - After ALL animations complete, the scene MUST remain visually stable.
   - No looping animations. No ambient floating. No continuous motion.
   - The last frame must be a clean, readable static state.
   - NEVER use `repeat: -1`, `yoyo: true` without a finite count, or infinite CSS loops.
"""


def generate_scene_html(
    scene: dict,
    layout: dict,
    choreography: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.2,
    critic_feedback: str | None = None,
) -> str:
    """Generate production-ready HTML/CSS/GSAP for a single scene."""
    scene_id = scene["scene_id"]
    logger.info(f"  Agent (Frontend): Rendering {scene_id}…")

    system = SYSTEM_PROMPT.format(
        design_system=get_design_system_prompt(),
    )

    scene_data = {
        "scene_id": scene["scene_id"],
        "text": scene["text"],
        "duration": scene["duration"],
        "importance": scene.get("importance", 0.5),
        "keywords": scene.get("keywords", []),
        "elements": scene.get("elements", []),
        "words": scene.get("words", []),
    }

    storyboard = scene.get("storyboard", {})
    zone_ids = [z.get("id", "zone_unknown") for z in layout.get("zones", [])]

    user_prompt = f"""Render this educational scene:

SCENE (duration: {scene['duration']:.3f}s):
{json.dumps(scene_data, indent=2)}

LAYOUT ZONES (populate these with content):
Zone IDs available: {json.dumps(zone_ids)}
Full layout: {json.dumps(layout, indent=2)}

CHOREOGRAPHY:
{json.dumps(choreography, indent=2)}

STORYBOARD:
Core Idea: {storyboard.get('core_visual', 'N/A')}
Takeaway: {storyboard.get('viewer_takeaway', 'N/A')}

RESPOND WITH JSON containing:
- "planning_thought": reasoning on how to apply the WOW aesthetics
- "css": custom CSS rules
- "zone_content": dict mapping zone_id → inner HTML for that zone
- "bg_html": background layer HTML
- "fg_html": foreground layer HTML
- "fx_html": fx layer HTML  
- "js": GSAP timeline code

REMINDERS:
- Texts MUST be massive (32px absolute minimum, 48px+ preferred).
- Keep animations fast and stable. No camera movement.
- Use `w.start` for sync.
- zone_content goes INSIDE existing containers."""

    if critic_feedback:
        user_prompt += f"""

CRITIC REJECTED previous version. Fix these issues:
{critic_feedback}"""
        logger.info(f"    Including critic feedback for regeneration")

    result = call_llm(
        system_prompt=system,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=6000,
        json_mode=True,
        agent_name="Frontend",
    )

    custom_css = result.get("css", "")
    zone_content = result.get("zone_content", {})
    bg_html = result.get("bg_html", "")
    fg_html = result.get("fg_html", "")
    fx_html = result.get("fx_html", "")
    custom_js = result.get("js", "")

    # We now allow backdrop-filter and camera shake (using GSAP random) 
    # to enable premium glassmorphism and glitch/shake effects.
    pass



    zone_css = _build_zone_css(layout)
    zone_html = _build_zone_html(layout, zone_content)

    html = _assemble_html(
        scene_data, layout,
        zone_css, zone_html,
        custom_css, bg_html, fg_html, fx_html, custom_js,
    )

    logger.info(f"    Generated {len(html)} chars of HTML")
    return html


def _build_zone_css(layout: dict) -> str:
    lines = []
    zones = layout.get("zones", [])
    for zone in zones:
        zone_id = zone.get("id", "zone_unknown")
        bounds = zone.get("bounds", {})
        x = bounds.get("x", 60)
        y = bounds.get("y", 60)
        w = bounds.get("width", 400)
        h = bounds.get("height", 300)
        layout_mode = zone.get("layout_mode", "flex_column")

        display = "flex"
        flex_dir = "column"
        if layout_mode == "flex_row":
            flex_dir = "row"
        elif layout_mode == "grid":
            display = "grid"
            flex_dir = ""

        spacing = zone.get("spacing", 16)

        css = f"""        #{zone_id} {{
            position: absolute;
            left: {x}px;
            top: {y}px;
            width: {w}px;
            height: {h}px;
            display: {display};
            {'flex-direction: ' + flex_dir + ';' if display == 'flex' else ''}
            align-items: center;
            justify-content: center;
            gap: {spacing}px;
            overflow: hidden;
        }}"""
        lines.append(css)

    return "\n".join(lines)


def _build_zone_html(layout: dict, zone_content: dict) -> str:
    lines = []
    zones = layout.get("zones", [])
    for zone in zones:
        zone_id = zone.get("id", "zone_unknown")
        inner = zone_content.get(zone_id, "")
        if inner:
            lines.append(f'            <div id="{zone_id}">')
            for line in inner.strip().split("\n"):
                lines.append(f'                {line}')
            lines.append(f'            </div>')
        else:
            lines.append(f'            <div id="{zone_id}"></div>')
    return "\n".join(lines)


def _assemble_html(
    scene_data: dict, layout: dict, zone_css: str, zone_html: str,
    custom_css: str, bg_html: str, fg_html: str, fx_html: str, custom_js: str,
) -> str:
    css_lines = custom_css.strip().split("\n") if custom_css.strip() else [""]
    indented_css = "\n".join(f"        {line}" for line in css_lines)

    bg_lines = bg_html.strip().split("\n") if bg_html.strip() else [""]
    indented_bg = "\n".join(f"            {line}" for line in bg_lines)

    fg_lines = fg_html.strip().split("\n") if fg_html.strip() else [""]
    indented_fg = "\n".join(f"            {line}" for line in fg_lines)

    fx_lines = fx_html.strip().split("\n") if fx_html.strip() else [""]
    indented_fx = "\n".join(f"            {line}" for line in fx_lines)

    js_lines = custom_js.strip().split("\n") if custom_js.strip() else [""]
    indented_js = "\n".join(f"            {line}" for line in js_lines)

    scene_data_json = json.dumps(scene_data, ensure_ascii=False)
    layout_data_json = json.dumps(layout, ensure_ascii=False)

    html = HTML_TEMPLATE.format(
        font_url=DESIGN_SYSTEM["typography"]["font_import_url"],
        gsap_cdn=DESIGN_SYSTEM["motion"]["gsap_cdn"],
        gsap_text_cdn=DESIGN_SYSTEM["motion"]["gsap_text_cdn"],
        zone_css=zone_css,
        zone_html=zone_html,
        custom_css=indented_css,
        bg_html=indented_bg,
        fg_html=indented_fg,
        fx_html=indented_fx,
        custom_js=indented_js,
        scene_data=scene_data_json,
        layout_data=layout_data_json,
    )

    return html
