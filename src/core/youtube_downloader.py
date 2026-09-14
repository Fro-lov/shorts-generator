import subprocess
from pathlib import Path
from typing import Optional
from config.settings import FFMPEG_PATH, ASSETS_DIR


class YouTubeDownloader:
    def __init__(self, ffmpeg_path: str = FFMPEG_PATH):
        self.ffmpeg_path = ffmpeg_path
        self.download_dir = ASSETS_DIR / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def download_clip(
        self,
        url: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        output_name: str = "gameplay_clip.mp4"
    ) -> Path:
        """
        Downloads a video segment from YouTube using yt-dlp.
        start_time and end_time can be in 'MM:SS' or 'HH:MM:SS' or seconds.
        """
        output_path = self.download_dir / output_name

        cmd = [
            "yt-dlp",
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "--ffmpeg-location", self.ffmpeg_path,
            "--force-overwrites",
            "-o", str(output_path)
        ]

        if start_time and end_time:
            # Download only the specific section using ffmpeg downloader
            cmd.extend([
                "--download-sections", f"*{start_time}-{end_time}",
                "--force-keyframes-at-cuts"
            ])
        elif start_time:
            cmd.extend([
                "--download-sections", f"*{start_time}-inf",
                "--force-keyframes-at-cuts"
            ])

        cmd.append(url)

        print(f"[*] Скачивание фрагмента YouTube ({start_time} - {end_time}): {url}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Ошибка загрузки видео с YouTube:\n{res.stderr}")

        return output_path
