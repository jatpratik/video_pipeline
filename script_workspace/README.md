# Scripting Workspace Guide

Welcome to the unified **Scripting Workspace**. This folder contains the curriculum and individual scripts for our educational AI shorts.

## Folder Directory & Architecture
- **`curriculums/`**: Contains curriculum JSON files tracking completion status.
  - [linear_algebra.json](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/curriculums/linear_algebra.json): Coordinates for the Linear Algebra series.
  - [agentic_ai.json](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/curriculums/agentic_ai.json): Outline for the Agentic AI Design Patterns series.
  - [channel_meta.json](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/curriculums/channel_meta.json): Tracking file for channel-level intro and roadmap videos.
- **`episodes/`**: Subdivided by series to store the "Learn-First" Markdown files.
  - `channel_meta/`: Introductory/meta-level videos outlining channel scope (e.g., [ep_00_channel_intro_roadmap.md](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/episodes/channel_meta/ep_00_channel_intro_roadmap.md)).
  - `linear_algebra/`: Episodes for Linear Algebra (e.g., [ep_01_dot_product.md](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/episodes/linear_algebra/ep_01_dot_product.md)).
  - `agentic_ai/`: Episodes for Agentic AI (e.g., [ep_01_intro.md](file:///e:/my-workspace/content_design/video_pipeline/script_workspace/episodes/agentic_ai/ep_01_intro.md)).
- **`assets/`**: Stores gathered diagrams, charts, and media references.
  - `channel_meta/`, `linear_algebra/` & `agentic_ai/`

---

## Series Workflows
We use slightly different workflows depending on the series:

- **Channel Meta (Roadmap & Intro)**:
  These files contain a Study Guide explaining the strategic channel vision/concept mapping, and the Video Script for production.

- **Linear Algebra for AI (Learn-First Workflow)**:
  Because you are presenting these reels as an AI educator, it is critical that you have a deep, intuitive grasp of the mathematics before recording. Therefore, these files contain two parts:
  1. **PART 1: THE STUDY GUIDE (For You)**: Conversational explanation of mathematical intuition, geometric meaning, and PyTorch/FAISS code implementations.
  2. **PART 2: THE VIDEO SCRIPT (For Production)**: The 45-60s script with hook, body, and Maya co-host question.
  
- **Agentic AI Design Patterns**:
  Since you already have a deep understanding of the textbook *Agentic Design Patterns*, we skip the study guide. These files contain **only the Video Script** (optimized for production).

---

## Maya Co-Host Conventions
Our co-host **Maya** is a permanent fixture. She appears in a picture-in-picture card (`student_speaking.mp4`) positioned at `x: 140, y: 140, w: 800, h: 1160`.
- **Duration**: Dynamic, but always between **6 and 10 seconds** (defaulting to 9.0s).
- **Time Offset**: Injected after the first core teaching phase (typically around 55s - 65s).
- **Tone**: Professional, advanced engineer.
- **Topics**: Maya only asks implementation, scaling, failure, and optimization questions.

---

## How to Work with Antigravity to Generate Scripts

You can direct me using these commands in your chat (always specify the series `linear_algebra` or `agentic_ai`):

1. **"Draft Episode [Number] for [Series]"**: Generates the episode in the series' folder (both Study Guide + Script for `linear_algebra`, and Script-only for `agentic_ai`).
2. **"Review Curriculum for [Series]"**: Shows the current status of all episodes in that specific curriculum.
3. **"Gather Assets for Episode [Number] in [Series]"**: Performs web searches for educational illustrations, downloads them to `assets/[Series]/`, and provides advice on rendering them in HTML.
4. **"Verify/Align Script [Number] in [Series]"**: Checks script length, word counts, and timings to fit under the target short-video thresholds.

