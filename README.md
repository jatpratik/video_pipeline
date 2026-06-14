# AI Video Generation Pipeline — User Guide

This pipeline converts a narration script, audio file, and co-host clips into a highly engaging, vertical (1080×1920) vertical video (Short/Reel). 

Visual elements are rendered headlessly from custom HTML/CSS/GSAP scenes, assembled with the narrator’s voice and face overlays, speed-adjusted, and finally merged with fullscreen co-host videos (hooks and student questions) with transition pauses and burned-in captions.

---

## 🚀 Core Workflow Step-by-Step

Follow these 8 steps for every new video:

### Step 1: Place Source Assets
1. Put your raw narration script in `input/script.txt` (only the presenter’s spoken lines).
2. Place the recorded/cloned voice audio in `input/voice.wav`.
3. Put the co-host videos in `input/start_hook.mp4` (intro) and `input/student_speaking.mp4` (middle question).

### Step 2: Run Audio Alignment
Align the narrator's voice to get word-level timestamps. This command automatically calculates the audio duration, updates `scenes/scenes.json`, and outputs the browser captions file `scenes/agent_scene_05_captions.js`:
```bash
python main.py align --scene agent_scene_05
```

### Step 3: Scaffold Visual HTML Template
Generate a pre-styled, vertical visual template matching the channel's metrics and ambient particle canvas. It will be pre-linked to the generated captions JS file:
```bash
python main.py scaffold --scene agent_scene_05
```

### Step 4: Develop Visual Animations
Open the newly created `scenes/agent_scene_05.html` in your editor. Build your visual elements and choreograph their entrance/exit transitions in the GSAP timeline (`tl`) using the `time(seconds)` helper relative to the narration script.

> [!TIP]
> Open the HTML file in a local browser. Use the **Spacebar** to play/pause the animations and numbers **1 to 6** to jump/seek to specific parts of the timeline for rapid manual previewing!

### Step 5: Headless Rendering
Record the visual scene animations into a silent `.mp4` visual clip:
```bash
python main.py render
```

### Step 6: Assemble Base Video
Stitch the visual clips with the narrator audio stream and overlay the circular face video in the bottom-left corner:
```bash
python main.py assemble
```
*Output: `output/final_video.mp4`*

### Step 7: Speed Up Video
Speed up the assembled video (visuals, captions, voice audio, and face overlay) using visually-lossless transcoding:
```bash
python main.py speed -s 1.25
```
*Output: `output/final_video_speed.mp4`*

### Step 8: Final Co-host Video Merge
1. Open `cohost_config.json` in the project root.
2. Verify the `speed` matches Step 7 (e.g. `1.25`), configure the `insert_time_original` where the question co-host video should insert (measured in the original unshifted narrator timeline), and add the subtitle captions text for the co-host's question.
3. Run the merge command:
```bash
python main.py merge -c cohost_config.json
```
*Output: `output/release_ready.mp4` (Final release-ready video)*

---

## 🛠️ Co-host Merge Config (`cohost_config.json`)

The merge tool reads `cohost_config.json` to insert hooks and question videos fullscreen. It clones video frames at start and end to create a clean pause before/after speaking:

```json
{
  "explanation_video": "output/final_video_speed.mp4",
  "output_video": "output/release_ready.mp4",
  "speed": 1.25,
  "cohosts": [
    {
      "name": "start_hook",
      "video_path": "input/start_hook.mp4",
      "insert_time_original": 0.0,
      "padding_start": 0.0,
      "padding_end": 0.5,
      "captions": []
    },
    {
      "name": "student_speaking",
      "video_path": "input/student_speaking.mp4",
      "insert_time_original": 91.615,
      "padding_start": 0.5,
      "padding_end": 0.5,
      "captions": [
        {
          "text": "Wait... if a system can write its own code and change its own structure,",
          "start": 0.5,
          "end": 4.5
        },
        {
          "text": "how do we keep it under control? What if it does something dangerous?",
          "start": 4.6,
          "end": 8.5
        }
      ]
    }
  ]
}
```

---

## 📐 Layout Standards & Metric Specifications

To maintain a consistent styling identity across daily Reels, all HTML template layout elements utilize fixed visual anchors:

1. **Visual Animation Canvas Area**
   - Coordinates: `top: 0px`, `left: 0px`, `width: 1080px`, `height: 1320px` (safely covers the top 70% of the canvas).
2. **Circle Face Overlay Area**
   - Coordinates: bottom-left `x: 60px, y: 1320px`.
   - HTML Placeholder Border: `left: 56px, top: 1316px, width: 408px, height: 408px` (matches circular crop diameter of `400px` plus a `4px` glowing cyan border).
3. **Captions Box Area**
   - Coordinates: bottom-right `right: 30px, top: 1320px, width: 550px, height: 400px`.
   - Style: Frosted dark background card (`rgba(8, 10, 20, 0.78)`) with Outfit font.
