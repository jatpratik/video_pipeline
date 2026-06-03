import json
import re
from pathlib import Path

def main():
    base_dir = Path(__file__).parent.parent
    captions_file = base_dir / "scenes" / "agent_scene_02_captions.js"
    
    with open(captions_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract the JSON array
    match = re.search(r"window\.agent_scene_02_captions\s*=\s*(\[[\s\S]*\]);", content)
    if not match:
        raise ValueError("Could not parse captions JS format")
        
    segments = json.loads(match.group(1))
    shifted_segments = []
    
    # 1. Shift presenter segments after 78.1s by 8s
    for seg in segments:
        if seg["start"] >= 78.1:
            seg["start"] += 8.0
            seg["end"] += 8.0
            for w in seg["words"]:
                w["start"] += 8.0
                w["end"] += 8.0
        shifted_segments.append(seg)
        
    # 2. Define Riya's speaking segments (78.1s - 86.1s)
    riya_segments = [
        {
            "start": 78.1,
            "end": 82.1,
            "words": [
                {"text": "Wait,", "start": 78.2, "end": 78.6},
                {"text": "but", "start": 78.6, "end": 78.8},
                {"text": "doesn't", "start": 78.8, "end": 79.1},
                {"text": "a", "start": 79.1, "end": 79.2},
                {"text": "team", "start": 79.2, "end": 79.5},
                {"text": "of", "start": 79.5, "end": 79.6},
                {"text": "agents", "start": 79.6, "end": 80.0},
                {"text": "make", "start": 80.0, "end": 80.3},
                {"text": "the", "start": 80.3, "end": 80.4},
                {"text": "system", "start": 80.4, "end": 80.8},
                {"text": "slow", "start": 80.9, "end": 81.3},
                {"text": "and", "start": 81.3, "end": 81.5},
                {"text": "expensive?", "start": 81.5, "end": 82.1}
            ]
        },
        {
            "start": 82.3,
            "end": 86.1,
            "words": [
                {"text": "When", "start": 82.6, "end": 82.9},
                {"text": "is", "start": 82.9, "end": 83.1},
                {"text": "a", "start": 83.1, "end": 83.2},
                {"text": "team", "start": 83.2, "end": 83.5},
                {"text": "actually", "start": 83.5, "end": 84.0},
                {"text": "better", "start": 84.0, "end": 84.4},
                {"text": "than", "start": 84.4, "end": 84.6},
                {"text": "just", "start": 84.6, "end": 84.8},
                {"text": "one", "start": 84.8, "end": 85.1},
                {"text": "good", "start": 85.1, "end": 85.4},
                {"text": "prompt?", "start": 85.4, "end": 85.9}
            ]
        }
    ]
    
    # 3. Interweave Riya's segments in the timeline
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 86.1 and not inserted:
            final_segments.extend(riya_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(riya_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.agent_scene_02_captions = {json.dumps(final_segments, indent=2)};"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted Riya's captions into {captions_file}")

if __name__ == "__main__":
    main()
