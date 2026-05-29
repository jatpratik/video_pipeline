import json
import re
from pathlib import Path

def shift_and_insert():
    base_dir = Path(__file__).parent.parent
    captions_file = base_dir / "scenes" / "scene_05_captions.js"
    
    with open(captions_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the JSON array
    match = re.search(r"window\.scene_05_captions\s*=\s*(key_out_match)?(\[[\s\S]*\]);", content)
    if not match:
        # Try raw json load if search failed
        raw_json_str = content.replace("window.scene_05_captions = ", "").rstrip(";")
        segments = json.loads(raw_json_str)
    else:
        segments = json.loads(match.group(2))
        
    shifted_segments = []
    
    # 1. Shift segments after 35.354s by 10s
    for seg in segments:
        if seg["start"] >= 35.354:
            seg["start"] += 10.0
            seg["end"] += 10.0
            for w in seg["words"]:
                w["start"] += 10.0
                w["end"] += 10.0
        shifted_segments.append(seg)
        
    # 2. Define Maya's co-host speaking segments (35.354s - 45.354s)
    maya_segments = [
        {
            "start": 35.354,
            "end": 38.0,
            "words": [
                {"text": "Hey,", "start": 35.354, "end": 35.7},
                {"text": "Maya", "start": 35.7, "end": 36.1},
                {"text": "here.", "start": 36.1, "end": 36.5},
                {"text": "The", "start": 36.7, "end": 37.0},
                {"text": "plan", "start": 37.0, "end": 37.3},
                {"text": "looks", "start": 37.3, "end": 37.6},
                {"text": "good.", "start": 37.6, "end": 38.0}
            ]
        },
        {
            "start": 38.0,
            "end": 41.5,
            "words": [
                {"text": "But", "start": 38.1, "end": 38.3},
                {"text": "AI", "start": 38.3, "end": 38.6},
                {"text": "is", "start": 38.6, "end": 38.8},
                {"text": "changing", "start": 38.8, "end": 39.2},
                {"text": "very", "start": 39.2, "end": 39.5},
                {"text": "fast.", "start": 39.5, "end": 39.9},
                {"text": "New", "start": 40.1, "end": 40.3},
                {"text": "models", "start": 40.3, "end": 40.6},
                {"text": "come", "start": 40.6, "end": 40.8},
                {"text": "out", "start": 40.8, "end": 41.0},
                {"text": "every", "start": 41.0, "end": 41.2},
                {"text": "week.", "start": 41.2, "end": 41.5}
            ]
        },
        {
            "start": 41.5,
            "end": 45.354,
            "words": [
                {"text": "Will", "start": 41.6, "end": 41.8},
                {"text": "this", "start": 41.8, "end": 42.0},
                {"text": "channel", "start": 42.0, "end": 42.4},
                {"text": "teach", "start": 42.4, "end": 42.7},
                {"text": "us", "start": 42.7, "end": 42.9},
                {"text": "the", "start": 42.9, "end": 43.1},
                {"text": "latest", "start": 43.1, "end": 43.5},
                {"text": "things,", "start": 43.5, "end": 43.9},
                {"text": "or", "start": 43.9, "end": 44.1},
                {"text": "only", "start": 44.1, "end": 44.4},
                {"text": "old", "start": 44.4, "end": 44.6},
                {"text": "textbook", "start": 44.6, "end": 45.0},
                {"text": "theory?", "start": 45.0, "end": 45.354}
            ]
        }
    ]
    
    # 3. Interweave Maya's segments in the sorted timeline
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 45.354 and not inserted:
            final_segments.extend(maya_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(maya_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.scene_05_captions = {json.dumps(final_segments, indent=2)};"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted co-host captions into {captions_file}")

if __name__ == "__main__":
    shift_and_insert()
