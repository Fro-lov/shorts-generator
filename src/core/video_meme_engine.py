import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from config.settings import ASSETS_DIR, FFMPEG_PATH


class VideoMemeDownloader:
    """
    Downloads short video memes and green-screen clips via yt-dlp or direct URLs.
    """
    def __init__(self):
        self.video_memes_dir = ASSETS_DIR / "memes" / "video"
        self.video_memes_dir.mkdir(parents=True, exist_ok=True)

    def download_meme_clip(
        self,
        url: str,
        start_time: Optional[str] = None,
        duration: float = 3.0,
        output_name: str = "meme_clip.mp4"
    ) -> Path:
        out_path = self.video_memes_dir / output_name

        cmd = [
            "yt-dlp",
            "--ffmpeg-location", FFMPEG_PATH,
            "--force-overwrites",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", str(out_path)
        ]

        if start_time:
            end_sec = float(start_time) + duration if isinstance(start_time, (int, float)) else f"{start_time}+{duration}"
            cmd.extend(["--download-sections", f"*{start_time}-{end_sec}", "--force-keyframes-at-cuts"])

        cmd.append(url)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed downloading video meme:\n{res.stderr}")

        return out_path


class VideoMemeOverlay:
    """
    FFmpeg filter helper for Video Memes:
    - Green Screen (Chroma-Key) overlay with colorkey filter
    - Cut-in video overlay with original meme sound
    """
    @staticmethod
    def build_chromakey_filter(
        input_idx: int,
        start: float,
        end: float,
        scale: int = 500,
        pos_y: int = 860,
        key_color: str = "0x00FF00",
        similarity: float = 0.3,
        blend: float = 0.1
    ) -> Dict[str, str]:
        """
        Generates FFmpeg filter string for removing green background and overlaying on timeline.
        """
        label_in = f"[{input_idx}:v]"
        label_out = f"[chroma_{input_idx}]"

        filter_str = (
            f"{label_in}colorkey={key_color}:{similarity}:{blend},"
            f"scale={scale}:-1,format=rgba,"
            f"fade=t=in:st={start}:d=0.2:alpha=1,fade=t=out:st={end-0.2}:d=0.2:alpha=1{label_out}"
        )

        overlay_expr = f"(W-w)/2:{pos_y}:enable='between(t,{start},{end})'"

        return {
            "filter": filter_str,
            "label_out": label_out,
            "overlay_expr": overlay_expr
        }
