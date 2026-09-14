import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from config.settings import DEFAULT_VOICE


class SceneBlock:
    def __init__(
        self,
        name: str,
        text: str,
        visual_type: str = "gameplay",  # "gameplay", "diagram1", "diagram2", "code_fix", "outro"
        meme_file: Optional[str] = None,
        sfx_file: Optional[str] = None,
        trigger_bgm: bool = False
    ):
        self.name = name
        self.text = text
        self.visual_type = visual_type
        self.meme_file = meme_file
        self.sfx_file = sfx_file
        self.trigger_bgm = trigger_bgm


class SceneTimelineBuilder:
    """
    Builds a perfectly synchronized timeline where visual transitions, 
    diagrams, memes, and BGM are dynamically locked to exact speech block durations.
    """
    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = "+8%"):
        self.tts = TTSEngine(voice=voice, rate=rate)

    def compile_timeline(self, blocks: List[SceneBlock], output_voice_dir: Path) -> Dict[str, Any]:
        output_voice_dir = Path(output_voice_dir)
        output_voice_dir.mkdir(parents=True, exist_ok=True)

        timeline_events = []
        all_subtitle_events = []
        current_time = 0.0
        bgm_start_time = None

        audio_files = []

        for idx, block in enumerate(blocks):
            block_audio_path = output_voice_dir / f"block_{idx+1}_{block.name}.mp3"
            tts_res = self.tts.generate_speech(block.text, block_audio_path)
            audio_files.append(block_audio_path)

            raw_events = tts_res["events"]
            block_duration = raw_events[-1]["end"] + 0.3 if raw_events else 3.0

            # Adjust subtitle timestamps to global time
            for ev in raw_events:
                all_subtitle_events.append({
                    "text": ev["text"],
                    "start": current_time + ev["start"],
                    "end": current_time + ev["end"]
                })

            block_start = current_time
            block_end = current_time + block_duration

            if block.trigger_bgm and bgm_start_time is None:
                bgm_start_time = block_start

            timeline_events.append({
                "name": block.name,
                "visual_type": block.visual_type,
                "start": block_start,
                "end": block_end,
                "duration": block_duration,
                "meme": block.meme_file,
                "sfx": block.sfx_file,
                "audio_path": block_audio_path
            })

            # Add natural tiny pause (0.2s) between semantic blocks
            current_time = block_end + 0.2

        total_duration = current_time

        return {
            "total_duration": total_duration,
            "bgm_start_time": bgm_start_time if bgm_start_time is not None else 0.0,
            "blocks": timeline_events,
            "subtitle_events": all_subtitle_events,
            "audio_files": audio_files
        }
