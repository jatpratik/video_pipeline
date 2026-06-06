import json
from pathlib import Path

def main():
    base_dir = Path(__file__).parent.parent
    alignment_file = base_dir / "timestamps" / "alignment.json"
    captions_file = base_dir / "scenes" / "agent_scene_03_captions.js"
    
    with open(alignment_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    segments = data["segments"]
    shifted_segments = []
    
    # Shifts:
    # 1. Before 91.615s (end of Prediction 5): shift by 9.5s (due to start_hook.mp4)
    # 2. Maya's speaking segment runs from 101.115s to 111.115s (visual overlay window)
    # 3. After 91.615s (Safety Sandbox and onwards): shift by 19.5s (9.5s start_hook + 10.0s student_speaking)
    
    for seg in segments:
        # Check start time to decide the shift
        if seg["start"] < 91.615:
            shift = 9.5
        else:
            shift = 19.5
            
        seg_shifted = {
            "text": seg["text"],
            "start": round(seg["start"] + shift, 3),
            "end": round(seg["end"] + shift, 3),
            "words": []
        }
        for w in seg["words"]:
            seg_shifted["words"].append({
                "text": w["word"],
                "start": round(w["start"] + shift, 3),
                "end": round(w["end"] + shift, 3)
            })
        shifted_segments.append(seg_shifted)
        
    # Maya's speaking segments (101.115s - 111.115s visual window)
    # Maya starts speaking at 101.115s + 1s padding_start = 102.115s
    # Speaks for 8s, ending at 110.115s
    maya_segments = [
        {
            "text": "Wait... if a system can write its own code and change its own structure,",
            "start": 102.115,
            "end": 106.115,
            "words": [
                {"text": "Wait...", "start": 102.2, "end": 102.6},
                {"text": "if", "start": 102.7, "end": 102.9},
                {"text": "a", "start": 102.9, "end": 103.0},
                {"text": "system", "start": 103.0, "end": 103.4},
                {"text": "can", "start": 103.4, "end": 103.6},
                {"text": "write", "start": 103.6, "end": 103.9},
                {"text": "its", "start": 103.9, "end": 104.1},
                {"text": "own", "start": 104.1, "end": 104.3},
                {"text": "code", "start": 104.3, "end": 104.6},
                {"text": "and", "start": 104.7, "end": 104.9},
                {"text": "change", "start": 104.9, "end": 105.2},
                {"text": "its", "start": 105.2, "end": 105.4},
                {"text": "own", "start": 105.4, "end": 105.6},
                {"text": "structure,", "start": 105.6, "end": 106.1}
            ]
        },
        {
            "text": "how do we keep it under control? What if it does something dangerous?",
            "start": 106.215,
            "end": 110.115,
            "words": [
                {"text": "how", "start": 106.3, "end": 106.6},
                {"text": "do", "start": 106.6, "end": 106.8},
                {"text": "we", "start": 106.8, "end": 107.0},
                {"text": "keep", "start": 107.0, "end": 107.3},
                {"text": "it", "start": 107.3, "end": 107.5},
                {"text": "under", "start": 107.5, "end": 107.9},
                {"text": "control?", "start": 107.9, "end": 108.4},
                {"text": "What", "start": 108.6, "end": 108.9},
                {"text": "if", "start": 108.9, "end": 109.1},
                {"text": "it", "start": 109.1, "end": 109.3},
                {"text": "does", "start": 109.3, "end": 109.5},
                {"text": "something", "start": 109.5, "end": 109.8},
                {"text": "dangerous?", "start": 109.8, "end": 110.1}
            ]
        }
    ]
    
    # Interweave Maya's segments in the timeline
    final_segments = []
    inserted = False
    for seg in shifted_segments:
        if seg["start"] >= 111.115 and not inserted:
            final_segments.extend(maya_segments)
            inserted = True
        final_segments.append(seg)
    if not inserted:
        final_segments.extend(maya_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.agent_scene_03_captions = {json.dumps(final_segments, indent=2)};"
    with open(captions_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully shifted and inserted Maya's captions into {captions_file}")

if __name__ == "__main__":
    main()
