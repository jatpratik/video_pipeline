"""
Video Pipeline — Step Modules
==============================
Each module implements one stage of the pipeline:
  step1_alignment    — WhisperX forced alignment
  step2_segmentation — LLM-powered scene segmentation
  step3_visual_gen   — HTML/CSS/GSAP generation
  step4_render       — Playwright headless rendering
  step5_assembly     — FFmpeg video assembly
  step6_export       — Final export & validation
"""
