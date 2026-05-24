"""
Educational Visual Intelligence Patterns
=============================================
Reusable visual composition patterns focused strictly on:
1. One core idea per scene
2. Large mobile-readable elements (Top 55% safe area)
3. Instant educational comprehensibility

The Storyboard Agent SELECTS from these instead of inventing
primitive shapes from scratch. No cinematic complexity allowed.
"""

# ======================================================================
# Educational Shot Types
# ======================================================================

EDUCATIONAL_SHOTS = {
    "hero_focus": {
        "name": "Hero Focus",
        "description": "Single dominant element centered in top 55% area. Everything else is contextual.",
        "layout_strategy": "One massive element, perfectly readable. Minimal contextual labels.",
        "motion": "Simple fade-in or scale-in. No ambient drift.",
    },
    "split_comparison": {
        "name": "Split Comparison",
        "description": "Two panels side-by-side or top/bottom showing before/after or good/bad.",
        "layout_strategy": "Canvas divided cleanly in the safe area. High contrast between sides.",
        "motion": "Panels appear sequentially. Left then Right.",
    },
    "progressive_reveal": {
        "name": "Progressive Reveal",
        "description": "Elements appear one-by-one synchronized with narration keywords.",
        "layout_strategy": "Vertical stack or clean grid in the safe area.",
        "motion": "Fade-in one at a time. Previous items remain stable.",
    },
    "highlight_focus": {
        "name": "Highlight Focus",
        "description": "Specific part of an existing diagram/text is highlighted.",
        "layout_strategy": "Existing layout remains identical.",
        "motion": "Yellow highlight or glow appears instantly on target keyword/element.",
    },
    "step_flow": {
        "name": "Step Flow",
        "description": "Simple pipeline or process steps.",
        "layout_strategy": "3-4 large connected nodes.",
        "motion": "Nodes and arrows appear strictly sequentially.",
    },
    "transform_state": {
        "name": "Transform State",
        "description": "Input visually morphs or transforms into output.",
        "layout_strategy": "Input -> Arrow -> Output.",
        "motion": "Direct morph or fade transition. Must explain the 'why'.",
    }
}

# ======================================================================
# Educational Visual Patterns
# ======================================================================

EDUCATIONAL_VISUAL_PATTERNS = {
    "progressive_reveal": {
        "name": "Progressive Reveal",
        "description": "Elements appear one-by-one synchronized with narration.",
        "teaches": "Building understanding, introducing components.",
        "element_structure": {
            "items": "3-4 extremely large labeled items",
            "emphasis": "Current item highlighted"
        },
        "recommended_shots": ["progressive_reveal"],
    },
    "comparison_split": {
        "name": "Comparison Split",
        "description": "Side-by-side or before/after comparison.",
        "teaches": "Good vs bad, old vs new, wrong vs right.",
        "element_structure": {
            "left_panel": "First approach (red accent)",
            "right_panel": "Second approach (green accent)",
            "divider": "Clean dividing line"
        },
        "recommended_shots": ["split_comparison"],
    },
    "highlight_focus": {
        "name": "Highlight Focus",
        "description": "Drawing strict attention to one element.",
        "teaches": "Importance, focus area, errors.",
        "element_structure": {
            "target": "Element to be highlighted",
            "context": "Dimmed surrounding elements"
        },
        "recommended_shots": ["highlight_focus"],
    },
    "process_pipeline": {
        "name": "Process Pipeline",
        "description": "Sequential chain of processing nodes.",
        "teaches": "Workflows, data pipelines.",
        "element_structure": {
            "nodes": "Large labeled boxes",
            "connections": "Thick directional arrows"
        },
        "recommended_shots": ["step_flow"],
    },
    "transform_state": {
        "name": "Transform State",
        "description": "Input element visually morphs/transforms into output element.",
        "teaches": "Data transformation, conversion.",
        "element_structure": {
            "input": "Source element",
            "process": "Transformation arrow",
            "output": "Result element"
        },
        "recommended_shots": ["transform_state"],
    },
    "keyword_emphasis": {
        "name": "Keyword Emphasis",
        "description": "Massive typography representing the core concept.",
        "teaches": "Key terms, takeaways.",
        "element_structure": {
            "text": "Giant single word or short phrase",
            "supporting": "Small subtitle"
        },
        "recommended_shots": ["hero_focus"],
    }
}

# ======================================================================
# Pedagogical Motion Behaviors
# ======================================================================

PEDAGOGICAL_MOTION = {
    "fade_in": {
        "description": "Element simply fades in cleanly.",
        "gsap_hint": "tl.from(el, {opacity: 0, duration: 0.3});",
    },
    "scale_focus": {
        "description": "Element scales up slightly and fades in to draw attention.",
        "gsap_hint": "tl.from(el, {scale: 0.8, opacity: 0, duration: 0.4, ease: 'back.out(1.2)'});",
    },
    "highlight_pulse": {
        "description": "Instant highlight or glow to emphasize an existing element.",
        "gsap_hint": "tl.to(el, {boxShadow: '0 0 20px yellow', duration: 0.3});",
    },
    "sequential_reveal": {
        "description": "List items or nodes appearing one after another.",
        "gsap_hint": "tl.from(els, {opacity: 0, y: 20, stagger: 0.2, duration: 0.4});",
    },
    "simple_transform": {
        "description": "Object changing color or shape to teach a state change.",
        "gsap_hint": "tl.to(el, {backgroundColor: '#4CAF50', duration: 0.4});",
    },
}

# ======================================================================
# Temporal Beat Types (Educational)
# ======================================================================

TEMPORAL_BEATS = {
    "setup": {
        "description": "Establish the visual concept instantly.",
    },
    "reveal": {
        "description": "A new element appears. Synchronized to speech.",
    },
    "emphasis": {
        "description": "Highlight a keyword or concept. Must map directly to spoken word.",
    },
    "transformation": {
        "description": "Visual state change showing cause and effect.",
    },
}


# ======================================================================
# Prompt Helpers
# ======================================================================

def get_patterns_prompt() -> str:
    """Format the educational visual patterns library for LLM prompts."""
    lines = ["AVAILABLE EDUCATIONAL VISUAL PATTERNS (select ONE per scene):\n"]
    for key, p in EDUCATIONAL_VISUAL_PATTERNS.items():
        lines.append(f"  - {key}: {p['description']}")
        lines.append(f"    Teaches: {p['teaches']}")
        lines.append("")
    return "\n".join(lines)


def get_shots_prompt() -> str:
    """Format the educational shot types for LLM prompts."""
    lines = ["EDUCATIONAL SHOT TYPES (select ONE per scene):\n"]
    for key, s in EDUCATIONAL_SHOTS.items():
        lines.append(f"  - {key}: {s['description']}")
        lines.append(f"    Layout: {s['layout_strategy']}")
        lines.append("")
    return "\n".join(lines)


def get_camera_prompt() -> str:
    """Format motion behaviors for LLM prompts."""
    lines = ["PEDAGOGICAL MOTION BEHAVIORS (select appropriate motion):\n"]
    for key, c in PEDAGOGICAL_MOTION.items():
        lines.append(f"  - {key}: {c['description']}")
        lines.append("")
    return "\n".join(lines)


def get_beats_prompt() -> str:
    """Format temporal beat types for LLM prompts."""
    lines = ["TEMPORAL BEAT TYPES:\n"]
    for key, b in TEMPORAL_BEATS.items():
        lines.append(f"  - {key}: {b['description']}")
    return "\n".join(lines)


def get_pattern_details(pattern_name: str) -> dict:
    """Get full details for a specific pattern."""
    return EDUCATIONAL_VISUAL_PATTERNS.get(pattern_name, EDUCATIONAL_VISUAL_PATTERNS["progressive_reveal"])


def get_shot_details(shot_name: str) -> dict:
    """Get full details for a specific educational shot type."""
    return EDUCATIONAL_SHOTS.get(shot_name, EDUCATIONAL_SHOTS["hero_focus"])

def get_depth_layers_prompt() -> str:
    return "DEPTH LAYER SYSTEM: DO NOT USE PARALLAX. Use a simple flat hierarchy (background, content, highlight). Everything must be flat, clear, and stable."

def get_motion_energy_prompt() -> str:
    return "MOTION ENERGY: Minimal and purposeful. Do not use continuous ambient motion or shaking."

def get_state_progressions_prompt() -> str:
    return "STATE PROGRESSIONS: keep it simple. e.g. [input -> processing -> output]"
