import asyncio
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import DEFAULT_VOICE, FFMPEG_PATH

import shutil

def find_edge_tts_cli() -> str:
    cli = shutil.which("edge-tts")
    if cli:
        return cli
    py_scripts = Path(sys.prefix) / "Scripts" / "edge-tts.exe"
    if py_scripts.exists():
        return str(py_scripts)
    default_user_path = Path("C:/Users/onter/AppData/Local/Programs/Python/Python311/Scripts/edge-tts.exe")
    if default_user_path.exists():
        return str(default_user_path)
    return "edge-tts"

EDGE_TTS_CLI = find_edge_tts_cli()

# Dual-voice mapping by role and language
ROLE_VOICE_MAP = {
    "ru": {
        "host": "ru-RU-SvetlanaNeural",
        "expert": "ru-RU-DmitryNeural"
    },
    "en": {
        "host": "en-US-AnaNeural",
        "expert": "en-US-ChristopherNeural"
    }
}

FALLBACK_VOICE_MAP = {
    "ru-RU-DmitryNeural": "ru-RU-SvetlanaNeural",
    "ru-RU-SvetlanaNeural": "ru-RU-DmitryNeural",
    "en-US-ChristopherNeural": "en-US-AnaNeural",
    "en-US-AnaNeural": "en-US-ChristopherNeural"
}


def _get_duration(file_path: Path) -> float:
    cmd = [FFMPEG_PATH, "-i", str(file_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, mn, s = m.groups()
        return int(h) * 3600 + int(mn) * 60 + float(s)
    return 3.0


class TTSEngine:
    def __init__(self, voice: Optional[str] = None, rate: str = "+8%", lang: str = "ru"):
        self.primary_voice = voice
        self.rate = rate
        self.lang = lang

    def get_voice_for_role(self, role: str = "expert") -> str:
        """Returns specific voice according to dual-voice format (host vs expert)."""
        if self.primary_voice:
            return self.primary_voice
        lang_map = ROLE_VOICE_MAP.get(self.lang, ROLE_VOICE_MAP["ru"])
        return lang_map.get(role, "ru-RU-SvetlanaNeural" if role == "host" else "ru-RU-DmitryNeural")

    async def generate_speech_async(
        self,
        text: str,
        output_audio_path: Path,
        role: str = "expert",
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates TTS audio using edge-tts CLI tool with explicit role-based voice assignment and retry resilience.
        """
        output_audio_path = Path(output_audio_path)
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)

        primary_target_voice = voice or (self.primary_voice if self.primary_voice else self.get_voice_for_role(role))
        voices_to_try = [primary_target_voice]
        if primary_target_voice in FALLBACK_VOICE_MAP:
            voices_to_try.append(FALLBACK_VOICE_MAP[primary_target_voice])

        success = False
        used_voice = primary_target_voice

        for curr_voice in voices_to_try:
            for attempt in range(3):
                # 1. Try with rate
                cmd = [
                    EDGE_TTS_CLI,
                    "--voice", curr_voice,
                    "--rate", self.rate,
                    "--text", text,
                    "--write-media", str(output_audio_path.resolve())
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                success = (res.returncode == 0 and output_audio_path.exists() and output_audio_path.stat().st_size > 0)

                # 2. Try without rate if rate command failed
                if not success:
                    cmd = [
                        EDGE_TTS_CLI,
                        "--voice", curr_voice,
                        "--text", text,
                        "--write-media", str(output_audio_path.resolve())
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    success = (res.returncode == 0 and output_audio_path.exists() and output_audio_path.stat().st_size > 0)

                if success:
                    used_voice = curr_voice
                    break
                
                await asyncio.sleep(1.0)

            if success:
                break

        if not success:
            raise RuntimeError(f"Edge-TTS failed for voice {primary_target_voice} (and fallback) after multiple retries")

        dur = _get_duration(output_audio_path)
        words = [w for w in text.split() if w.strip()]
        sub_events: List[Dict[str, Any]] = []

        if words:
            w_dur = dur / len(words)
            for i, w in enumerate(words):
                w_start = i * w_dur
                w_end = (i + 1) * w_dur
                sub_events.append({
                    "type": "WordBoundary",
                    "text": w,
                    "start": w_start,
                    "end": w_end,
                    "duration": w_dur
                })

        return {
            "audio_path": str(output_audio_path),
            "events": sub_events,
            "voice_used": target_voice,
            "role": role
        }

    def generate_speech(self, text: str, output_audio_path: Path, role: str = "expert") -> Dict[str, Any]:
        """Synchronous wrapper for generate_speech_async."""
        return asyncio.run(self.generate_speech_async(text, output_audio_path, role))
