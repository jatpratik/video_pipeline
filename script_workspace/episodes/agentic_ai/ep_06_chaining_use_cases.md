# Episode 06: Prompt Chaining in Practice

- **Target Duration**: 80 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 55.0s - 65.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"In this video, we will see how prompt chaining is used in real projects — from reading invoices to building full research reports."

**Presenter:**
"Prompt chaining is not just theory. Let me show you how people use it in the real world.

Use case one: Reading invoices. Imagine you have a scanned PDF invoice. Step one: the AI reads the text from the image using OCR. Step two: it cleans up the data — for example, converting 'one thousand and fifty' into the number 1050. Step three: if there is any math to do, like calculating tax, we send the numbers to a calculator tool. The AI is not good at math, so we use an external tool for that part. Step four: we get the final, accurate result.

Use case two: Building a research report. Step one: find and download many articles about a topic. Step two: extract key information from each article. This part can actually run in parallel — all articles at the same time. Step three: once all the data is collected, we chain it together. Combine the findings into one document, then write a draft, and then review and improve the draft. These last steps must happen one after the other, because each step depends on the previous one.

Use case three: Writing code. Step one: understand the request and write an outline. Step two: write the code. Step three: check for errors. Step four: fix the errors and add comments. Each step builds on the last one."

**Riya (Question Overlay at 55.0s - 65.0s):**
"You said some steps can run at the same time, and some must run one after the other. In a big project, how do we decide which parts to run in parallel and which to chain?"

**Presenter:**
"Good question, Riya! The rule is simple: if two tasks do not depend on each other, run them in parallel. For example, reading ten different articles — each one is independent. But once you need to combine all the results into one report, that must be sequential. You cannot combine data you have not collected yet.

So in practice, real systems use both: parallel processing for independent work, and prompt chaining for the steps that depend on each other.

In our next video, we will write actual Python code to build a prompt chain. Subscribe to code with me!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows blurred document icons and code snippets. | Riya: "In this video, we will see..." |
| **10.0s - 30.0s** | **[Use Case 1: Invoice]** Riya's card fades. Presenter's face circle appears. A scanned invoice image appears. Arrows flow: OCR (text extraction) → Cleanup ("one thousand" becomes "1050") → Calculator tool icon → Final clean data card with green checkmark. | Presenter: "Use case one: Reading invoices..." |
| **30.0s - 45.0s** | **[Use Case 2: Research Report]** Transition to a library of article thumbnails. Multiple articles download simultaneously (parallel arrows). Then a funnel merges them into one document → Draft text block → Polished report with gold badge. Sequential arrows are shown for the last three steps. | Presenter: "Use case two: Building a research report..." |
| **45.0s - 55.0s** | **[Use Case 3: Code Generation]** Transition to a code editor. Steps appear as tabs: "Outline" → "Draft Code" → "Error Check" → "Final Code + Comments". Each tab lights up green in sequence. | Presenter: "Use case three: Writing code..." |
| **55.0s - 65.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background code editor freezes. Presenter's face circle is hidden. | Riya: "You said some steps can run..." |
| **65.0s - 75.0s** | **[Parallel vs Sequential]** Riya's card fades. Presenter's face circle reappears. Split screen: Left side shows 10 parallel arrows going into 10 article boxes (parallel). Right side shows 3 sequential boxes connected by arrows: "Combine" → "Draft" → "Review" (sequential). | Presenter: "Good question, Riya!..." |
| **75.0s - 80.0s** | **[Outro / Subscribe]** All three use case icons (invoice, report, code) line up with green checkmarks. Text overlay: "Next: Coding a Prompt Chain" with a pulsing subscribe button. | Presenter: "In our next video..." |
