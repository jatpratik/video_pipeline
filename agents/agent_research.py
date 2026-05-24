"""
Agent 2 — Research Agent
===========================
Maps educational concepts to visual metaphors and teaching patterns.

v1: Uses an embedded knowledge base of visual teaching patterns.
Architected so real web search can be added as an optional mode later.
"""

import logging
from .llm_client import call_llm

logger = logging.getLogger("video_pipeline.agents.research")

# ======================================================================
# Embedded Visual Knowledge Base
# ======================================================================

VISUAL_KNOWLEDGE_BASE = """
VISUAL METAPHORS FOR COMMON TECHNICAL CONCEPTS:

AI & Machine Learning:
- Neural networks → layered connected nodes with glowing activation paths
- Training → progress bar filling, loss curve descending
- Inference → input flowing through a pipeline to output
- Attention mechanism → spotlight beams connecting elements
- Model → black box with input/output arrows

APIs & Web:
- API call → request arrow going out, response arrow coming back
- REST endpoint → labeled door/gateway
- Authentication → lock/key animation
- Rate limiting → funnel narrowing flow

Data & Processing:
- Data pipeline → conveyor belt or flowing river
- ETL → three connected stages with transformation in middle
- Database → cylinder/storage icon
- Caching → fast-access memory layer above slower storage

Programming Concepts:
- Variables → labeled boxes/containers
- Functions → machine/factory taking input, producing output
- Loops → circular arrows
- Conditionals → branching paths (fork in road)
- Recursion → nested mirrors or Russian dolls

Prompt Engineering & LLMs:
- Prompt → text block entering a brain/processor
- Prompt chaining → sequential boxes connected by arrows
- Context window → fixed-size container that overflows
- Token → small text blocks/puzzle pieces
- Hallucination → distorted/glitchy output
- RAG → retrieval step (search) before generation step

Systems & Architecture:
- Microservices → separate boxes with communication lines
- Load balancing → traffic distributor
- Message queue → conveyor belt with items waiting
- Orchestration → conductor directing multiple instruments

Error & Failure:
- Bug → red warning flash
- Crash → system shutdown animation
- Latency → slow hourglass or expanding gap
- Bottleneck → narrow passage restricting flow

EDUCATIONAL ANIMATION PATTERNS:

Progressive Disclosure:
- Reveal information step-by-step, never all at once
- Each new element appears as narration mentions it
- Previously revealed elements dim slightly (context, not focus)

Before/After:
- Split screen or sequential transformation
- Show the "wrong way" first, then the "right way"
- Red → Green color transition

Step-by-Step Process:
- Numbered nodes appearing sequentially
- Connection lines animating between steps
- Active step highlighted, others dimmed

Cause & Effect:
- Cause element triggers animation that flows to effect element
- Visual chain reaction
- Domino effect metaphor

Zoom & Focus:
- Start wide (overview), zoom into detail
- Or start with detail, zoom out to show context
- Spotlight effect on key elements

Comparison:
- Side by side panels
- Toggle/switch between views
- Overlapping with transparency

Accumulation:
- Elements stack or collect
- Counter increases
- Bar chart grows

Transformation:
- Element morphs from one form to another
- Input transforms through a process into output
- Visual metamorphosis

TEACHING PRINCIPLES FOR VISUAL EXPLANATION:

1. ONE idea per visual moment
2. Show, don't just label
3. Use spatial relationships to show logical relationships
4. Motion should MEAN something (not decorative)
5. Color should be SEMANTIC (consistent meaning)
6. Text should be MINIMAL (supporting, not primary)
7. Timing should match cognitive load (complex = slower)
"""

SYSTEM_PROMPT = f"""You are a VISUAL RESEARCH SPECIALIST for educational content.

You have deep knowledge of how to visually explain technical concepts.

Given a concept analysis, identify the BEST visual metaphors and teaching patterns
for explaining these specific concepts.

{VISUAL_KNOWLEDGE_BASE}

You MUST return a JSON object:

{{
  "best_visual_metaphors": [
    {{
      "concept": "the concept being visualized",
      "metaphor": "the visual metaphor to use",
      "why": "why this metaphor works for teaching this concept"
    }}
  ],
  "educational_patterns": [
    {{
      "pattern": "the animation pattern name",
      "apply_to": "which part of the narration this applies to",
      "why": "why this pattern is effective here"
    }}
  ],
  "teaching_analogies": [
    {{
      "complex_idea": "the difficult concept",
      "simple_analogy": "the simpler way to represent it",
      "visual_form": "how to render the analogy visually"
    }}
  ],
  "visual_warnings": [
    "things to AVOID in the visual design for this topic"
  ]
}}

IMPORTANT:
- Be SPECIFIC to the actual concepts in the script
- Prioritize CLARITY over creativity
- Choose metaphors that viewers will INSTANTLY understand
- Avoid overly abstract or artistic representations
"""


def run_research(
    concept_analysis: dict,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
    use_web_search: bool = False,
) -> dict:
    """
    Map concepts to visual metaphors and teaching patterns.

    Args:
        concept_analysis: Output from Agent 1.
        api_key:          OpenAI API key.
        model:            Model identifier.
        temperature:      Sampling temperature.
        use_web_search:   If True, augment with web search (future v2).

    Returns:
        Research insights dict.
    """
    logger.info("Agent 2: Researching visual teaching patterns…")

    if use_web_search:
        logger.info("  Web search mode: not yet implemented, using embedded KB")
        # Future: call search_web() here to augment the knowledge base
        # web_context = _search_visual_patterns(concept_analysis)

    import json
    user_prompt = f"""Here is the concept analysis for an educational video:

{json.dumps(concept_analysis, indent=2)}

Based on this analysis, identify:
1. The best VISUAL METAPHORS for each concept
2. The best EDUCATIONAL ANIMATION PATTERNS for this narration flow
3. TEACHING ANALOGIES that simplify difficult concepts
4. WARNINGS about visual pitfalls to avoid

Return your research as a JSON object."""

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=2048,
        json_mode=True,
        agent_name="Research",
    )

    # Log summary
    metaphors = result.get("best_visual_metaphors", [])
    patterns = result.get("educational_patterns", [])
    logger.info(
        f"  Found {len(metaphors)} visual metaphors, "
        f"{len(patterns)} educational patterns"
    )
    for m in metaphors[:3]:
        logger.info(f"    • {m.get('concept', '?')} → {m.get('metaphor', '?')}")

    return result
