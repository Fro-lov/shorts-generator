from pathlib import Path
from typing import Dict
from config.settings import OUTPUT_DIR


class EpisodeOutputManager:
    """
    Manages structured clean per-episode output folders.
    Structure:
    output/<episode_id>/
      ├── video.mp4          (Final video file)
      ├── voice/             (TTS audio tracks)
      ├── subtitles/         (.ass subtitle files)
      ├── visuals/           (Generated 2D diagrams, code cards)
      ├── frames/            (Extracted preview frames)
      └── temp/              (Intermediate background/temp files)
    """
    def __init__(self, episode_id: str = "1"):
        self.episode_id = str(episode_id)
        self.root_dir = OUTPUT_DIR / self.episode_id
        self.voice_dir = self.root_dir / "voice"
        self.subtitles_dir = self.root_dir / "subtitles"
        self.visuals_dir = self.root_dir / "visuals"
        self.frames_dir = self.root_dir / "frames"
        self.temp_dir = self.root_dir / "temp"

        # Ensure all folders exist
        for d in [self.root_dir, self.voice_dir, self.subtitles_dir, self.visuals_dir, self.frames_dir, self.temp_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_paths(self, video_name: str = "final_short.mp4") -> Dict[str, Path]:
        return {
            "final_video": self.root_dir / video_name,
            "voice": self.voice_dir / "voice.mp3",
            "subtitles": self.subtitles_dir / "subtitles.ass",
            "temp_bg": self.temp_dir / "temp_bg.mp4",
            "visuals_dir": self.visuals_dir,
            "frames_dir": self.frames_dir
        }
