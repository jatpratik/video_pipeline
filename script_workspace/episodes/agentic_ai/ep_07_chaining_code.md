# Episode 07: Coding a Prompt Chain

- **Target Duration**: 80 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 55.0s - 65.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"In this video, we will write real Python code to build a prompt chain using LangChain. You will see how just a few lines of code can connect two AI steps together."

**Presenter:**
"Let's code a prompt chain. We will use a Python library called LangChain. It makes building chains very easy.

Here is our task: we have a sentence that describes a laptop — something like 'The new laptop has a 3.5 GHz processor, 16GB of RAM, and a 1TB SSD.' We want to extract the specifications and then convert them into a clean JSON format. Two steps, two prompts.

Step one: we create an extraction prompt. We tell the AI: 'Extract the technical specifications from the following text.' The AI reads the text and pulls out the specs.

Step two: we create a transformation prompt. We tell the AI: 'Take these specifications and turn them into a JSON object with cpu, memory, and storage as keys.' The AI takes the output from step one and formats it.

Now here is the beautiful part. In LangChain, we connect these two steps using a pipe operator — just a vertical bar symbol. We write: extraction prompt, pipe, LLM, pipe, output parser. And then we feed this into the second prompt with another pipe. The whole chain runs in one line of code.

When we run it, the AI first extracts the specs, then automatically passes them to the second prompt, and we get a clean JSON output. No manual copying, no messy text."

**Riya (Question Overlay at 55.0s - 65.0s):**
"This looks clean for two steps. But what if step one gives wrong output — like it misreads the specs? Does the whole chain break? How do we handle errors in the middle of a chain?"

**Presenter:**
"Great question, Riya! In production, we add validation checks between steps. After step one, we check: did the AI actually return the right fields? If something is missing or wrong, we can retry that step or ask the AI to correct it before moving to step two.

Some teams also add a 'judge' step — a separate prompt that reviews the output and decides if it is good enough to pass forward. This makes the chain much more reliable.

In our next video, we will talk about something even bigger: Context Engineering — the skill that separates good AI tools from great ones. Subscribe to stay ahead!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows a dark code editor with Python syntax faintly visible. | Riya: "In this video, we will write..." |
| **10.0s - 20.0s** | **[The Task]** Riya's card fades. Presenter's face circle appears. A text bubble shows the laptop description sentence. Two target boxes appear below: "Step 1: Extract Specs" and "Step 2: Convert to JSON", connected by an arrow. | Presenter: "Let's code a prompt chain..." |
| **20.0s - 32.0s** | **[Step 1: Extraction Prompt]** A code block appears on screen showing the `ChatPromptTemplate` for extraction. The input sentence flows in from the left, and extracted specs text flows out to the right. | Presenter: "Step one: we create an extraction prompt..." |
| **32.0s - 42.0s** | **[Step 2: Transformation Prompt]** A second code block appears below showing the JSON transformation prompt. The extracted specs flow in from step one's output, and a clean JSON object appears on the right. | Presenter: "Step two: we create a transformation prompt..." |
| **42.0s - 55.0s** | **[The Pipe Operator]** Both code blocks merge into one elegant line of code using `|` pipe operators. The line glows: `extraction_chain | prompt_transform | llm | StrOutputParser()`. An animation shows data flowing through each pipe segment left to right. The final JSON output lights up green. | Presenter: "Now here is the beautiful part..." |
| **55.0s - 65.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background code freezes. Presenter's face circle is hidden. | Riya: "This looks clean for two steps..." |
| **65.0s - 75.0s** | **[Error Handling]** Riya's card fades. Presenter's face circle reappears. Between step 1 and step 2, a new "Validator" box appears with a shield icon. Red arrows show failed output being sent back to step 1 for retry. Green arrows show validated output passing to step 2. | Presenter: "Great question, Riya!..." |
| **75.0s - 80.0s** | **[Outro / Subscribe]** The full chain with validator zooms out into a clean pipeline diagram. Text overlay: "Next: Context Engineering vs Prompt Engineering" with a pulsing subscribe button. | Presenter: "In our next video..." |
