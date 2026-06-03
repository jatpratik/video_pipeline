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
    
    # 1. Filter out old Riya segments (between 78.0 and 86.1)
    # 2. Shift presenter segments after 86.0 by 2.0s
    for seg in segments:
        if 78.0 <= seg["start"] <= 86.1:
            # Skip old Riya segments
            continue
        if seg["start"] >= 86.0:
            seg["start"] = round(seg["start"] + 2.0, 3)
            seg["end"] = round(seg["end"] + 2.0, 3)
            for w in seg["words"]:
                w["start"] = round(w["start"] + 2.0, 3)
                w["end"] = round(w["end"] + 2.0, 3)
        shifted_segments.append(seg)
        
    # 3. Define Riya's new 10.0s speaking segments (78.1s - 88.1s)
    riya_segments = [
        {
            "start": 78.1,
            "end": 83.1,
            "words": [
                {"text": "Wait,", "start": 78.225, "end": 78.725},
                {"text": "but", "start": 78.725, "end": 78.975},
                {"text": "doesn't", "start": 78.975, "end": 79.350},
                {"text": "a", "start": 79.350, "end": 79.475},
                {"text": "team", "start": 79.475, "end": 79.850},
                {"text": "of", "start": 79.850, "end": 79.975},
                {"text": "agents", "start": 79.975, "end": 80.475},
                {"text": "make", "start": 80.475, "end": 80.850},
                {"text": "the", "start": 80.850, "end": 80.975},
                {"text": "system", "start": 80.975, "end": 81.475},
                {"text": "slow", "start": 81.600, "end": 82.100},
                {"text": "and", "start": 82.100, "end": 82.350},
                {"text": "expensive?", "start": 82.350, "end": 83.100}
            ]
        },
        {
            "start": 83.3,
            "end": 88.1,
            "words": [
                {"text": "When", "start": 83.679, "end": 84.058},
                {"text": "is", "start": 84.058, "end": 84.311},
                {"text": "a", "start": 84.311, "end": 84.437},
                {"text": "team", "start": 84.437, "end": 84.816},
                {"text": "actually", "start": 84.816, "end": 85.447},
                {"text": "better", "start": 85.447, "end": 85.953},
                {"text": "than", "start": 85.953, "end": 86.205},
                {"text": "just", "start": 86.205, "end": 86.458},
                {"text": "one", "start": 86.458, "end": 86.837},
                {"text": "good", "start": 86.837, "end": 87.216},
                {"text": "prompt?", "start": 87.216, "end": 87.900}
            ]
        }
    ]
    
    # 4. Interweave Riya's segments
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 88.0 and not inserted:
            final_segments.extend(riya_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(riya_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.agent_scene_02_captions = {json.dumps(final_segments, indent=2)};\n"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted Riya's captions (10s) into {captions_file}")

if __name__ == "__main__":
    main()
