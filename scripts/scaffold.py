#!/usr/bin/env python3
"""
Visual Scene Scaffolding Script
================================
Creates a boilerplate HTML file (e.g. scenes/agent_scene_05.html) based on
the layout coordinates, styles, fonts, and scripts of agent_scene_03.html.
"""

import argparse
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    import config
    logger = config.logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("scaffold")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, width=1080, height=1920">
    <title>AI Video Scene ({scene_id})</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&family=Inter:wght@400;700;900&family=Outfit:wght@400;700;900&display=swap" rel="stylesheet">

    <style>
        :root {
            --bg-color: #060610;
            --neon-cyan: #00F0FF;
            --neon-pink: #FF2D6A;
            --neon-purple: #7B2CBF;
            --neon-orange: #FF6B35;
            --neon-green: #00FF88;
            --neon-yellow: #FFDD00;
            --neon-gold: #FFD700;
            --neon-red: #FF3333;
            --glass-bg: rgba(10, 12, 24, 0.85);
            --glass-border: rgba(255, 255, 255, 0.1);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            background-color: var(--bg-color);
            color: #ffffff;
            font-family: 'Outfit', 'Inter', sans-serif;
            width: 1080px;
            height: 1920px;
            overflow: hidden;
            position: relative;
        }

        /* Deep nebula background */
        .nebula-layer {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background:
                radial-gradient(ellipse at 25% 20%, rgba(123, 44, 191, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 75% 50%, rgba(0, 240, 255, 0.07) 0%, transparent 45%),
                radial-gradient(ellipse at 50% 85%, rgba(255, 45, 106, 0.08) 0%, transparent 40%);
            z-index: 1;
            pointer-events: none;
        }

        /* Micro-grid */
        .bg-grid {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-image:
                linear-gradient(rgba(255, 255, 255, 0.018) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.018) 1px, transparent 1px);
            background-size: 40px 40px;
            z-index: 2;
            opacity: 0.5;
        }

        /* Scanlines */
        .scanlines {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: repeating-linear-gradient(0deg,
                rgba(0, 0, 0, 0.1),
                rgba(0, 0, 0, 0.1) 1px,
                transparent 1px,
                transparent 3px);
            pointer-events: none;
            z-index: 99;
            opacity: 0.3;
        }

        /* Canvas layer for particles */
        #canvas-bg {
            position: absolute;
            top: 0; left: 0;
            width: 1080px; height: 1920px;
            z-index: 5;
            pointer-events: none;
        }

        .scene-container {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 10;
            pointer-events: none;
        }

        /* CAPTIONS - Centered bottom-right */
        #caption-container {
            position: absolute;
            right: 30px;
            top: 1320px;
            width: 550px;
            height: 400px;
            z-index: 90;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(8, 10, 20, 0.78);
            border: 1.5px solid rgba(255, 255, 255, 0.08);
            border-radius: 22px;
            padding: 16px 24px;
            box-shadow:
                0 12px 50px rgba(0, 0, 0, 0.6),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
        }

        /* Glowing border frame for face video */
        #face-frame {
            position: absolute;
            left: 56px;
            top: 1316px;
            width: 408px;
            height: 408px;
            border: 4px solid var(--neon-cyan);
            border-radius: 34px;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.4), inset 0 0 15px rgba(0, 240, 255, 0.2);
            z-index: 85;
            background: rgba(8, 10, 20, 0.6);
            pointer-events: none;
            opacity: 1;
        }

        .sentence-block {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-content: center;
            width: 100%;
            gap: 8px 12px;
            text-shadow: 0 3px 10px rgba(0, 0, 0, 0.9);
        }

        .cap-word {
            display: inline-block;
            font-size: 30px;
            font-weight: 800;
            color: rgba(255, 255, 255, 0.92);
            transition: color 0.12s ease, transform 0.12s ease, text-shadow 0.12s ease;
            transform-origin: center;
            line-height: 1.4;
        }

        .cap-word.active {
            color: #00F0FF !important;
            text-shadow: 0 0 22px #00F0FF, 0 0 8px #00F0FF;
            transform: scale(1.15);
            font-weight: 900;
        }

        .cap-word.active-highlight {
            color: #FFDD00 !important;
            text-shadow: 0 0 22px #FFDD00, 0 0 10px #FFDD00;
            transform: scale(1.18);
            font-weight: 900;
        }

        .cap-word.active-danger {
            color: var(--neon-red) !important;
            text-shadow: 0 0 22px var(--neon-red), 0 0 10px var(--neon-red);
            transform: scale(1.15);
            font-weight: 900;
        }

        .cap-word.past {
            color: rgba(255, 255, 255, 0.32) !important;
            text-shadow: none;
            transform: scale(1.0);
        }

        /* ============================================== */
        /* VISUAL CANVAS STYLING SYSTEM                   */
        /* ============================================== */
        .visual-area {
            position: absolute;
            top: 0;
            left: 0;
            width: 1080px;
            height: 1320px;
            z-index: 20;
            pointer-events: none;
        }
        
        .visual-title {
            position: absolute;
            top: 160px;
            left: 50%;
            transform: translateX(-50%);
            font-family: 'Outfit', sans-serif;
            font-size: 52px;
            font-weight: 900;
            text-align: center;
            background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 3px;
            white-space: nowrap;
            z-index: 22;
        }
    </style>
</head>

<body>
    <div class="nebula-layer"></div>
    <div class="bg-grid"></div>
    <div class="scanlines"></div>

    <canvas id="canvas-bg" width="1080" height="1920"></canvas>

    <div class="scene-container">
        <div id="caption-container"></div>
        <div id="face-frame"></div>

        <!-- ============================================================== -->
        <!-- Visual Component Area (0px to 1320px height)                   -->
        <!-- ============================================================== -->
        <div class="visual-area">
            <div class="visual-title" id="scene-title" style="opacity: 0;">VISUALS AREA</div>
            
            <!-- Implement your scene elements here -->
            
        </div>
    </div>

    <!-- Captions Data -->
    <script src="{scene_id}_captions.js"></script>

    <script>
        // =====================================================================
        // MASTER TIMELINE (All timed animations relative to voice)
        // =====================================================================
        const tl = gsap.timeline({ paused: true });
        window.tl = tl;
        
        // Identity mapping since co-hosts are integrated at the end
        const time = (sec) => sec;

        // =====================================================================
        // CANVAS STATE & AMBIENT PARTICLES
        // =====================================================================
        const S = {
            ambientOpacity: 0.0,
            time: 0
        };

        const canvas = document.getElementById("canvas-bg");
        const ctx = canvas.getContext("2d");
        const W = 1080, H = 1920;

        const ambientParticles = [];
        for (let i = 0; i < 100; i++) {
            ambientParticles.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 0.4,
                vy: -0.3 - Math.random() * 0.5,
                size: 1 + Math.random() * 2.5,
                alpha: 0.1 + Math.random() * 0.3,
                hue: Math.random() > 0.5 ? 186 : 320,
                pulse: Math.random() * Math.PI * 2
            });
        }

        let frameCount = 0;

        function drawFrame() {
            ctx.clearRect(0, 0, W, H);
            frameCount++;
            S.time = frameCount / 60;

            if (S.ambientOpacity > 0.01) {
                drawAmbientParticles();
            }

            requestAnimationFrame(drawFrame);
        }

        function drawAmbientParticles() {
            ctx.save();
            ctx.globalAlpha = S.ambientOpacity;

            for (const p of ambientParticles) {
                p.x += p.vx;
                p.y += p.vy;
                p.pulse += 0.02;

                if (p.y < -10) { p.y = H + 10; p.x = Math.random() * W; }
                if (p.x < -10) p.x = W + 10;
                if (p.x > W + 10) p.x = -10;

                const pulseAlpha = p.alpha * (0.5 + 0.5 * Math.sin(p.pulse));
                const color = p.hue === 186 ? "#00F0FF" : "#FF2D6A";

                ctx.save();
                ctx.globalAlpha *= pulseAlpha;
                ctx.shadowBlur = 10;
                ctx.shadowColor = color;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
            ctx.restore();
        }

        drawFrame();

        // =====================================================================
        // CAPTIONS SYNC ENGINE
        // =====================================================================
        const sentences = window.{scene_id}_captions;
        const captionContainer = document.getElementById("caption-container");

        // Words to highlight in Cyan/Yellow/Red
        const highlightWords = [
            "chaining", "prompt", "ai", "agents", "structure", "data"
        ];

        const dangerWords = [
            "failed", "forgot", "lost", "confused", "risk"
        ];

        sentences.forEach((sentence) => {
            const sDiv = document.createElement("div");
            sDiv.className = "sentence-block";
            gsap.set(sDiv, { display: "none", opacity: 0 });

            sentence.words.forEach((w) => {
                const wSpan = document.createElement("span");
                wSpan.className = "cap-word";
                wSpan.innerText = w.text;
                sDiv.appendChild(wSpan);

                const cleanWord = w.text.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?%]/g, "");
                let activeClass = "active";
                if (highlightWords.includes(cleanWord)) {
                    activeClass = "active-highlight";
                }
                if (dangerWords.includes(cleanWord)) {
                    activeClass = "active-danger";
                }

                tl.to(wSpan, {
                    onStart: () => { wSpan.classList.add(activeClass); wSpan.classList.remove("past"); },
                    onReverseComplete: () => { wSpan.classList.remove(activeClass); wSpan.classList.remove("past"); },
                    duration: 0.05
                }, w.start);

                tl.to(wSpan, {
                    onStart: () => { wSpan.classList.remove(activeClass); wSpan.classList.add("past"); },
                    onReverseComplete: () => { wSpan.classList.add(activeClass); wSpan.classList.remove("past"); },
                    duration: 0.05
                }, w.end);
            });

            captionContainer.appendChild(sDiv);
            tl.set(sDiv, { display: "flex" }, sentence.start);
            tl.to(sDiv, { opacity: 1, duration: 0.12 }, sentence.start);
            tl.to(sDiv, { opacity: 0, duration: 0.12 }, sentence.end);
            tl.set(sDiv, { display: "none" }, sentence.end + 0.12);
        });

        // =====================================================================
        // ANIMATION SEQUENCE
        // =====================================================================
        
        // Turn on particles at start
        tl.to(S, { ambientOpacity: 1.0, duration: 1.0 }, time(0.0));
        tl.to("#scene-title", { opacity: 1, duration: 0.8 }, time(0.5));
        
        // Add your GSAP animation steps keyed to the "time(sec)" timeline here
        
        // Keyboard controls for testing / scrubbing
        window.addEventListener("keydown", (e) => {
            if (e.code === "Space") {
                if (tl.paused()) tl.play();
                else tl.pause();
            }
            if (e.key === "1") tl.seek(0.0);
            if (e.key === "2") tl.seek(10.0);
            if (e.key === "3") tl.seek(20.0);
            if (e.key === "4") tl.seek(30.0);
            if (e.key === "5") tl.seek(40.0);
            if (e.key === "6") tl.seek(50.0);
        });

    </script>
</body>
</html>
"""


def scaffold_scene(scene_id: str, scenes_dir: Path):
    """Generate the scaffolded HTML boilerplate scene."""
    output_html_path = scenes_dir / f"{scene_id}.html"
    
    if output_html_path.exists():
        logger.error(f"Scene file already exists: {output_html_path}. Omit to prevent overwrite.")
        sys.exit(1)
        
    formatted_html = HTML_TEMPLATE.replace("{scene_id}", scene_id)
    
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(formatted_html)
        
    logger.info(f"Successfully generated scaffolded scene file at {output_html_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new visual HTML/CSS/GSAP scene template based on agent_scene_03.html dimensions."
    )
    parser.add_argument(
        "-s", "--scene",
        type=str,
        required=True,
        help="Scene ID to scaffold (e.g. agent_scene_05)"
    )
    args = parser.parse_args()
    
    import config
    scaffold_scene(args.scene, config.SCENES_DIR)


if __name__ == "__main__":
    main()
