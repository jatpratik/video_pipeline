"""
Design System — Visual Identity & Language Persistence
=========================================================
Hardcoded visual identity rules injected into all agent prompts.
Manages a persistent visual_language.json that maintains
cross-scene consistency for color semantics, motion language,
node styles, typography, and animation personality.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("video_pipeline.agents.design_system")


# ======================================================================
# Core Design System (hardcoded base)
# ======================================================================

DESIGN_SYSTEM = {
    "colors": {
        "background": "#050505",
        "surface": "rgba(255,255,255,0.03)",
        "surface_hover": "rgba(255,255,255,0.06)",
        "border": "rgba(255,255,255,0.08)",
        "border_active": "rgba(255,255,255,0.15)",
        "text_primary": "rgba(255,255,255,0.92)",
        "text_secondary": "#94a3b8",
        "text_muted": "#475569",
        "accent_positive": "#10b981",     # success, correct, good output
        "accent_negative": "#ef4444",     # error, failure, wrong, break
        "accent_info": "#3b82f6",         # AI, data, process, system
        "accent_warning": "#f59e0b",      # caution, attention, hidden
        "accent_highlight": "#c084fc",    # emphasis, keywords, special
        "accent_neutral": "#64748b",      # secondary, supporting
    },
    "color_semantics": {
        "ai_reasoning": "#3b82f6",
        "data_flow": "#3b82f6",
        "success_output": "#10b981",
        "error_failure": "#ef4444",
        "keyword_emphasis": "#c084fc",
        "warning_attention": "#f59e0b",
        "process_node": "rgba(59,130,246,0.1)",
        "connection_line": "rgba(255,255,255,0.06)",
        "glow_positive": "rgba(16,185,129,0.3)",
        "glow_negative": "rgba(239,68,68,0.3)",
        "glow_info": "rgba(59,130,246,0.3)",
    },
    "typography": {
        "primary_font": "Inter",
        "code_font": "JetBrains Mono",
        "font_import_url": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap",
        "heading_weight": 800,
        "heading_size": "46px",
        "subheading_size": "28px",
        "body_size": "22px",
        "label_size": "16px",
        "code_size": "17px",
        "line_height": 1.55,
    },
    "motion": {
        "gsap_cdn": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js",
        "gsap_text_cdn": "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/TextPlugin.min.js",
        "default_ease": "power2.out",
        "emphasis_ease": "back.out(1.8)",
        "enter_ease": "power2.out",
        "exit_ease": "power2.in",
        "reveal_duration": 0.12,
        "emphasis_duration": 0.18,
        "transition_duration": 0.4,
        "max_simultaneous_animations": 3,
        "max_elements_on_screen": 7,
    },
    "layout": {
        "width": 1080,
        "height": 1056,
        "content_padding": 60,
        "content_width": 960,
        "content_height": 936,
        "safe_area": {"top": 60, "right": 60, "bottom": 60, "left": 60},
        "node_border_radius": "16px",
        "card_border_radius": "14px",
    },
    "composition": {
        "max_elements_on_screen": 6,
        "max_primary_focus": 1,
        "max_secondary_focus": 2,
        "primary_focus_min_percent": 35,
        "primary_focus_max_percent": 60,
        "screen_utilization_min_percent": 55,
        "negative_space_min_percent": 20,
        "negative_space_max_percent": 40,
        "depth_layers": ["background", "midground", "foreground", "fx"],
    },
    "effects": {
        "grid_opacity": 0.015,
        "grid_size": "60px",
        "glow_blur": "80px",
        "shadow_large": "0 20px 60px rgba(0,0,0,0.6)",
        "shadow_subtle": "0 4px 20px rgba(0,0,0,0.3)",
    },
}


# ======================================================================
# Visual Language Persistence
# ======================================================================

def load_visual_language(path: Path) -> dict:
    """
    Load the persistent visual language from visual_language.json.
    Returns default structure if file doesn't exist.
    """
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"  Loaded visual language from {path}")
            return data
        except Exception as e:
            logger.warning(f"  Failed to load visual language: {e}")

    return _default_visual_language()


def save_visual_language(data: dict, path: Path) -> None:
    """Save the visual language state for cross-scene consistency."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved visual language to {path}")


def _default_visual_language() -> dict:
    """Default visual language structure."""
    return {
        "concept_colors": {},
        "node_styles": {},
        "established_metaphors": [],
        "animation_personality": {
            "energy_level": "calm",
            "transition_style": "smooth_fade",
            "emphasis_style": "subtle_glow",
        },
        "scene_history": [],
    }


def update_visual_language(
    visual_language: dict,
    scene: dict,
) -> dict:
    """
    Update visual language after a scene is generated.
    Maintains consistency by recording what visual choices were made.
    """
    scene_entry = {
        "scene_id": scene.get("scene_id", ""),
        "visual_approach": scene.get("visual_approach", ""),
        "color_intent": scene.get("color_intent", {}),
        "importance": scene.get("importance", 0.5),
    }

    # Record concept → color mappings
    color_intent = scene.get("color_intent", {})
    if isinstance(color_intent, dict):
        for concept, color in color_intent.items():
            visual_language["concept_colors"][concept] = color

    # Record metaphors used
    metaphor = scene.get("visual_metaphor", "")
    if metaphor and metaphor not in visual_language["established_metaphors"]:
        visual_language["established_metaphors"].append(metaphor)

    visual_language["scene_history"].append(scene_entry)
    return visual_language


# ======================================================================
# Prompt Helpers
# ======================================================================

def get_design_system_prompt() -> str:
    """
    Format the design system as a prompt section for agents.
    """
    return f"""
DESIGN SYSTEM (MANDATORY RULES):

ANTIGRAVITY AESTHETIC DIRECTIVE (CRITICAL):
- Use Rich Aesthetics: The user must be WOWED at first glance. Use vibrant colors, sleek dark modes, glassmorphism, and dynamic animations.
- Prioritize Visual Excellence: Avoid generic colors. Use modern typography. Add micro-animations.
- Use a Dynamic Design: The interface must feel alive. Use glowing pulses and dynamic data flows.
- Never use placeholders. Every technical concept must have a concrete, premium visual representation.

DIMENSIONS:
- Canvas: {DESIGN_SYSTEM['layout']['width']}px × {DESIGN_SYSTEM['layout']['height']}px
- Content area: {DESIGN_SYSTEM['layout']['content_width']}px centered
- Padding: {DESIGN_SYSTEM['layout']['content_padding']}px

COLORS (use EXACTLY these):
- Background: {DESIGN_SYSTEM['colors']['background']}
- Surface: {DESIGN_SYSTEM['colors']['surface']}
- Border: {DESIGN_SYSTEM['colors']['border']}
- Text primary: {DESIGN_SYSTEM['colors']['text_primary']}
- Text secondary: {DESIGN_SYSTEM['colors']['text_secondary']}
- Positive/success: {DESIGN_SYSTEM['colors']['accent_positive']}
- Negative/error: {DESIGN_SYSTEM['colors']['accent_negative']}
- Info/AI/data: {DESIGN_SYSTEM['colors']['accent_info']}
- Warning/attention: {DESIGN_SYSTEM['colors']['accent_warning']}
- Keyword emphasis: {DESIGN_SYSTEM['colors']['accent_highlight']}

COLOR SEMANTICS (maintain across all scenes):
- Blue (#3b82f6) = AI reasoning, data processing, systems
- Green (#10b981) = success, correct output, positive results
- Red (#ef4444) = failure, errors, breaking, problems
- Purple (#c084fc) = emphasis, keywords, special highlights
- Amber (#f59e0b) = caution, hidden issues, attention needed

TYPOGRAPHY:
- Primary font: '{DESIGN_SYSTEM['typography']['primary_font']}'
- Code font: '{DESIGN_SYSTEM['typography']['code_font']}'
- Heading: {DESIGN_SYSTEM['typography']['heading_size']} weight {DESIGN_SYSTEM['typography']['heading_weight']}
- Body: {DESIGN_SYSTEM['typography']['body_size']}
- Line height: {DESIGN_SYSTEM['typography']['line_height']}

MOTION RULES:
- Default ease: '{DESIGN_SYSTEM['motion']['default_ease']}'
- Emphasis ease: '{DESIGN_SYSTEM['motion']['emphasis_ease']}'
- Max {DESIGN_SYSTEM['motion']['max_simultaneous_animations']} simultaneous animations
- Max {DESIGN_SYSTEM['motion']['max_elements_on_screen']} elements on screen at once
- All timing MUST be driven by GSAP timeline, NOT CSS animation-duration

REQUIRED CDN LINKS:
- GSAP: {DESIGN_SYSTEM['motion']['gsap_cdn']}
- Google Fonts: {DESIGN_SYSTEM['typography']['font_import_url']}

COMPLEXITY BUDGET (per scene — MANDATORY):
- Max 1 core teaching idea
- Max 2 major visual objects on screen
- Max 8 visible words on screen at any time
- Max 3 simultaneous motions
- All important content MUST be inside the top 55% of 1080×1920 (the canvas)
- After all animations complete, scene MUST stabilise (no loops, no ambient drift)
- Motion MUST explain; if static works better, do NOT animate
"""


def get_visual_language_prompt(visual_language: dict) -> str:
    """
    Format the current visual language state for agent context.
    """
    if not visual_language.get("scene_history"):
        return "\nVISUAL LANGUAGE: No previous scenes. You are defining the visual identity."

    parts = ["\nVISUAL LANGUAGE (maintain consistency with previous scenes):"]

    if visual_language.get("concept_colors"):
        parts.append("Established concept→color mappings:")
        for concept, color in visual_language["concept_colors"].items():
            parts.append(f"  - {concept} → {color}")

    if visual_language.get("established_metaphors"):
        parts.append(
            f"Established metaphors: {', '.join(visual_language['established_metaphors'])}"
        )

    personality = visual_language.get("animation_personality", {})
    if personality:
        parts.append(
            f"Animation personality: energy={personality.get('energy_level', 'calm')}, "
            f"transitions={personality.get('transition_style', 'smooth')}, "
            f"emphasis={personality.get('emphasis_style', 'subtle')}"
        )

    prev = visual_language.get("scene_history", [])
    if prev:
        parts.append(f"Previous scenes ({len(prev)}):")
        for s in prev[-3:]:
            parts.append(
                f"  - {s.get('scene_id', '?')}: {s.get('visual_approach', '?')} "
                f"(importance: {s.get('importance', 0.5):.1f})"
            )

    return "\n".join(parts)
