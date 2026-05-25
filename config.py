"""
Video Pipeline Configuration
=============================
Central configuration for the AI video generation pipeline.
Auto-detects CUDA availability, defines all paths, video specs, and logging.
"""

import os
import sys
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Load .env file (optional dependency)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not installed; rely on system env vars


# ===========================================================================
# DEVICE CONFIGURATION
# ===========================================================================

def detect_device() -> str:
    """Auto-detect CUDA availability, fallback to CPU."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


_device_env = os.environ.get("WHISPERX_DEVICE", "auto")
DEVICE: str = detect_device() if _device_env == "auto" else _device_env


# ===========================================================================
# VIDEO SPECIFICATIONS
# ===========================================================================

VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VISUAL_WIDTH: int = 1080
VISUAL_HEIGHT: int = 1920
FPS: int = 30


# ===========================================================================
# WHISPERX CONFIGURATION
# ===========================================================================

WHISPERX_MODEL: str = os.environ.get("WHISPERX_MODEL", "large-v3-turbo")
WHISPERX_COMPUTE_TYPE: str = "float32" if DEVICE == "cpu" else "float16"
WHISPERX_BATCH_SIZE: int = 4 if DEVICE == "cpu" else 16



# ===========================================================================
# DIRECTORY PATHS
# ===========================================================================

BASE_DIR: Path = Path(__file__).parent.resolve()
INPUT_DIR: Path = BASE_DIR / "input"
OUTPUT_DIR: Path = BASE_DIR / "output"
SCENES_DIR: Path = BASE_DIR / "scenes"
RENDERED_DIR: Path = BASE_DIR / "rendered_scenes"
TEMPLATES_DIR: Path = BASE_DIR / "templates"
TIMESTAMPS_DIR: Path = BASE_DIR / "timestamps"
AUDIO_DIR: Path = BASE_DIR / "audio"
LOGS_DIR: Path = BASE_DIR / "logs"

# Create all directories on import
for _dir in [INPUT_DIR, OUTPUT_DIR, SCENES_DIR, RENDERED_DIR, TEMPLATES_DIR,
             TIMESTAMPS_DIR, AUDIO_DIR, LOGS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)



# ===========================================================================
# COMPLEXITY BUDGET (per scene)
# ===========================================================================

MAX_TEACHING_IDEAS_PER_SCENE: int = 1
MAX_MAJOR_OBJECTS_PER_SCENE: int = 2
MAX_VISIBLE_WORDS_PER_SCENE: int = 8
MAX_SIMULTANEOUS_MOTIONS: int = 3
SAFE_AREA_TOP_PERCENT: int = 55   # All content in top 55% of 1080×1920



# ===========================================================================
# RENDERING CONFIGURATION
# ===========================================================================

RENDER_BATCH_SIZE: int = int(os.environ.get("RENDER_BATCH_SIZE", "3"))
RENDER_TIMEOUT_BUFFER_MS: int = 2000   # Extra wait after animation ends
MAX_DRIFT_TOLERANCE_S: float = 0.15    # Max allowed duration drift (seconds)
MAX_RE_RENDER_ATTEMPTS: int = 3        # Auto re-render on validation failure


# ===========================================================================
# SCENE SEGMENTATION
# ===========================================================================

MIN_SCENE_DURATION: float = 2.0   # Merge scenes shorter than this
MAX_SCENE_DURATION: float = 8.0   # Split scenes longer than this


# ===========================================================================
# FFMPEG SETTINGS
# ===========================================================================

FFMPEG_CRF: int = 18
FFMPEG_PRESET: str = "medium"
FFMPEG_AUDIO_BITRATE: str = "192k"


# ===========================================================================
# LOGGING
# ===========================================================================

def setup_logging() -> logging.Logger:
    """Configure pipeline-wide logging to file and console."""
    # Reconfigure stdout/stderr to UTF-8 to prevent encoding errors on Windows console
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    log_file = LOGS_DIR / "pipeline.log"

    # Root pipeline logger
    _logger = logging.getLogger("video_pipeline")
    _logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on re-import
    if not _logger.handlers:
        # File handler — full debug output
        fh = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

        # Console handler — info and above
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(message)s",
            datefmt="%H:%M:%S"
        ))

        _logger.addHandler(fh)
        _logger.addHandler(ch)

    return _logger


logger: logging.Logger = setup_logging()
