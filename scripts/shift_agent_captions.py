import json
import re
from pathlib import Path

def main():
    base_dir = Path(__file__).parent.parent
    captions_file = base_dir / "scenes" / "agent_scene_01_captions.js"
    
    with open(captions_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the JSON array
    match = re.search(r"window\.agent_scene_01_captions\s*=\s*(\[[\s\S]*\]);", content)
    if not match:
        raise ValueError("Could not parse captions JS format")
        
    segments = json.loads(match.group(1))
    shifted_segments = []
    
    # 1. Shift presenter segments after 68.8s by 8s
    for seg in segments:
        if seg["start"] >= 68.8:
            seg["start"] += 8.0
            seg["end"] += 8.0
            for w in seg["words"]:
                w["start"] += 8.0
                w["end"] += 8.0
        shifted_segments.append(seg)
        
    # 2. Define Riya's speaking segments (68.8s - 76.8s)
    riya_segments = [
        {
            "start": 68.8,
            "end": 72.8,
            "words": [
                {"text": "Wait,", "start": 68.9, "end": 69.3},
                {"text": "but", "start": 69.3, "end": 69.5},
                {"text": "doesn't", "start": 69.5, "end": 69.8},
                {"text": "a", "start": 69.8, "end": 69.9},
                {"text": "team", "start": 69.9, "end": 70.2},
                {"text": "of", "start": 70.2, "end": 70.3},
                {"text": "agents", "start": 70.3, "end": 70.7},
                {"text": "make", "start": 70.7, "end": 71.0},
                {"text": "the", "start": 71.0, "end": 71.1},
                {"text": "system", "start": 71.1, "end": 71.5},
                {"text": "slow", "start": 71.6, "end": 72.0},
                {"text": "and", "start": 72.0, "end": 72.2},
                {"text": "expensive?", "start": 72.2, "end": 72.8}
            ]
        },
        {
            "start": 73.0,
            "end": 76.8,
            "words": [
                {"text": "When", "start": 73.3, "end": 73.6},
                {"text": "is", "start": 73.6, "end": 73.8},
                {"text": "a", "start": 73.8, "end": 73.9},
                {"text": "team", "start": 73.9, "end": 74.2},
                {"text": "actually", "start": 74.2, "end": 74.7},
                {"text": "better", "start": 74.7, "end": 75.1},
                {"text": "than", "start": 75.1, "end": 75.3},
                {"text": "just", "start": 75.3, "end": 75.5},
                {"text": "one", "start": 75.5, "end": 75.8},
                {"text": "good", "start": 75.8, "end": 76.1},
                {"text": "prompt?", "start": 76.1, "end": 76.6}
            ]
        }
    ]
    
    # 3. Interweave Riya's segments in the sorted timeline
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 76.8 and not inserted:
            final_segments.extend(riya_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(riya_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.agent_scene_01_captions = {json.dumps(final_segments, indent=2)};"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted Riya's captions into {captions_file}")

if __name__ == "__main__":
    main()
