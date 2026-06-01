# Episode 03: The 4 Levels of AI Agent Complexity

- **Target Duration**: 80 seconds
- **Narrator Tone**: Friendly, clear, tech-focused AI educator.
- **Maya's Timing**: 55.0s - 64.0s (9.0s duration).

## The Video Script

### 1. Voiceover Narration Script
This is the clean text you will read during voice recording/teleprompting.

**Presenter:**
"Did you know that AI agents have different levels of capability? Let's break down the four levels of AI agents.

Level 0 is just the LLM itself. It cannot use tools, it has no memory, and it does not know about current events. It only answers using what it learned during its training.

Level 1 is the Connected Solver. Here, we connect the LLM to tools like Google search, databases, and APIs. Now, the LLM can find live information, like today's stock prices.

Level 2 is the Strategic Solver. This agent can plan steps ahead. It also uses something called 'context engineering'. This means we clean up the information and give the AI only the most important details at each step, so its memory does not get overloaded.

Level 3 is a Team of Agents. Just like a real company, different agents have different jobs—like a researcher, a designer, and a manager. They work together to finish a big project from start to end.

But building these levels in real life is not easy."

**Maya (Overlay at 55.0s - 64.0s):**
"You mentioned context engineering. How do we actually clean up the data at each step without losing important details that the AI needs?"

**Presenter:**
"Great question, Maya! Instead of giving the AI the whole raw text, we write code to filter it. We extract only the key details, like a flight number or an error message, and ignore the rest. This keeps the AI focused and saves a lot of API costs.

So where is all this going? In our next video, we will talk about the future of AI agents. Subscribe to stay ahead!"

### 2. Visual Storyboard
This coordinates the animations, overlays, and timing cues for the video assembly.

| Time | Visual State / Animation | Audio Cues |
| :--- | :--- | :--- |
| **0.0s - 10.0s** | **[Hook]** A large vertical ladder with four rungs appears, glowing neon blue. The rungs are labeled: Level 0, Level 1, Level 2, Level 3. | Presenter: "Did you know that AI agents..." |
| **10.0s - 20.0s** | **[Level 0 Node]** Focus on the "Level 0" rung. A brain icon lights up, but it is locked inside a bubble with a dotted line indicating no external connections. A calendar showing "2026" appears with a red "X" over it to show lack of real-time awareness. | Presenter: "Level 0 is just the LLM..." |
| **20.0s - 32.0s** | **[Level 1 Node]** The view pans up to "Level 1". The bubble pops, and wires connect the brain node to external icons: a magnifying glass (search), a database container (RAG), and a stocks chart (financial APIs). | Presenter: "Level 1 is the Connected..." |
| **32.0s - 43.0s** | **[Level 2 Context Engineering]** Panning up to "Level 2". Show a massive, messy text file of API output. A filter funnel compresses it into a tiny, shining golden scroll containing only three key-value pairs (e.g., flight_id: 102, status: delayed). | Presenter: "Level 2 is the Strategic..." |
| **43.0s - 55.0s** | **[Level 3 Collaboration]** Panning up to "Level 3". We see a "Project Manager" node delegating tasks to a "Research" node, a "Design" node, and a "Marketing" node. Arrows flow between them representing collaborative communication. | Presenter: "Level 3 is a Team of Agents..." |
| **55.0s - 64.0s** | **[Maya Overlay (PiP)]** Maya's glassmorphic overlay card slides in at $x: 140, y: 140, w: 800, h: 1160$ with an orange border glow. Background multi-agent animations freeze. | Maya: "You mentioned context engineering..." |
| **64.0s - 73.0s** | **[Context Filtering Visual]** Maya's card fades. We show a schema parser code snippet on screen: `extract_critical_context(api_response) -> payload`. Watch the payload shrink from 50 lines to 3 lines, lighting up green. | Presenter: "Great question, Maya! Instead..." |
| **73.0s - 80.0s** | **[Outro / Subscribe]** The ladder zooms out. Rungs glow in sequence. A neon preview text pops up: "Next: The Future of AI Agents" with a pulsing subscribe button. | Presenter: "So where is all this going..." |
