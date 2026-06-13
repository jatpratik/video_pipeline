# Episode 06: Prompt Chaining in Practice

- **Target Duration**: 80 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Riya's Timing (Intro Hook)**: 0.0s - 10.0s (10.0s duration).
- **Riya's Timing (Question)**: 55.0s - 65.0s (10.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Riya (Intro Hook at 0.0s - 10.0s):**
"Prompt chaining isn't just theory. Today we'll see it work on real tasks — reading invoices, building reports, and even writing code."

**Presenter:**
"Let's make this real.

Your company gets hundreds of scanned invoices every month. All PDFs. How does AI handle this?

Step one — the AI reads text from the scanned image. That's OCR.
Step two — it cleans up the messy text. 'One thousand fifty' becomes 1050.
Step three — any math needed? Like tax? We don't trust the AI with math. We send the numbers to a calculator tool. It does the math perfectly.
Step four — done. Clean, accurate data.

Now, a bigger example. You need a research report on a topic.

Step one — find and download ten articles. Here's the cool part — this step can run in parallel. All ten at the same time. They don't depend on each other.

But after that? It's sequential. Step two — combine all findings into one document. Step three — write the draft. Step four — review and polish it. Each step needs the previous one to finish first.

One more. Writing code.

Step one — understand the request and plan it out.
Step two — write the first draft of code.
Step three — check for bugs.
Step four — fix bugs, add comments. Done."

**Riya (Question Overlay at 55.0s - 65.0s):**
"So some steps run together, and some run one by one. How do you decide which is which?"

**Presenter:**
"Simple rule. If two tasks don't need each other — run them together. Reading ten different articles? Independent. Run them all at once.

But combining those articles into one report? That needs all the data first. So it waits. It runs after.

Real systems use both. Parallel for speed. Chaining for order.

Next — we'll write actual Python code to build a chain. Subscribe!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Riya Intro (PiP)]** Riya's glassmorphic card overlays the center visual space at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background shows blurred document icons and code snippets. | Riya: "Prompt chaining isn't just theory..." |
| **10.0s - 30.0s** | **[Use Case 1: Invoice]** Riya's card fades. Presenter's face circle appears. A scanned invoice image appears. Arrows flow: OCR (text extraction) → Cleanup ("one thousand" becomes "1050") → Calculator tool icon → Final clean data card with green checkmark. | Presenter: "Your company gets hundreds..." |
| **30.0s - 45.0s** | **[Use Case 2: Research Report]** Transition to a library of article thumbnails. Multiple articles download simultaneously (parallel arrows). Then a funnel merges them into one document → Draft text block → Polished report with gold badge. Sequential arrows are shown for the last three steps. | Presenter: "Now, a bigger example..." |
| **45.0s - 55.0s** | **[Use Case 3: Code Generation]** Transition to a code editor. Steps appear as tabs: "Plan" → "Draft Code" → "Bug Check" → "Final Code". Each tab lights up green in sequence. | Presenter: "One more. Writing code..." |
| **55.0s - 65.0s** | **[Riya Question (PiP)]** Riya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background code editor freezes. Presenter's face circle is hidden. | Riya: "So some steps run together..." |
| **65.0s - 75.0s** | **[Parallel vs Sequential]** Riya's card fades. Presenter's face circle reappears. Split screen: Left side shows 10 parallel arrows going into 10 article boxes (parallel). Right side shows 3 sequential boxes connected by arrows: "Combine" → "Draft" → "Review" (sequential). | Presenter: "Simple rule..." |
| **75.0s - 80.0s** | **[Outro / Subscribe]** All three use case icons (invoice, report, code) line up with green checkmarks. Text overlay: "Next: Coding a Prompt Chain" with a pulsing subscribe button. | Presenter: "Next — we'll write actual Python code..." |
