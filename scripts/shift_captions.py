import json
import re
from pathlib import Path

def shift_and_insert():
    base_dir = Path(__file__).parent.parent
    captions_file = base_dir / "scenes" / "scene_02_captions.js"
    
    with open(captions_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the JSON array
    match = re.search(r"window\.scene_02_captions\s*=\s*(key_out_match)?(\[[\s\S]*\]);", content)
    if not match:
        raw_json_str = content.replace("window.scene_02_captions = ", "").rstrip(";")
        segments = json.loads(raw_json_str)
    else:
        segments = json.loads(match.group(2))
        
    shifted_segments = []
    
    # 1. Shift presenter segments after 90.5s by 8s
    for seg in segments:
        if seg["start"] >= 90.5:
            seg["start"] += 8.0
            seg["end"] += 8.0
            for w in seg["words"]:
                w["start"] += 8.0
                w["end"] += 8.0
        shifted_segments.append(seg)
        
    # 2. Define Tara's speaking segments (90.5s - 98.5s)
    tara_segments = [
        {
            "start": 90.5,
            "end": 94.1,
            "words": [
                {"text": "Wait,", "start": 90.5, "end": 90.9},
                {"text": "Pratik!", "start": 90.9, "end": 91.4},
                {"text": "If", "start": 91.6, "end": 91.8},
                {"text": "a", "start": 91.8, "end": 91.9},
                {"text": "matrix", "start": 91.9, "end": 92.4},
                {"text": "can", "start": 92.4, "end": 92.6},
                {"text": "only", "start": 92.6, "end": 92.9},
                {"text": "stretch", "start": 92.9, "end": 93.4},
                {"text": "and", "start": 93.4, "end": 93.6},
                {"text": "rotate", "start": 93.6, "end": 94.1}
            ]
        },
        {
            "start": 94.1,
            "end": 98.5,
            "words": [
                {"text": "space", "start": 94.1, "end": 94.5},
                {"text": "in", "start": 94.5, "end": 94.7},
                {"text": "straight", "start": 94.7, "end": 95.1},
                {"text": "lines,", "start": 95.1, "end": 95.6},
                {"text": "how", "start": 96.0, "end": 96.2},
                {"text": "do", "start": 96.2, "end": 96.4},
                {"text": "neural", "start": 96.4, "end": 96.7},
                {"text": "networks", "start": 96.7, "end": 97.1},
                {"text": "separate", "start": 97.1, "end": 97.6},
                {"text": "complex,", "start": 97.6, "end": 98.0},
                {"text": "mixed-up", "start": 98.0, "end": 98.3},
                {"text": "data?", "start": 98.3, "end": 98.5}
            ]
        }
    ]
    
    # 3. Interweave Tara's segments in the sorted timeline
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 98.5 and not inserted:
            final_segments.extend(tara_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(tara_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.scene_02_captions = {json.dumps(final_segments, indent=2)};"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted Tara's captions into {captions_file}")

if __name__ == "__main__":
    shift_and_insert()
