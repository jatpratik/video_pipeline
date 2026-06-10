# e:/my-workspace/content_design/video_pipeline/visual_agents/nodes.py

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt

from .state import VisualPlannerState
from .utils import generate_captions_js, update_scenes_json, find_timestamp_by_caption_line, update_task_markdown
from . import prompts

# Load environment
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# Initialize ChatAnthropic model
# Standard Sonnet 3.5 output tokens can be up to 8192.
llm = ChatAnthropic(
    model=model_name,
    api_key=api_key,
    temperature=0.2,
    max_tokens=8000
)

def load_inputs(state: VisualPlannerState) -> Dict[str, Any]:
    """Loads input files and sets up identifiers."""
    output_path = Path(state.get("output_path", "scenes/ep_04_scene.html"))
    update_task_markdown(output_path, "Load inputs & configuration", "in_progress")
    
    script_path = Path(state.get("script_text"))  # Overloaded in init state as path
    alignment_path = Path(state.get("alignment_data"))  # Path
    scenes_path = Path(state.get("scene_config"))  # Path
    reference_path = Path(state.get("reference_template"))  # Path
    
    # 1. Determine Episode ID and Scene ID
    episode_id = "ep_04"
    if "ep_" in script_path.name:
        match = re.search(r"ep_(\d+)", script_path.name)
        if match:
            episode_id = f"ep_{match.group(1)}"
            
    scene_id = f"{episode_id}_scene"
    
    # 2. Read Files
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
        
    with open(alignment_path, "r", encoding="utf-8") as f:
        alignment_data = json.load(f)
        
    # Read reference template (only layout constraints structure)
    with open(reference_path, "r", encoding="utf-8") as f:
        reference_text = f.read()
        
    # Extract excerpt of layout container structure (around lines 90 to 180)
    # This helps guide the code generator without pasting the 1700+ lines visual code.
    lines = reference_text.splitlines()
    excerpt_lines = []
    # Extract styles/structure related to Captions & Face frame
    for idx, line in enumerate(lines):
        if "CAPTIONS" in line or "face-frame" in line or "sentence-block" in line:
            start_idx = max(0, idx - 5)
            end_idx = min(len(lines), idx + 15)
            excerpt_lines.append(f"Lines {start_idx}-{end_idx}:")
            excerpt_lines.append("\n".join(lines[start_idx:end_idx]))
            excerpt_lines.append("...\n")
            
    # Include script structure block (sentences loop)
    for idx, line in enumerate(lines):
        if "sentences.forEach" in line or "tl = gsap.timeline" in line:
            start_idx = max(0, idx - 5)
            end_idx = min(len(lines), idx + 25)
            excerpt_lines.append(f"Lines {start_idx}-{end_idx}:")
            excerpt_lines.append("\n".join(lines[start_idx:end_idx]))
            excerpt_lines.append("...\n")
            
    reference_excerpt = "\n".join(excerpt_lines)

    # Read scenes config (look for this episode)
    scene_config = {}
    if scenes_path.exists():
        try:
            with open(scenes_path, "r", encoding="utf-8") as f:
                scenes_list = json.load(f)
                for item in scenes_list:
                    if item.get("scene_id") == scene_id:
                        scene_config = item
                        break
        except Exception as e:
            print(f"[Warning] Failed to load scenes.json: {e}")

    update_task_markdown(output_path, "Load inputs & configuration", "done")

    # Return populated state
    return {
        "episode_id": episode_id,
        "scene_id": scene_id,
        "script_text": script_text,
        "alignment_data": alignment_data,
        "scene_config": scene_config,
        "reference_template": reference_excerpt,
        "human_assets": state.get("human_assets", []),
        "validation_errors": [],
        "generation_attempts": 0,
        "refinement_mode": False
    }

def plan_visuals(state: VisualPlannerState) -> Dict[str, Any]:
    """Generates a structured visual plan using Claude."""
    output_path = Path(state.get("output_path", "scenes/ep_04_scene.html"))
    if state.get("refinement_mode", False):
        return {}
        
    update_task_markdown(output_path, "Design structured visual plan", "in_progress")
    print(f"\n--- [Planning Node] Designing Visual Plan for {state['episode_id']} ---")
    
    # Format a condensed snippet of alignment data (first few words of each segment)
    segments = state["alignment_data"].get("segments", [])
    condensed_segments = []
    for idx, seg in enumerate(segments):
        text = seg.get("text", "")
        start = seg.get("start")
        end = seg.get("end")
        condensed_segments.append({
            "segment_index": idx,
            "text": text,
            "start": start,
            "end": end
        })
    alignment_snippet = json.dumps(condensed_segments, indent=2)

    # Human feedback context
    feedback_text = "None."
    if state.get("human_feedback"):
        feedback_text = state["human_feedback"]
        
    if state.get("human_assets"):
        feedback_text += f"\nInject these human asset paths/descriptions: {state['human_assets']}"

    # Setup prompt
    user_prompt = prompts.VISUAL_PLANNER_USER_PROMPT.format(
        script_text=state["script_text"],
        alignment_data_snippet=alignment_snippet,
        scenes_config=json.dumps(state["scene_config"], indent=2),
        human_feedback_text=feedback_text
    )

    messages = [
        SystemMessage(content=prompts.VISUAL_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Strip markdown code blocks if the model wrapped it in ```json
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
            content = content.strip()
            
        visual_plan = json.loads(content)
        update_task_markdown(output_path, "Design structured visual plan", "done")
        return {
            "visual_plan": visual_plan,
            "plan_approved": False  # Reset for next review node
        }
    except json.JSONDecodeError as e:
        print(f"[Warning] First planning attempt failed JSON parse: {e}. Retrying with strict conciseness constraints...")
        
        retry_messages = messages + [
            HumanMessage(content="The JSON response failed to parse because it was truncated or malformed. "
                                 "Please regenerate the plan, but make it SIGNIFICANTLY more compact. "
                                 "Combine adjacent narrator segments into at most 5-6 broad acts. "
                                 "Limit each act to at most 1-2 elements. "
                                 "Ensure your entire output is valid JSON and well within the token limit. "
                                 "Output ONLY the JSON and nothing else.")
        ]
        
        try:
            response_retry = llm.invoke(retry_messages)
            content_retry = response_retry.content.strip()
            
            if content_retry.startswith("```"):
                content_retry = re.sub(r"^```[a-zA-Z]*\n", "", content_retry)
                content_retry = re.sub(r"\n```$", "", content_retry)
                content_retry = content_retry.strip()
                
            visual_plan = json.loads(content_retry)
            print("[Success] JSON parsed successfully on retry.")
            update_task_markdown(output_path, "Design structured visual plan", "done")
            return {
                "visual_plan": visual_plan,
                "plan_approved": False
            }
        except Exception as retry_err:
            print(f"[Error] Failed to parse retry response as JSON: {retry_err}")
            update_task_markdown(output_path, "Design structured visual plan", "failed", "JSON parsing failed on retry.")
            return {
                "visual_plan": {"error": "JSON parse failure on retry", "raw_content": content_retry if 'content_retry' in locals() else content},
                "plan_approved": False
            }

def human_review(state: VisualPlannerState) -> Dict[str, Any]:
    """Interrupts the graph to let the user review the visual plan."""
    output_path = Path(state.get("output_path", "scenes/ep_04_scene.html"))
    update_task_markdown(output_path, "Human-in-the-Loop review & approval", "in_progress", "Awaiting user approval in CLI...")
    
    # Raise a LangGraph interrupt passing the visual plan
    decision = interrupt({
        "visual_plan": state.get("visual_plan"),
        "human_assets": state.get("human_assets", [])
    })
    
    # The runner will resume and pass the decision dict back
    approved = decision.get("approved", False)
    status_str = "done" if approved else "failed"
    notes_str = "Plan approved by user." if approved else f"Plan rejected: {decision.get('feedback', '')}"
    update_task_markdown(output_path, "Human-in-the-Loop review & approval", status_str, notes_str)
    
    return {
        "plan_approved": approved,
        "human_feedback": decision.get("feedback", ""),
        "human_assets": decision.get("assets", state.get("human_assets", []))
    }

def generate_code(state: VisualPlannerState) -> Dict[str, Any]:
    """Generates the HTML/CSS/GSAP code based on the approved plan or browser feedback."""
    output_path = Path(state.get("output_path", "scenes/ep_04_scene.html"))
    attempts = state.get("generation_attempts", 0) + 1
    
    # Check if we are in browser feedback refinement loop
    if state.get("refinement_mode"):
        print(f"\n--- [Code Refinement Node] Applying Browser Feedback (Caption: '{state['refinement_caption_line']}') ---")
        update_task_markdown(output_path, "Browser feedback loop refinements", "in_progress", f"Applying change: {state.get('refinement_feedback')}")
        
        # Match caption line to timestamp segment
        matching_seg = find_timestamp_by_caption_line(state["alignment_data"], state["refinement_caption_line"])
        if matching_seg:
            start_time = matching_seg["start"]
            end_time = matching_seg["end"]
            # To get unshifted times, subtract shifts:
            # Shift is 9.5s before 91.615s narrator time (101.115s visual time), 19.5s after.
            # Visual time is start_time.
            if start_time < 101.115:
                unshifted_start = round(start_time - 9.5, 3)
                unshifted_end = round(end_time - 9.5, 3)
            else:
                unshifted_start = round(start_time - 19.5, 3)
                unshifted_end = round(end_time - 19.5, 3)
                
            shifted_start_time = start_time
            shifted_end_time = end_time
        else:
            print(f"[Warning] Could not find timestamp match for: '{state['refinement_caption_line']}'. Fallback to general modification.")
            unshifted_start = "unknown"
            unshifted_end = "unknown"
            shifted_start_time = "unknown"
            shifted_end_time = "unknown"

        user_prompt = prompts.BROWSER_REFINEMENT_USER_PROMPT.format(
            caption_line=state["refinement_caption_line"],
            start_time=unshifted_start,
            end_time=unshifted_end,
            shifted_start_time=shifted_start_time,
            shifted_end_time=shifted_end_time,
            feedback=state["refinement_feedback"],
            html_code=state["generated_code"]
        )
        
        messages = [
            SystemMessage(content=prompts.BROWSER_REFINEMENT_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Clean markdown formatting if present
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
            content = content.strip()
            
        update_task_markdown(output_path, "Browser feedback loop refinements", "done", f"Feedback applied: {state.get('refinement_feedback')}")
        return {
            "generated_code": content,
            "refinement_mode": False,  # Reset loop flag
            "validation_errors": []
        }
        
    # Check if we are doing error correction retry
    errors = state.get("validation_errors", [])
    if errors:
        print(f"\n--- [Code Generator Node] Attempt {attempts}: Correcting Validation Errors ---")
        update_task_markdown(output_path, "Generate HTML / CSS / GSAP scene", "in_progress", f"Correcting validation errors (Attempt {attempts})")
        user_prompt = prompts.CODE_REFINE_PROMPT.format(
            validation_errors="\n".join([f"- {err}" for err in errors]),
            original_code=state["generated_code"]
        )
        
        messages = [
            SystemMessage(content=prompts.CODE_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
    else:
        print(f"\n--- [Code Generator Node] Attempt {attempts}: Generating Complete HTML ---")
        update_task_markdown(output_path, "Generate HTML / CSS / GSAP scene", "in_progress", f"Generating HTML (Attempt {attempts})")
        user_prompt = prompts.CODE_GENERATOR_USER_PROMPT.format(
            visual_plan_json=json.dumps(state["visual_plan"], indent=2),
            reference_template_excerpt=state["reference_template"]
        )
        
        messages = [
            SystemMessage(content=prompts.CODE_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]
        
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # Strip markdown wrappers
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n", "", content)
        content = re.sub(r"\n```$", "", content)
        content = content.strip()
        
    update_task_markdown(output_path, "Generate HTML / CSS / GSAP scene", "done", f"Code generated successfully (Attempt {attempts})")
    return {
        "generated_code": content,
        "generation_attempts": attempts,
        "validation_errors": []  # Reset for next validation check
    }

def validate(state: VisualPlannerState) -> Dict[str, Any]:
    """Performs rule-based checks on generated HTML."""
    output_path = Path(state.get("output_path", "scenes/ep_04_scene.html"))
    update_task_markdown(output_path, "Validate generated scene layout", "in_progress")
    
    print("--- [Validator Node] Running Rule-Based Checks ---")
    code = state.get("generated_code", "")
    scene_id = state.get("scene_id", "ep_04_scene")
    errors = []
    
    if not code:
        errors.append("Generated code is empty.")
        update_task_markdown(output_path, "Validate generated scene layout", "failed", "Generated code is empty.")
        return {"validation_errors": errors}
        
    # 1. Structural Checks
    if "<!DOCTYPE html>" not in code:
        errors.append("Missing <!DOCTYPE html> declaration.")
    if "</html>" not in code:
        errors.append("Missing </html> closing tag.")
    if "</body>" not in code:
        errors.append("Missing </body> closing tag.")
        
    # 2. Layout Elements Checks
    if 'id="caption-container"' not in code and "id='caption-container'" not in code:
        errors.append("Missing #caption-container element.")
    if 'id="face-frame"' not in code and "id='face-frame'" not in code:
        errors.append("Missing #face-frame element.")
    if 'id="canvas-bg"' not in code and "id='canvas-bg'" not in code:
        errors.append("Missing #canvas-bg element for background particles.")
        
    # 3. CDN Links
    if "cdnjs.cloudflare.com/ajax/libs/gsap/" not in code:
        errors.append("Missing GSAP library CDN reference.")
    if "fonts.googleapis.com/css2" not in code:
        errors.append("Missing Google Fonts link reference.")
        
    # 4. Captions Loading
    expected_captions_script = f'src="{scene_id}_captions.js"'
    expected_captions_script_single = f"src='{scene_id}_captions.js'"
    if expected_captions_script not in code and expected_captions_script_single not in code:
        errors.append(f"Missing external script source reference to captions file: {scene_id}_captions.js")
        
    # 5. Captions Object Referencing
    expected_captions_var = f"window.{scene_id}_captions"
    if expected_captions_var not in code:
        errors.append(f"Captions syncing code does not reference the correct captions object: {expected_captions_var}")
        
    # 6. time() wrapper shift function check
    if "const time" not in code and "function time" not in code:
        errors.append("Missing time() timestamp shift function.")
    else:
        # Check that it contains shifts
        if "9.5" not in code or "91.615" not in code or "10.0" not in code:
            errors.append("The time() function is missing necessary shift parameters (9.5s hook shift or 10.0s student speaking shift).")

    # Log results
    if errors:
        print(f"[Validation Failed] Found {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        update_task_markdown(output_path, "Validate generated scene layout", "failed", f"Failed: {', '.join(errors)}")
    else:
        print("[Validation Passed] HTML structure matches all layout constraints.")
        update_task_markdown(output_path, "Validate generated scene layout", "done", "Validation passed.")
        
    return {"validation_errors": errors}

def save_output(state: VisualPlannerState) -> Dict[str, Any]:
    """Saves final HTML, updates scenes.json, and generates JS captions."""
    print("--- [Saver Node] Saving Output Files ---")
    html_code = state["generated_code"]
    output_path = Path(state["output_path"])
    scene_id = state["scene_id"]
    
    update_task_markdown(output_path, "Save scene files & update configs", "in_progress")
    
    # 1. Save HTML scene
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"[Saved] Scene HTML file written to {output_path}")
    
    # 2. Save JS captions file dynamically
    alignment_path = Path(state["output_path"]).parent.parent / "timestamps" / "combined_alignment.json"
    if not alignment_path.exists():
        # fallback to the config alignment path
        alignment_path = Path("timestamps/combined_alignment.json")
        
    js_captions_path = output_path.parent / f"{scene_id}_captions.js"
    generate_captions_js(alignment_path, js_captions_path, scene_id)
    
    # 3. Save scenes.json metadata
    scenes_json_path = output_path.parent / "scenes.json"
    if not scenes_json_path.exists():
        scenes_json_path = Path("scenes/scenes.json")
        
    # Calculate duration
    duration = 144.623  # Fallback to known ep_04 length
    if state["alignment_data"].get("segments"):
        duration = state["alignment_data"]["segments"][-1]["end"]
        
    # Extract overlays timing from approved visual plan
    overlays = []
    plan_overlays = state["visual_plan"].get("overlays", [])
    for ov in plan_overlays:
        name = ov.get("type", "")
        # map layout details
        v_name = "start_hook.mp4" if "hook" in name.lower() else "student_speaking.mp4"
        overlays.append({
            "video": v_name,
            "insert_time": ov.get("start", 0.0),
            "duration": round(ov.get("end", 8.0) - ov.get("start", 0.0), 3),
            "padding_start": ov.get("padding_start", 0.0),
            "padding_end": ov.get("padding_end", 0.0),
            "position": {
                "x": 0, "y": 0, "w": 1080, "h": 1920
            }
        })
        
    # If no overlays in plan, write default ones for ep_04
    if not overlays:
        overlays = [
            {
                "video": "start_hook.mp4",
                "insert_time": 0.0,
                "duration": 8.0,
                "padding_start": 0.0,
                "padding_end": 1.5,
                "position": {"x": 0, "y": 0, "w": 1080, "h": 1920}
            },
            {
                "video": "student_speaking.mp4",
                "insert_time": 101.115,
                "duration": 8.0,
                "padding_start": 1.0,
                "padding_end": 1.0,
                "position": {"x": 0, "y": 0, "w": 1080, "h": 1920}
            }
        ]
        
    update_scenes_json(scenes_json_path, scene_id, duration, overlays)
    update_task_markdown(output_path, "Save scene files & update configs", "done", "Saved HTML, captions JS, and scenes.json")
    
    return {}
