import os
from pathlib import Path
import imageio_ffmpeg

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SFX_DIR = ASSETS_DIR / "sfx"
MUSIC_DIR = ASSETS_DIR / "music"
PLACEHOLDERS_DIR = ASSETS_DIR / "placeholders"

# Ensure output and asset dirs exist
for d in [OUTPUT_DIR, ASSETS_DIR, FONTS_DIR, SFX_DIR, MUSIC_DIR, PLACEHOLDERS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# FFmpeg Executable detection
def get_ffmpeg_path() -> str:
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()

# Video output settings (9:16 Shorts / TikTok standard)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Hardware Acceleration / Encoder Settings
# NVIDIA RTX NVENC GPU encoder offloads work from CPU and renders ~10x faster
VIDEO_CODEC = "h264_nvenc"
VIDEO_PRESET = "p4"
VIDEO_CQ = "20"

# TTS Defaults
DEFAULT_VOICE = "ru-RU-DmitryNeural"  # High quality natural Russian voice
# Alternative voices: "ru-RU-SvetlanaNeural"

# Subtitle styling (ASS SubStation Alpha format)
SUBTITLE_FONT = "Arial"
SUBTITLE_FONT_SIZE = 48
SUBTITLE_PRIMARY_COLOR = "&H00FFFFFF"     # White (BGR in ASS: &H00BBGGRR)
SUBTITLE_HIGHLIGHT_COLOR = "&H0000FFFF"   # Bright Yellow (&H0000FFFF in ASS is yellow B:00 G:FF R:FF)
SUBTITLE_OUTLINE_COLOR = "&H00000000"     # Black border
SUBTITLE_OUTLINE_WIDTH = 4
SUBTITLE_MARGIN_V = 420                   # Placed comfortably above YouTube Subscribe button (Y=1480-1500)

# Layout Zones (Strict Zero-Overlap Vertical Grid for 1080x1920)
ZONE_GAMEPLAY_Y = 200                     # Top gameplay block: Y=200 to Y=774
ZONE_GAMEPLAY_WIDTH = 1020
ZONE_GAMEPLAY_HEIGHT = 574

# Full-Height Diagram Cards (Top 2/3 during explanation scenes): Y=80 to Y=1360
ZONE_DIAGRAM_TOP_Y = 80
ZONE_DIAGRAM_WIDTH = 1000
ZONE_DIAGRAM_HEIGHT = 1280

# Motion UI / Memes overlay zone during gameplay: Y=860 to Y=1400
ZONE_VISUAL_Y = 860
ZONE_VISUAL_MAX_WIDTH = 960
ZONE_VISUAL_MAX_HEIGHT = 540

ZONE_SUBTITLES_Y = 1480                   # Subtitles zone: Y=1480 to Y=1540 (MarginV=420)
ZONE_BOTTOM_SAFE_GAP = 380                # Safe margin for YouTube Subscribe button and Shorts UI


