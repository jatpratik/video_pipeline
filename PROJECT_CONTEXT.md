# AI Video Generation Pipeline - Project Context

This document outlines the architecture, flow, and components of the AI Video Generation Pipeline. Use this document as context when assisting with development, debugging, or extending the project.

## AI Educator Channel Mission & Monetization Goal
- **Mission:** Create educational short-form vertical videos (YouTube Shorts/Reels) explaining AI concepts, math for AI, autonomous agents, and system architecture.
- **Goal:** Drive user engagement to monetize the YouTube channel by posting daily, high-quality explanation videos.
- **Progress:** Completed 2 Reels successfully (Reel 1: Prompt Chaining, Reel 2: Structured Outputs).
- **Strategy:** The next 10 reels must strictly adhere to the same styling conventions, layout metrics, and high-quality FFmpeg overlay flow established here.

## Core Design Conventions for Future Reels
1. **Vertical 9:16 Mobile Aspect Ratio:** 1080 × 1920 viewport.
2. **Full Screen Visualization:** Visual animations use 100% of the screen space.
3. **Presenter Face Overlay (FFmpeg-driven):**
   - Presenter's face is circle-cropped (`diameter: 400px`) and overlaid at the bottom-left corner (`x: 80, y: 1440`).
   - Do NOT embed face `<video>` tags or circle placeholder markup inside HTML templates. Headless rendering should output a clean visual canvas.
   - FFmpeg assembly script handles the face overlay, applying smartblur skin smoothing, unsharp detail sharpening, vibrance boost, Mobius tonemapping, and BT.709 colorspace.
4. **Student Speaking Question Overlay (PiP Card):**
   - When a question is asked, a picture-in-picture student video (`student_speaking.mp4`) card overlays the main visual space at coordinates `x: 140, y: 140, w: 800, h: 1160`.
   - Card border, headers, and shadow overlays are handled by HTML/CSS and animated in/out with GSAP (typically for the 8s to 10s question duration).
   - Audio is paused/split automatically by the assembly script during this window, and the face circle is hidden.
5. **Caption Wrapping & Formatting:**
   - Word blocks wrap dynamically to prevent clipping on mobile screens (`flex-wrap: wrap; justify-content: center;`).
   - Captions are positioned safely above the face circle overlay (`bottom: 520px` or `margin-bottom: 540px`).

## Overview
The pipeline is a hybrid automated/manual system that converts a narration script and audio file into a polished, vertical (1080×1920) video. It uses WhisperX for audio alignment, manual HTML/CSS/GSAP generation (via an AI coding assistant like Antigravity) for visuals, Playwright for headless rendering, and FFmpeg for final assembly.

**Core philosophy**: The system behaves like a human educator, not a cinematic generator. Primary goal: lowest cognitive load for the viewer.

## Technology Stack
- **Core Orchestration:** Python (with `argparse` for CLI subcommands).
- **Audio/Alignment:** `WhisperX` for forced alignment and word-level timestamps.
- **Frontend/Animation:** HTML, CSS, JavaScript (GSAP for animations).
- **Rendering:** Playwright (headless browser capture) and FFmpeg.


**TECH STACK for visuals design used by antigravity**:  
- Three.js – for 3D pipeline / chain visuals (optional, keep simple if needed)  
- GSAP – master timeline for all animations  
- Canvas API – for code blocks, JSON rendering, parsing chaos effects  
- tsParticles – for “broken pipeline” particle bursts  
- D3.js (optional, only for simple graph of validators/retries)  
- CSS glitch / shake effects – for formatting errors 

## Core Pipeline Steps (`main.py`)

1. **Step 1: Forced Alignment & Auto-Captions (`python main.py align [--scene SCENE_ID]`)**
   - Inputs: `input/voice.wav` and `input/script.txt`
   - Action: Runs WhisperX to align narration audio. Auto-probes audio duration, automatically writes/updates `scenes/scenes.json`, and writes a browser-ready JS captions array (e.g. `scenes/agent_scene_05_captions.js`).
   - Output: `timestamps/alignment.json`, updated `scenes/scenes.json`, and `scenes/<scene_id>_captions.js`

2. **Step 2: Visual Scaffolding (`python main.py scaffold [--scene SCENE_ID]`)**
   - Action: Scaffolds a new visual HTML file (e.g. `scenes/agent_scene_05.html`) based on standard layout coordinates, fonts, face overlays, caption areas, and particle loops of previous episodes.
   - Output: Visual boilerplate template in `scenes/<scene_id>.html`

3. **Step 3: Visual Implementation (Manual / AI Assistant)**
   - Action: Code custom visual divs and timeline animations inside the visuals area of the generated HTML scene file.
   - Output: Completed visual animation HTML file.

4. **Step 4: Headless Rendering (`python main.py render`)**
   - Action: Loads the manually finished HTML scenes in Playwright Chromium. Records visual animations.
   - Output: Silent `.mp4` visual clips in `rendered_scenes/`.

5. **Step 5: Video Assembly (`python main.py assemble`)**
   - Action: Combines silent visual clips and narration audio, and overlays the presenter's face circle.
   - Output: Assembled base video in `output/final_video.mp4`

6. **Step 6: Speed Adjustment (`python main.py speed -s MULTIPLIER`)**
   - Action: Speeds up the base video (both video, audio, and captions) using visual-lossless transcoding.
   - Output: Speed-adjusted video in `output/final_video_speed.mp4`

7. **Step 7: Co-host Video Merging (`python main.py merge [-c cohost_config.json]`)**
   - Action: Reads the merge configurations, splices the speed-adjusted video, inserts full-screen co-host clips (hook, student questions) with smooth cloned-frame padding transitions, and burns styled co-host captions.
   - Output: Release-ready video in `output/release_ready.mp4`

## Directory Structure
- `input/`: Narration files (`script.txt`, `voice.wav`) and co-host clips (`start_hook.mp4`, `student_speaking.mp4`).
- `output/`: Generated output video files (`final_video.mp4`, `final_video_speed.mp4`, and `release_ready.mp4`).
- `scripts/`: Python orchestrators (`step1_alignment.py`, `step4_render.py`, `step5_assembly.py`, `step6_export.py`, `adjust_speed.py`, `merge_cohost.py`, `scaffold.py`).
- `scenes/`: Generated HTML scenes, `.js` captions files, and `scenes.json`.
- `rendered_scenes/`: Intermediate visual `.mp4` scene clips.
- `timestamps/`: WhisperX forced alignment outputs.
- `config.py`: Central configuration variables.
- `cohost_config.json`: Configuration settings for the co-host merging process.
- `main.py`: The unified CLI entry point.