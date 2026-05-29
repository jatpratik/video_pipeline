import json
from pathlib import Path

def convert():
    base_dir = Path(__file__).parent.parent
    alignment_path = base_dir / "timestamps" / "alignment.json"
    js_output_path = base_dir / "scenes" / "scene_05_captions.js"
    
    with open(alignment_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    js_segments = []
    for seg in data["segments"]:
        js_words = []
        for w in seg["words"]:
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
        
    js_content = f"window.scene_05_captions = {json.dumps(js_segments, indent=2)};"
    
    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully wrote {js_output_path}")

if __name__ == "__main__":
    convert()
