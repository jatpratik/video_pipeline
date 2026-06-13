# Episode 05: Why Single Prompts Fail

- **Target Duration**: 75 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 50.0s - 60.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"Ever asked an AI to do five things at once… and it forgot half of them? Today you'll learn why that happens — and the simple trick to fix it."

**Presenter:**
"Okay, picture this. You give an AI one big prompt: 'Read this market report. Summarize it. Find the top three trends with numbers. And write an email to the team.'

Four tasks. One prompt. What happens?

The summary? Pretty good. The trends? It missed one. The email? It forgot the data completely.

Why? Because one prompt is too much. The AI gets confused. It forgets instructions. It loses track halfway. And sometimes? It just makes stuff up.

So here's the fix. Don't give it one big task. Break it into small steps.

Step one — just summarize the report. That's it.
Step two — take that summary and pull out the trends with numbers.
Step three — take those trends and write the email.

Each step does one job. And the result of each step feeds into the next one. Like a factory line — one worker, one job, pass it forward.

This is called Prompt Chaining. And it changes everything."

**Riya (Question Overlay at 50.0s - 60.0s):**
"Okay, but what if step one gives a messy answer? Won't that mess up step two also? How do we keep the data clean between steps?"

**Presenter:**
"Smart question. So here's what we do — we don't let the AI write freely. We say: give me the answer in JSON format. A fixed structure.

So instead of messy paragraphs, you get something like: trend name, supporting data — clean and organized. The next step reads it directly. No confusion.

Clean in, clean out. That's the rule.

Next up — real-world use cases of prompt chaining. Subscribe!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows a dark grid with faint prompt text scrolling. | Riya: "Ever asked an AI to do five things..." |
| **10.0s - 22.0s** | **[The Problem]** Riya's card fades. Presenter's face circle appears. A giant single prompt box appears on screen with four highlighted tasks crammed inside. Red warning icons appear next to "Extract Data" and "Draft Email" — showing they failed. | Presenter: "Okay, picture this..." |
| **22.0s - 32.0s** | **[Prompt Overload]** The single prompt box cracks and breaks apart. Labels fly out: "Forgot Instructions", "Lost Track", "Made Stuff Up". Each label pulses red. | Presenter: "Why? Because one prompt is too much..." |
| **32.0s - 50.0s** | **[The Chain Solution]** Three clean, small prompt boxes line up left-to-right connected by glowing arrows. Box 1: "Summarize" → Box 2: "Find Trends" → Box 3: "Write Email". Each box lights up green as it completes. A factory assembly line animation runs underneath. | Presenter: "So here's the fix..." |
| **50.0s - 60.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background chain animations freeze. Presenter's face circle is hidden. | Riya: "Okay, but what if step one gives..." |
| **60.0s - 70.0s** | **[Structured JSON]** Riya's card fades. Presenter's face circle reappears. Show a clean JSON object on screen: `{"trends": [{"trend_name": "AI Personalization", "supporting_data": "73% prefer..."}]}`. An arrow feeds it into the next prompt box which lights up green. | Presenter: "Smart question. So here's what we do..." |
| **70.0s - 75.0s** | **[Outro / Subscribe]** The chain zooms out showing the full three-step pipeline with green checkmarks. Text overlay: "Next: Prompt Chaining in Practice" with a pulsing subscribe button. | Presenter: "Next up — real-world use cases..." |
