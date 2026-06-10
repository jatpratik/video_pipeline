# e:/my-workspace/content_design/video_pipeline/visual_agents/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import VisualPlannerState
from .nodes import load_inputs, plan_visuals, human_review, generate_code, validate, save_output

# Define routing functions
def should_generate_code(state: VisualPlannerState) -> str:
    """Routes after human review node based on approval."""
    if state.get("plan_approved", False):
        return "generate_code"
    return "plan_visuals"

def check_validation_results(state: VisualPlannerState) -> str:
    """Routes after validator node based on error presence and attempt count."""
    errors = state.get("validation_errors", [])
    attempts = state.get("generation_attempts", 0)
    
    if errors and attempts < 3:
        print(f"[Retry] Validator found errors. Retrying code generation (Attempt {attempts + 1}/3)...")
        return "generate_code"
        
    if errors:
        print("[Warning] Max retries reached. Saving generated code despite validation errors.")
        
    return "save_output"

# Build StateGraph
builder = StateGraph(VisualPlannerState)

# Add Nodes
builder.add_node("load_inputs", load_inputs)
builder.add_node("plan_visuals", plan_visuals)
builder.add_node("human_review", human_review)
builder.add_node("generate_code", generate_code)
builder.add_node("validate", validate)
builder.add_node("save_output", save_output)

def should_review_plan(state: VisualPlannerState) -> str:
    """Routes after plan_visuals: review plan unless in refinement mode."""
    if state.get("refinement_mode", False):
        return "generate_code"
    return "human_review"

# Add Edges
builder.add_edge(START, "load_inputs")
builder.add_edge("load_inputs", "plan_visuals")

# Conditional edge after plan_visuals
builder.add_conditional_edges(
    "plan_visuals",
    should_review_plan,
    {
        "generate_code": "generate_code",
        "human_review": "human_review"
    }
)

# Conditional edge after human review
builder.add_conditional_edges(
    "human_review",
    should_generate_code,
    {
        "generate_code": "generate_code",
        "plan_visuals": "plan_visuals"
    }
)

builder.add_edge("generate_code", "validate")

# Conditional edge after validator
builder.add_conditional_edges(
    "validate",
    check_validation_results,
    {
        "generate_code": "generate_code",
        "save_output": "save_output"
    }
)

builder.add_edge("save_output", END)

# Compile graph with MemorySaver checkpointer for human interrupts
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
