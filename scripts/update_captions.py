import json
import re
from pathlib import Path

# Paths
base_dir = Path(__file__).parent.parent
alignment_path = base_dir / "timestamps" / "alignment.json"
html_path = base_dir / "scenes" / "scene_01.html"

# Load alignment data
with open(alignment_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Format segments to JS objects
js_segments = []
for seg in data["segments"]:
    js_words = []
    for w in seg["words"]:
        # Clean text and construct word object
        word_text = w["word"].strip()
        if not word_text:
            continue
        js_words.append({
            "text": word_text,
            "start": w["start"],
            "end": w["end"]
        })
    
    js_segments.append({
        "start": seg["start"],
        "end": seg["end"],
        "words": js_words
    })

# Convert to clean formatted JS string
js_array_str = "        const sentences = " + json.dumps(js_segments, indent=4) + ";"

# Read scene_01.html
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Pattern to replace sentences array
pattern = r"(\s*//\s*---\s*INJECT\s*CAPTION\s*DATA\s*---\s*\n\s*const\s+sentences\s*=\s*\[[\s\S]*?\];)"

# If pattern matches, replace it
if re.search(pattern, html_content):
    new_block = f"\n        // --- INJECT CAPTION DATA ---\n{js_array_str}"
    updated_html = re.sub(pattern, new_block, html_content)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("Successfully updated scene_01.html with full video caption timestamps.")
else:
    print("Could not find the '// --- INJECT CAPTION DATA ---' anchor block in scene_01.html.")
