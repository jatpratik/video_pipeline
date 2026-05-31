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
        js_words = []
        for w in seg["words"]:
            word_text = w["word"].strip()
            if not word_text:
                continue
            
            w_start = w["start"]
            w_end = w["end"]
            
            # Shift words after the co-host overlay insert point (50.577s) by 9.0s
            if w_start >= 50.577:
                w_start += 9.0
                w_end += 9.0
                
            js_words.append({
                "text": word_text,
                "start": w_start,
                "end": w_end
            })
            
        seg_start = seg["start"]
        seg_end = seg["end"]
        
        # Shift segments after the co-host overlay insert point (50.577s) by 9.0s
        if seg_start >= 50.577:
            seg_start += 9.0
            seg_end += 9.0
            
        js_segments.append({
            "start": seg_start,
            "end": seg_end,
            "words": js_words
        })
        
    # Define Tara's co-host speaking segments (50.577s - 59.577s)
    tara_segments = [
        {
            "start": 50.577,
            "end": 53.5,
            "words": [
                {"text": "But", "start": 50.577, "end": 50.8},
                {"text": "wait,", "start": 50.8, "end": 51.1},
                {"text": "Pratik!", "start": 51.1, "end": 51.6},
                {"text": "For", "start": 51.8, "end": 52.1},
                {"text": "Generative", "start": 52.1, "end": 52.7},
                {"text": "AI,", "start": 52.7, "end": 53.0},
                {"text": "since", "start": 53.0, "end": 53.3},
                {"text": "we", "start": 53.3, "end": 53.5}
            ]
        },
        {
            "start": 53.5,
            "end": 56.5,
            "words": [
                {"text": "are", "start": 53.6, "end": 53.8},
                {"text": "only", "start": 53.8, "end": 54.1},
                {"text": "using", "start": 54.1, "end": 54.4},
                {"text": "existing", "start": 54.4, "end": 54.9},
                {"text": "models,", "start": 54.9, "end": 55.4},
                {"text": "isn't", "start": 55.4, "end": 55.7},
                {"text": "it", "start": 55.7, "end": 55.9},
                {"text": "just", "start": 55.9, "end": 56.1},
                {"text": "calling", "start": 56.1, "end": 56.5}
            ]
        },
        {
            "start": 56.5,
            "end": 59.577,
            "words": [
                {"text": "APIs?", "start": 56.6, "end": 57.1},
                {"text": "How", "start": 57.3, "end": 57.6},
                {"text": "is", "start": 57.6, "end": 57.8},
                {"text": "that", "start": 57.8, "end": 58.0},
                {"text": "real", "start": 58.0, "end": 58.3},
                {"text": "engineering?", "start": 58.3, "end": 59.0}
            ]
        }
    ]
    
    # Interweave Tara's segments in the sorted timeline
    final_segments = []
    inserted = False
    for seg in js_segments:
        # Insert Tara's dialogue right after segment 14 (around 50.577s)
        if seg["start"] >= 59.577 and not inserted:
            final_segments.extend(tara_segments)
            inserted = True
        final_segments.append(seg)
        
    if not inserted:
        final_segments.extend(tara_segments)
        
    # Sort segments by start time
    final_segments.sort(key=lambda x: x["start"])
    
    js_content = f"window.roadmap_captions = {json.dumps(final_segments, indent=2)};\n"
    
    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Successfully wrote {js_output_path}")

if __name__ == "__main__":
    generate_captions()
