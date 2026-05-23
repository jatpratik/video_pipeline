"""
Step 3 — Visual Generation (HTML / CSS / GSAP)
================================================
Generates one self-contained HTML file per scene by rendering
Jinja2 templates with injected SCENE_DATA (including word-level
timestamps for emphasis).

Output: scenes/scene_001.html, scene_002.html, …
"""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger("video_pipeline.visual_gen")


def generate_visuals(
    scenes: list,
    templates_dir: Path,
    output_dir: Path,
) -> list[Path]:
    """
    Generate HTML animation files for every scene.

    Each HTML file is a self-contained document with embedded CSS and
    GSAP-driven JavaScript.  The total animation duration is set to
    exactly ``scene['duration']`` seconds.  Word-level timestamps are
    injected so the animation engine can schedule emphasis effects at
    the moment each keyword is spoken.

    Args:
        scenes:        List of scene dicts from Step 2.
        templates_dir: Directory containing the Jinja2 HTML templates.
        output_dir:    Directory to write generated scene HTML files.

    Returns:
        Ordered list of Paths to the generated HTML files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=False,            # HTML templates, no auto-escaping
        keep_trailing_newline=True,
    )

    html_files: list[Path] = []

    for scene in scenes:
        template_name = scene.get("template", "text_reveal") + ".html"

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            logger.warning(
                f"Template '{template_name}' not found — "
                f"falling back to 'text_reveal.html'"
            )
            template = env.get_template("text_reveal.html")

        # Serialise scene data for injection into JS
        scene_data_json = json.dumps(scene, ensure_ascii=False, indent=None)

        html_content = template.render(scene_data_json=scene_data_json)

        output_file = output_dir / f"{scene['scene_id']}.html"
        output_file.write_text(html_content, encoding="utf-8")

        logger.info(
            f"  Generated {output_file.name}  "
            f"[{scene['template']}] "
            f"({scene['duration']:.2f}s, "
            f"{len(scene.get('words', []))} words)"
        )
        html_files.append(output_file)

    logger.info(f"Visual generation complete → {len(html_files)} HTML files")
    return html_files
