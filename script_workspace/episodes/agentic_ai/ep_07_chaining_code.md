# Episode 07: Coding a Prompt Chain

- **Target Duration**: 80 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 55.0s - 65.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"Enough theory. Today we write real code. We'll build a two-step prompt chain in Python using LangChain — and you'll see how simple it actually is."

**Presenter:**
"Alright, let's build this.

Here's what we want to do. We have a sentence: 'This laptop has a 3.5 GHz processor, 16GB RAM, and a 1TB SSD.'

We want two things. First — pull out the specs. Second — turn them into clean JSON. Two steps. Two prompts. One chain.

Step one. We write a prompt: 'Extract the specs from this text.' The AI reads it, pulls out processor, RAM, and storage. Done.

Step two. We write another prompt: 'Take these specs and format them as JSON with cpu, memory, and storage as keys.' The AI takes step one's output and formats it. Done.

Now here's the magic. In LangChain, we connect these with a pipe — just this symbol. Prompt, pipe, AI model, pipe, output parser. One line. The data flows through like water in a pipe.

We hit run. The AI extracts the specs… passes them forward… and out comes clean JSON. No copy-paste. No manual work. Just a smooth pipeline."

**Riya (Question Overlay at 55.0s - 65.0s):**
"This looks clean. But what if step one gives wrong output? Like, it misses the RAM. Does the whole chain break?"

**Presenter:**
"Good catch. In real projects, we add a quality gate between steps. After step one finishes, we check — did it find all the fields? If something's missing, we retry that step.

Some teams go further. They add a 'judge' — a separate AI call that reviews the output. If the judge says it's good, move forward. If not, try again.

That one extra step makes the whole chain much more reliable.

Next — we're going beyond prompts. Let's talk about Context Engineering. Subscribe!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows a dark code editor with Python syntax faintly visible. | Riya: "Enough theory. Today we write real code..." |
| **10.0s - 20.0s** | **[The Task]** Riya's card fades. Presenter's face circle appears. A text bubble shows the laptop description sentence. Two target boxes appear below: "Step 1: Extract Specs" and "Step 2: Convert to JSON", connected by an arrow. | Presenter: "Alright, let's build this..." |
| **20.0s - 32.0s** | **[Step 1: Extraction]** A code block appears showing the extraction prompt template. The input sentence flows in from the left, and extracted specs text flows out to the right. | Presenter: "Step one. We write a prompt..." |
| **32.0s - 42.0s** | **[Step 2: JSON Format]** A second code block appears below showing the JSON transformation prompt. The extracted specs flow in from step one's output, and a clean JSON object appears on the right. | Presenter: "Step two. We write another prompt..." |
| **42.0s - 55.0s** | **[The Pipe Operator]** Both code blocks merge into one elegant line using `|` pipe operators. The line glows as data flows through each segment left to right. The final JSON output lights up green. | Presenter: "Now here's the magic..." |
| **55.0s - 65.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background code freezes. Presenter's face circle is hidden. | Riya: "This looks clean. But what if..." |
| **65.0s - 75.0s** | **[Quality Gate]** Riya's card fades. Presenter's face circle reappears. Between step 1 and step 2, a "Quality Gate" shield icon appears. Red arrows show failed output looping back for retry. Green arrows show good output passing to step 2. | Presenter: "Good catch. In real projects..." |
| **75.0s - 80.0s** | **[Outro / Subscribe]** The full chain with quality gate zooms out into a clean pipeline diagram. Text overlay: "Next: Context Engineering" with a pulsing subscribe button. | Presenter: "Next — we're going beyond prompts..." |
