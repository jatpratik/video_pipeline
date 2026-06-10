# e:/my-workspace/content_design/video_pipeline/visual_agents/state.py

from typing import TypedDict, List, Dict, Any, Optional

class VisualPlannerState(TypedDict):
    # Identifiers
    episode_id: str                      # e.g., 'ep_04'
    scene_id: str                        # e.g., 'ep_04_scene'
    
    # Inputs
    script_text: str                     # Full episode script markdown
    alignment_data: Dict[str, Any]       # parsed combined_alignment.json
    scene_config: Dict[str, Any]         # parsed scenes.json entry
    reference_template: str              # reference html layout constraints
    
    # Planning
    visual_plan: Dict[str, Any]          # Structured JSON visual plan
    plan_approved: bool                  # HITL approval flag
    human_feedback: str                  # HITL feedback text
    human_assets: List[str]              # User-provided asset paths or descriptions
    
    # Code Generation
    generated_code: str                  # Full HTML output
    validation_errors: List[str]         # Validator error messages
    generation_attempts: int             # Retry counter (max 3)
    
    # Refinement Loop (caption line matching)
    refinement_mode: bool                # True if we are in code refinement mode based on browser feedback
    refinement_caption_line: str         # The caption line text user wants to change
    refinement_feedback: str             # Instructions on what change to make at that line
    
    # Output
    output_path: str                     # Final saved file path
