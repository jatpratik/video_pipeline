# Episode 05: Why Single Prompts Fail

- **Target Duration**: 75 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 50.0s - 60.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"In this video, we will learn why giving one big prompt to an AI often fails. And how breaking it into small steps — called Prompt Chaining — makes it work much better."

**Presenter:**
"Let me show you the problem. Imagine you ask an AI: 'Read this market report, summarize it, find the top three trends with data, and write an email to the team.' That is four jobs in one prompt.

What happens? The AI might summarize well, but forget to extract the data points. Or it writes a good email but misses a trend. This is because a single prompt puts too much load on the model. It starts forgetting instructions, losing track of context, and sometimes it just makes things up.

This is called prompt overload. And the solution is simple: Prompt Chaining.

Instead of one big prompt, we break the task into small steps. Step one: summarize the report. Step two: take that summary and find the top trends with data. Step three: take those trends and write the email.

Each step does only one job. And the output of one step becomes the input of the next step. This is like a factory assembly line — each worker does one task, and passes the result to the next worker."

**Riya (Question Overlay at 50.0s - 60.0s):**
"But if one step gives messy output, won't the next step also fail? How do we make sure the data passed between steps is clean and correct?"

**Presenter:**
"Great question, Riya! This is why we use structured output — like JSON. Instead of letting the AI write its answer in free text, we tell it to return a clean JSON object. This way, the next step can read the data exactly, without any confusion.

For example, the trend extraction step returns a JSON with trend name and supporting data. The email step reads that JSON and uses it directly. Clean input, clean output. That is the power of structured chaining.

In our next video, we will look at real-world use cases of prompt chaining. Subscribe to keep learning!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows a dark grid with faint prompt text scrolling. | Riya: "In this video, we will learn why..." |
| **10.0s - 22.0s** | **[The Problem]** Riya's card fades. Presenter's face circle appears. A giant single prompt box appears on screen with four highlighted tasks crammed inside. Red warning icons appear next to "Extract Data" and "Draft Email" — showing they failed. | Presenter: "Let me show you the problem..." |
| **22.0s - 32.0s** | **[Prompt Overload]** The single prompt box cracks and breaks apart. Labels fly out: "Instruction Neglect", "Context Drift", "Hallucination". Each label pulses red. | Presenter: "This is called prompt overload..." |
| **32.0s - 50.0s** | **[The Chain Solution]** Three clean, small prompt boxes line up left-to-right connected by glowing arrows. Box 1: "Summarize" → Box 2: "Find Trends" → Box 3: "Write Email". Each box lights up green as it completes. A factory assembly line animation runs underneath. | Presenter: "Instead of one big prompt..." |
| **50.0s - 60.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background chain animations freeze. Presenter's face circle is hidden. | Riya: "But if one step gives messy output..." |
| **60.0s - 70.0s** | **[Structured JSON]** Riya's card fades. Presenter's face circle reappears. Show a clean JSON object on screen: `{"trends": [{"trend_name": "AI Personalization", "supporting_data": "73% of consumers prefer..."}]}`. An arrow feeds it into the next prompt box which lights up green. | Presenter: "Great question, Riya!..." |
| **70.0s - 75.0s** | **[Outro / Subscribe]** The chain zooms out showing the full three-step pipeline with green checkmarks. Text overlay: "Next: Prompt Chaining in Practice" with a pulsing subscribe button. | Presenter: "In our next video..." |
