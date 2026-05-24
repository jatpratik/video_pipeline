# AI Video Generation Pipeline - Project Context

This document outlines the architecture, flow, and components of the AI Video Generation Pipeline. Use this document as context when assisting with development, debugging, or extending the project.

## Overview
The pipeline is a hybrid automated/manual system that converts a narration script and audio file into a polished, vertical (1080×1920) video. It uses WhisperX for audio alignment, manual HTML/CSS/GSAP generation (via an AI coding assistant like Antigravity) for visuals, Playwright for headless rendering, and FFmpeg for final assembly.

**Core philosophy**: The system behaves like a human educator, not a cinematic generator. Primary goal: lowest cognitive load for the viewer.

## Technology Stack
- **Core Orchestration:** Python (with `argparse` for CLI subcommands).
- **Audio/Alignment:** `WhisperX` for forced alignment and word-level timestamps.
- **Frontend/Animation:** HTML, CSS, JavaScript (GSAP for animations).
- **Rendering:** Playwright (headless browser capture) and FFmpeg.

## Core Pipeline Steps (`main.py`)

1. **Step 1: Forced Alignment (`python main.py align`)**
   - Inputs: `input/voice.wav` and `input/script.txt`
   - Action: Runs WhisperX to generate exact word-level timestamps.
   - Output: `timestamps/alignment.json`

2. **Step 2: Visual Implementation (Manual / AI Assistant)**
   - Action: Using the generated alignment, an AI coding assistant (e.g., Antigravity) writes custom HTML/CSS/GSAP code for each scene. The user and AI reason over the script to divide it into scenes. 
   - Requirements: Output HTML files and update the `scenes.json` metadata in `scenes/` with duration and `scene_id`.
   - Output: `scenes/scenes.json` and a set of `.html` files for each scene.

3. **Step 3: Headless Rendering (`python main.py render`)**
   - Action: Loads the manually generated HTML scenes into a headless Playwright browser. Captures video.
   - Output: Individual `.mp4` clips for each scene in `rendered_scenes/`.

4. **Step 4: Video Assembly (`python main.py assemble`)**
   - Action: Uses FFmpeg to concatenate the rendered scene clips and overlay the original narration audio. Validates export.
   - Output: `output/final_video.mp4`

## Key Rules Enforced in Code (for Visual Generation)
- **One core idea per scene.** Viewer must understand within 1 second.
- **Motion must explain.** If static works better, do not animate.
- **Static rest state.** After animation completes, scene stabilises (no endless loops).
- **Complexity budget:** Max 1 teaching idea, 2 major objects, 8 visible words, 3 simultaneous motions per scene.
- **Top 55% safe area.** All important content inside top 1080×1056 of the 1080×1920 frame.
- **Relative timestamps only.** Never use abs_start — always relative to scene start.

## Directory Structure
- `input/`: Source files (`script.txt`, `voice.wav`).
- `output/`: The final generated video.
- `scripts/`: Implementation for pipeline steps (`step1_alignment.py`, `step4_render.py`, `step5_assembly.py`, `step6_export.py`).
- `scenes/`: Generated HTML scenes and `scenes.json`.
- `rendered_scenes/`: Intermediate `.mp4` scene clips.
- `timestamps/`: WhisperX alignment output.
- `config.py`: Central configuration (video specs, directories).
- `main.py`: The CLI entry point and main orchestrator.

## Configuration & Specs (`config.py`)
- **Video Format:** Vertical 1080×1920, 30 FPS.
- **Visual Rendering Area:** 1080×1056 (top 55% safe area).
- **Complexity Budget:** 1 idea, 2 objects, 8 words, 3 motions per scene.
- **Concurrency:** Supports parallel Playwright rendering (default batch size: 3).
