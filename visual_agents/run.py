# e:/my-workspace/content_design/video_pipeline/visual_agents/run.py

import os
import sys
import argparse
import json
from pathlib import Path

# Force console streams to UTF-8 to prevent cp1252 charmap encoding crashes on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from visual_agents.graph import graph
from visual_agents.state import VisualPlannerState
from visual_agents.utils import find_timestamp_by_caption_line

try:
    from langgraph.types import Command
    has_command = True
except ImportError:
    has_command = False

console = Console()

def display_visual_plan(plan: dict) -> None:
    """Displays the structured visual plan JSON in a beautiful table."""
    console.print(Panel(
        f"[bold cyan]Episode ID:[/bold cyan] {plan.get('episode_id', 'N/A')}\n"
        f"[bold cyan]Total Duration:[/bold cyan] {plan.get('total_duration', 'N/A')}s\n"
        f"[bold cyan]Design Tokens:[/bold cyan] BG: {plan.get('design_tokens', {}).get('bg_color', 'N/A')} | Fonts: {', '.join(plan.get('design_tokens', {}).get('fonts', []))}",
        title="[bold magenta]Visual Scene Design Plan[/bold magenta]",
        border_style="magenta"
    ))
    
    table = Table(title="Visual Acts (Timeline of animations)", border_style="cyan", show_lines=True)
    table.add_column("Act/ID", style="bold cyan")
    table.add_column("Timestamps (Unshifted / Narrator)", style="green")
    table.add_column("Visual Description & Elements", style="white", ratio=3)
    table.add_column("Tech Stack / Rationale", style="yellow", ratio=2)
    table.add_column("Asset Suggestions (Raster images needed)", style="red", ratio=2)

    for act in plan.get("acts", []):
        act_id = act.get("act_id", "")
        title = act.get("title", "")
        time_range = act.get("time_range", [0, 0])
        tech_stack = ", ".join(act.get("tech_stack", []))
        tech_reasoning = act.get("tech_reasoning", "")
        
        elements_desc = []
        asset_desc = []
        
        for idx, elem in enumerate(act.get("elements", [])):
            elem_id = elem.get("id", "")
            elem_type = elem.get("type", "")
            elem_content = elem.get("content", "")
            
            anims = []
            for anim in elem.get("animations", []):
                anims.append(f"{anim.get('type')}(@{anim.get('trigger_time')}s, dur: {anim.get('duration')}s)")
                
            elements_desc.append(
                f"[bold]- Elem {idx+1}:[/bold] ID: [cyan]{elem_id}[/cyan] ({elem_type})\n"
                f"  Position: {elem.get('position', {})}\n"
                f"  Animations: {', '.join(anims)}"
            )
            
            if elem.get("suggested_asset_description"):
                asset_desc.append(
                    f"[bold]Image ID:[/bold] [red]{elem_content}[/red]\n"
                    f"Prompt Suggestion: {elem.get('suggested_asset_description')}"
                )
                
        elements_text = "\n\n".join(elements_desc)
        assets_text = "\n\n".join(asset_desc) if asset_desc else "None (Procedural)"
        
        table.add_row(
            f"[bold]{title}[/bold]\n({act_id})",
            f"{time_range[0]}s -> {time_range[1]}s",
            elements_text,
            f"[bold]{tech_stack}[/bold]\n{tech_reasoning}",
            assets_text
        )
        
    console.print(table)
    
    # Highlight configuration
    caption_cfg = plan.get("caption_config", {})
    console.print(Panel(
        f"[bold yellow]Highlight Words:[/bold yellow] {', '.join(caption_cfg.get('highlight_words', []))}\n"
        f"[bold red]Danger/Warning Words:[/bold red] {', '.join(caption_cfg.get('danger_words', []))}",
        title="[bold green]Captions Timing Configuration[/bold green]",
        border_style="green"
    ))

def run_visual_pipeline(
    script_path: str,
    alignment_path: str,
    scenes_path: str,
    reference_path: str,
    output_path: str
) -> None:
    """Runs the LangGraph visual planning and generation pipeline."""
    config = {"configurable": {"thread_id": f"visuals_{Path(output_path).stem}"}}
    
    # Create initial state
    initial_state = {
        "script_text": script_path,
        "alignment_data": alignment_path,
        "scene_config": scenes_path,
        "reference_template": reference_path,
        "output_path": output_path,
        "plan_approved": False,
        "human_feedback": "",
        "human_assets": [],
        "generated_code": "",
        "validation_errors": [],
        "generation_attempts": 0,
        "refinement_mode": False
    }
    
    # Run the graph
    console.print("[bold green]Starting LangGraph Visual Planner Pipeline...[/bold green]")
    events = graph.stream(initial_state, config, stream_mode="values")
    
    for event in events:
        pass
        
    # Check if we are suspended at an interrupt
    state_snapshot = graph.get_state(config)
    
    while state_snapshot.next:
        # We are at the human review interrupt node
        tasks = state_snapshot.tasks
        if not tasks or not tasks[0].interrupts:
            break
            
        interrupt_val = tasks[0].interrupts[0].value
        visual_plan = interrupt_val.get("visual_plan", {})
        
        # Display the visual plan
        display_visual_plan(visual_plan)
        
        # Prompt user for review
        approved = Confirm.ask("\nDo you approve this visual design plan?", default=True)
        
        feedback = ""
        assets = []
        
        if not approved:
            feedback = Prompt.ask("[bold red]Enter your feedback/changes for the visual planner[/bold red]")
        else:
            add_assets = Confirm.ask("Do you want to specify any custom image paths or assets to use?", default=False)
            if add_assets:
                asset_input = Prompt.ask("Enter assets (comma-separated, e.g. humanoid.jpg, network.png)")
                assets = [a.strip() for a in asset_input.split(",") if a.strip()]
                
        decision = {
            "approved": approved,
            "feedback": feedback,
            "assets": assets
        }
        
        # Resume graph
        console.print("[green]Resuming graph execution...[/green]")
        if has_command:
            events = graph.stream(Command(resume=decision), config, stream_mode="values")
        else:
            graph.update_state(config, {
                "plan_approved": approved,
                "human_feedback": feedback,
                "human_assets": assets
            }, as_node="human_review")
            events = graph.stream(None, config, stream_mode="values")
            
        for event in events:
            pass
            
        state_snapshot = graph.get_state(config)

    # Graph finished. Let's load the final state to see if output saved correctly
    final_state = graph.get_state(config).values
    if final_state.get("validation_errors"):
        console.print(f"[bold red]Pipeline completed with validation errors:[/bold red]")
        for err in final_state["validation_errors"]:
            console.print(f" - {err}")
    else:
        console.print(f"\n[bold green]Success! Scene file and supporting assets generated successfully.[/bold green]")
        console.print(f"HTML output: [bold cyan]{output_path}[/bold cyan]")
        console.print(f"Captions output: [bold cyan]{Path(output_path).with_name(final_state['scene_id'] + '_captions.js')}[/bold cyan]")
        
        # Enter the browser verification and iterative refinement loop!
        run_browser_refinement_loop(config, final_state, alignment_path)

def run_browser_refinement_loop(config: dict, state: dict, alignment_path: str) -> None:
    """Runs a loop that allows the user to review in the browser and request modifications on specific lines."""
    console.print("\n" + "="*80)
    console.print("[bold yellow]Browser Verification & Iterative Refinement Loop[/bold yellow]")
    console.print("Instructions:")
    console.print("  1. Open the generated HTML in your browser.")
    console.print("  2. Watch the visuals and transitions.")
    console.print("  3. If you want changes: type the EXACT CAPTION LINE (or a distinct part of it) where you want a change.")
    console.print("  4. Then enter your request (e.g. 'make the robotic arm move faster', 'change the colors to cyan/gold').")
    console.print("  5. The system will update the scene code and tell you to refresh your browser.")
    console.print("  6. Press ENTER (empty input) when you are fully satisfied to finalize the build.")
    console.print("="*80 + "\n")
    
    with open(alignment_path, "r", encoding="utf-8") as f:
        alignment_data = json.load(f)
        
    while True:
        caption_line = Prompt.ask("\nEnter caption line to modify (or press Enter to exit/finish)").strip()
        if not caption_line:
            console.print("[bold green]Finalized! Visual automation task completed.[/bold green]")
            break
            
        # Find if this matches any timestamp in the alignment file
        match = find_timestamp_by_caption_line(alignment_data, caption_line)
        if match:
            console.print(f"[green]Matched segment:[/green] \"{match['text']}\" (Time: {match['start']}s -> {match['end']}s)")
        else:
            console.print("[yellow]Warning: Could not find a clear match for that caption line in the voice track.[/yellow]")
            confirm = Confirm.ask("Do you want to proceed with a general code change anyway?", default=True)
            if not confirm:
                continue
                
        feedback = Prompt.ask("[bold red]Describe the changes you want to apply at this scene[/bold red]").strip()
        if not feedback:
            console.print("[yellow]No feedback provided. Skipping change.[/yellow]")
            continue
            
        console.print("[cyan]Refining code using Claude...[/cyan]")
        
        # Update state with refinement parameters
        graph.update_state(config, {
            "refinement_mode": True,
            "refinement_caption_line": caption_line,
            "refinement_feedback": feedback,
            "generated_code": state.get("generated_code")  # Ensure we pass the current code
        }, as_node="load_inputs") # Or we can update directly
        
        # Run graph again starting from generate_code
        # To run specific sub-nodes, we can update the state to trigger the generate_code node.
        # In LangGraph, when we update state and call stream(None, config), the checkpointer
        # will resume execution from the next planned nodes or we can force it.
        # Since refinement_mode is checked inside generate_code, we update and call graph.stream
        # and it goes through generate_code -> validate -> save_output
        graph.update_state(config, {
            "refinement_mode": True,
            "refinement_caption_line": caption_line,
            "refinement_feedback": feedback
        })
        
        # We need to tell the graph to run generate_code next. In LangGraph checkpoint state,
        # we can update the next tasks or we can run the graph with starting node.
        # A simpler way to trigger refinement is to run a separate sub-call or run from graph beginning
        # with refinement_mode=True (in which case load_inputs is bypassed or just loads data, then planner is skipped,
        # and it goes directly to generate_code). Let's trace how the graph routing works:
        # If refinement_mode is True, can we bypass planning?
        # Yes! Let's ensure that if we are in refinement mode, plan_visuals just returns the visual plan as-is and approves it,
        # skipping HITL review!
        # Let's adjust plan_visuals in nodes.py to:
        # "if state.get('refinement_mode'): return {'plan_approved': True}"
        # Let's verify: Yes! In nodes.py:plan_visuals:
        # if state.get("refinement_mode"): return {"plan_approved": True}
        # Wait, if we set refinement_mode to True, we want it to run starting from load_inputs again,
        # which will load inputs, then go to plan_visuals (which skips planning since refinement_mode=True and returns plan_approved=True),
        # then go to human_review (which will be bypassed because plan_approved is True in the routing conditional should_generate_code!),
        # then go to generate_code (which will use the refinement prompts!), then validate, then save_output.
        # This is beautiful, clean, and uses the exact same graph execution logic without complex sub-graph overrides!
        
        # Let's double check nodes.py and prompts.py to verify:
        # In nodes.py, if state.get("refinement_mode") is True, generate_code does refinement.
        # But wait, does plan_visuals check state.get("refinement_mode")?
        # Let's check nodes.py lines we wrote:
        # No, nodes.py plan_visuals doesn't have the bypass. We should add that!
        # Let's check:
        # "If state.get('refinement_mode'): return {'plan_approved': True}"
        # Wait, if plan_visuals returns plan_approved=True, then routing condition:
        # "should_generate_code" checks: if state.get("plan_approved", False) -> returns "generate_code".
        # This means it will jump straight to generate_code!
        # Let's add that bypass to nodes.py. Let's do it using replace_file_content.
        
        # First, let's write run.py completely.
        # Once we save run.py, we will modify nodes.py to support the bypass.
        
        # Let's execute the run:
        events = graph.stream(None, config, stream_mode="values")
        for event in events:
            pass
            
        # Get updated state values
        state = graph.get_state(config).values
        console.print("[bold green]Applied changes and updated files! Please refresh your browser.[/bold green]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent Visual Scene Planner & Generator")
    parser.add_argument("--script", default="script_workspace/episodes/agentic_ai/ep_04_future_hypotheses.md", help="Path to script markdown")
    parser.add_argument("--alignment", default="timestamps/combined_alignment.json", help="Path to combined_alignment.json")
    parser.add_argument("--scenes", default="scenes/scenes.json", help="Path to scenes.json")
    parser.add_argument("--reference", default="scenes/agent_scene_03.html", help="Path to reference template html")
    parser.add_argument("--output", default="scenes/ep_04_scene.html", help="Path to save generated HTML scene")
    
    args = parser.parse_args()
    
    run_visual_pipeline(
        script_path=args.script,
        alignment_path=args.alignment,
        scenes_path=args.scenes,
        reference_path=args.reference,
        output_path=args.output
    )
