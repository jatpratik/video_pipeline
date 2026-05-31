import json
from pathlib import Path

def generate_captions():
    base_dir = Path(__file__).parent.parent
    alignment_path = base_dir / "timestamps" / "alignment.json"
    js_output_path = base_dir / "scenes" / "roadmap_captions.js"
    
    with open(alignment_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    js_segments = []
    for seg in data["segments"]:
        is_tara = (seg.get("speaker") == "tara")
        js_words = []
        for w in seg["words"]:
            word_text = w["word"].strip()
            if not word_text:
                continue
            
            w_start = w["start"]
            w_end = w["end"]
            
            # Shift words:
            # - Tara's own segments are shifted by +0.5s to align with video padding_start
            # - Other segments after the insert point (50.577s) are shifted by +10.0s
            if is_tara:
                w_start += 0.5
                w_end += 0.5
            elif w_start >= 50.577:
                w_start += 10.0
                w_end += 10.0
                
            js_words.append({
                "text": word_text,
                "start": w_start,
                "end": w_end
            })
            
        seg_start = seg["start"]
        seg_end = seg["end"]
        
        # Shift segments:
        # - Tara's own segments are shifted by +0.5s to align with video padding_start
        # - Other segments after the insert point (50.577s) are shifted by +10.0s
        if is_tara:
            seg_start += 0.5
            seg_end += 0.5
        elif seg_start >= 50.577:
            seg_start += 10.0
            seg_end += 10.0
            
        js_segments.append({
            "start": seg_start,
            "end": seg_end,
            "words": js_words
        })
        
    # Sort segments by start time
    js_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.roadmap_captions = {json.dumps(js_segments, indent=2)};\n"
    
    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully wrote {js_output_path}")

if __name__ == "__main__":
    generate_captions()
