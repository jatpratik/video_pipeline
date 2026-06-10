# e:/my-workspace/content_design/video_pipeline/visual_agents/utils.py

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

def generate_captions_js(combined_alignment_path: Path, output_js_path: Path, scene_id: str) -> None:
    """
    Generates a captions.js file from the combined alignment JSON.
    It writes to output_js_path with the window.<scene_id>_captions global variable.
    """
    if not combined_alignment_path.exists():
        raise FileNotFoundError(f"Combined alignment file not found: {combined_alignment_path}")
        
    with open(combined_alignment_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    js_segments = []
    for seg in data.get("segments", []):
        js_words = []
        for w in seg.get("words", []):
            word_text = w.get("word", "").strip()
            if not word_text:
                continue
            js_words.append({
                "text": word_text,
                "start": w.get("start"),
                "end": w.get("end")
            })
            
        js_segments.append({
            "text": seg.get("text", "").strip(),
            "start": seg.get("start"),
            "end": seg.get("end"),
            "words": js_words
        })
        
    # Write captions file
    js_content = f"window.{scene_id}_captions = {json.dumps(js_segments, indent=2, ensure_ascii=False)};\n"
    
    # Ensure parent directories exist
    output_js_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_js_path, "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"[Captions] Successfully auto-generated captions JS: {output_js_path}")

def update_scenes_json(scenes_json_path: Path, scene_id: str, duration: float, overlays: List[Dict[str, Any]]) -> None:
    """
    Reads scenes.json, updates or inserts the scene entry with the target scene_id,
    duration, and overlays, and saves it.
    """
    data = []
    if scenes_json_path.exists():
        try:
            with open(scenes_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"[Warning] Failed to decode {scenes_json_path}. Starting clean list.")
            
    # Find existing scene or create one
    scene_entry = None
    for entry in data:
        if entry.get("scene_id") == scene_id:
            scene_entry = entry
            break
            
    if scene_entry is None:
        scene_entry = {"scene_id": scene_id}
        data.append(scene_entry)
        
    scene_entry["duration"] = round(duration, 3)
    scene_entry["overlays"] = overlays
    
    # Ensure scenes.json directory exists
    scenes_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scenes_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"[Scenes Config] Successfully updated scenes configuration in {scenes_json_path}")

def normalize_text(text: str) -> str:
    """Lowercase, remove punctuation, and normalize spaces."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())

def find_timestamp_by_caption_line(alignment_data: Dict[str, Any], caption_line: str) -> Optional[Dict[str, Any]]:
    """
    Finds the segment in alignment_data that best matches the caption_line.
    Returns the segment dict (with 'start', 'end', and 'text') or None.
    """
    query_norm = normalize_text(caption_line)
    if not query_norm:
        return None
        
    segments = alignment_data.get("segments", [])
    best_match = None
    best_score = 0.0
    
    # 1. First check for direct substring match
    for seg in segments:
        seg_text_norm = normalize_text(seg.get("text", ""))
        if query_norm in seg_text_norm or seg_text_norm in query_norm:
            # Substring match gets high score based on length overlap
            overlap_len = min(len(query_norm), len(seg_text_norm))
            score = 1.0 + (overlap_len / 1000.0)
            if score > best_score:
                best_score = score
                best_match = seg
                
    if best_match and best_score >= 1.0:
        return best_match
        
    # 2. Fuzzy token-based matching if no clear substring match
    query_words = set(query_norm.split())
    for seg in segments:
        seg_text_norm = normalize_text(seg.get("text", ""))
        seg_words = set(seg_text_norm.split())
        
        # Word overlap (Jaccard similarity style or intersection size)
        intersection = query_words.intersection(seg_words)
        if not intersection:
            continue
            
        score = len(intersection) / max(len(query_words), len(seg_words))
        if score > best_score:
            best_score = score
            best_match = seg
            
    # Require a minimum threshold for word overlap
    if best_score > 0.2:
        return best_match
        
    return None

def update_task_markdown(output_path: Path, active_task: str, status: str, notes: str = "") -> None:
    """Updates the task progress markdown file visual_agents_task.md."""
    task_file = output_path.parent / "visual_agents_task.md"
    
    # Define order of tasks
    tasks = [
        "Load inputs & configuration",
        "Design structured visual plan",
        "Human-in-the-Loop review & approval",
        "Generate HTML / CSS / GSAP scene",
        "Validate generated scene layout",
        "Save scene files & update configs",
        "Browser feedback loop refinements"
    ]
    
    # Read existing file to preserve state of other checkboxes if we want
    checkboxes = {t: "[ ]" for t in tasks}
    if task_file.exists():
        try:
            content = task_file.read_text(encoding="utf-8")
            for t in tasks:
                # Find the checkbox state in file
                match = re.search(r"-\s*\[([ x/])\]\s*" + re.escape(t), content)
                if match:
                    checkboxes[t] = f"[{match.group(1)}]"
        except Exception:
            pass
            
    # Update active task state
    if status == "done":
        checkboxes[active_task] = "[x]"
    elif status == "in_progress":
        checkboxes[active_task] = "[/]"
    elif status == "failed":
        checkboxes[active_task] = "[ ]" # keep empty/todo
    else:
        checkboxes[active_task] = "[ ]"
        
    # Write the updated task markdown
    md_content = "# Visual Agent Task Tracking\n\n"
    for t in tasks:
        md_content += f"- {checkboxes[t]} {t}\n"
        
    md_content += f"\n## Active Node\n{active_task} ({status.upper()})\n"
    if notes:
        md_content += f"\n## Notes\n{notes}\n"
        
    try:
        task_file.write_text(md_content, encoding="utf-8")
        print(f"[Task Tracker] Updated visual_agents_task.md at {task_file}")
    except Exception as e:
        print(f"[Warning] Failed to write task tracking markdown: {e}")

