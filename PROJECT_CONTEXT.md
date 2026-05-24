# AI Video Generation Pipeline - Project Context

This document outlines the architecture, flow, and components of the Phase 3 Multi-Agent AI Video Generation Pipeline. Use this document as context when assisting with development, debugging, or extending the project.

## Overview
The pipeline is a fully automated, educational multi-agent system that converts a narration script and audio file into a polished, vertical (1080×1920) video. It uses WhisperX for audio alignment, a 7-phase LLM reasoning pipeline for visual conceptualization and code generation, Playwright for headless rendering and asset retrieval, and FFmpeg for final assembly.

**Core philosophy**: The system behaves like a human educator, not a cinematic generator. Primary goal: lowest cognitive load for the viewer.

## Technology Stack
- **Core Orchestration:** Python (with `argparse` for CLI, modular structure).
- **Audio/Alignment:** `WhisperX` for forced alignment and word-level timestamps.
- **LLM/Agents:** OpenAI API (`gpt-4o`) via custom orchestrator.
- **Frontend/Animation:** HTML, CSS, JavaScript (GSAP for animations).
- **Asset Retrieval:** DuckDuckGo (default), SerpAPI, or Google Custom Search + Playwright screenshots.
- **Rendering:** Playwright (headless browser capture) and FFmpeg.

## Core Pipeline Steps (`main.py`)

1. **Step 1: Forced Alignment**
   - Inputs: `input/voice.wav` and `input/script.txt`
   - Action: Runs WhisperX to generate exact word-level timestamps.
   - Output: `timestamps/alignment.json`

2. **Step 2: Multi-Agent Visual Reasoning (`agents/orchestrator.py`)**
   A 7-phase architecture that translates the script into visual scenes:

   - **Phase 1 — Script Understanding** (`agent_script_understanding.py`)
     Analyzes the script for themes, teaching goals, difficult concepts, visual metaphors, and educational patterns. Merges old concept + research agents into a single LLM call.

   - **Phase 2 — Visual Reasoning** (`agent_visual_reasoner.py`)
     Chooses visual strategies dynamically from a toolbox (story, diagram, metaphor, UI, kinetic text, comparison, etc.). Outputs a narration-to-visual map with exact text spans and timings. NO rigid hierarchy — the best strategy is chosen per segment.

   - **Phase 2.5 — Asset Retrieval** (`asset_retriever.py`)
     For segments needing real images (diagram_flow, metaphor_animation, ui_mockup, etc.), searches the web using DuckDuckGo, SerpAPI, or Google CSE. Takes screenshots via Playwright and stores them in `assets/`. Falls back to CSS/SVG if no image found.

   - **Phase 3 — Human Review** (hybrid CLI + file)
     Stops the pipeline, presents the visual map with proposed images to the user. The user can edit `timestamps/visual_map.json` directly and then type `approve` or `reject` in the CLI.

   - **Phase 4 — Scene Structuring** (`agent_scene_structurer.py`)
     Converts the approved visual map into concrete scene specifications with pixel-precise layouts, animation choreography, and complexity budget verification.

   - **Phase 5 — Visual Implementation** (`agent_frontend.py` + `agent_critic.py`)
     Generates HTML/CSS/GSAP code for each scene. The critic reviews with 1 retry max. Enforces complexity budget, static rest state, and educational constraints.

   - Output: `scenes/scenes.json` and a set of `.html` files for each scene.

3. **Step 3: Headless Rendering**
   - Action: Loads the generated HTML scenes into a headless Playwright browser. Captures video with precise synchronization to the timestamps.
   - Output: Individual `.mp4` clips for each scene in `rendered_scenes/`.

4. **Step 4: Video Assembly**
   - Action: Uses FFmpeg to concatenate the rendered scene clips and overlay the original narration audio.
   - Output: `output/final_video.mp4`

5. **Step 5: Export Validation**
   - Action: Verifies the final video's resolution (1080×1920), framerate (30fps), duration, and audio sync.
   - Output: Final success/failure logs.

## Key Rules Enforced in Code
- **One core idea per scene.** Viewer must understand within 1 second.
- **Motion must explain.** If static works better, do not animate.
- **Static rest state.** After animation completes, scene stabilises (no endless loops).
- **Complexity budget:** Max 1 teaching idea, 2 major objects, 8 visible words, 3 simultaneous motions per scene.
- **Top 55% safe area.** All important content inside top 1080×1056 of the 1080×1920 frame.
- **Relative timestamps only.** Never use abs_start — always relative to scene start.

## Directory Structure
- `agents/`: Multi-agent reasoning system.
  - `agent_script_understanding.py`: Phase 1 — script analysis.
  - `agent_visual_reasoner.py`: Phase 2 — visual strategy selection.
  - `asset_retriever.py`: Phase 2.5 — web search + screenshot.
  - `agent_scene_structurer.py`: Phase 4 — scene structuring.
  - `agent_frontend.py`: Phase 5 — HTML/CSS/GSAP code generation.
  - `agent_critic.py`: Phase 5 — code review with retry.
  - `orchestrator.py`: Main pipeline coordinator.
  - `design_system.py`: Visual identity and complexity budget.
  - `visual_patterns.py`: Reusable visual composition patterns.
  - `llm_client.py`: Shared OpenAI wrapper.
  - `_archive/`: Superseded agents from Phase 2 architecture.
- `input/`: Source files (`script.txt`, `voice.wav`).
- `output/`: The final generated video.
- `assets/`: Downloaded images and screenshots from asset retrieval.
- `scripts/`: Implementation for pipeline steps (alignment, rendering, assembly, export).
- `scenes/`: Generated HTML scenes and `scenes.json`.
- `rendered_scenes/`: Intermediate `.mp4` scene clips.
- `timestamps/`: WhisperX alignment output, visual map, and agent checkpoints.
- `templates/`: Legacy HTML templates (from Phase 1).
- `config.py`: Central configuration (video specs, models, directories, complexity budget).
- `main.py`: The CLI entry point and main orchestrator.

## Configuration & Specs (`config.py`)
- **Video Format:** Vertical 1080×1920, 30 FPS.
- **Visual Rendering Area:** 1080×1056 (top 55% safe area).
- **Complexity Budget:** 1 idea, 2 objects, 8 words, 3 motions per scene.
- **Concurrency:** Supports parallel Playwright rendering (default batch size: 3).
- **Models:** Default WhisperX model `large-v3-turbo`, Default LLM `gpt-4o`.
- **Search:** DuckDuckGo (default), configurable to SerpAPI or Google CSE.
- **Critic Retries:** Max 1 retry per scene.
