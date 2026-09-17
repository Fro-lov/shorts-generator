import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any
import edge_tts
from config.settings import DEFAULT_VOICE, OUTPUT_DIR


class TTSEngine:
    def __init__(self, voice: str = DEFAULT_VOICE, rate: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    async def generate_speech_async(
        self,
        text: str,
        output_audio_path: Path
    ) -> Dict[str, Any]:
        """
        Generates TTS audio and extracts sentence boundaries with timestamps.
        """
        output_audio_path = Path(output_audio_path)
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=self.voice,
                    rate=self.rate,
                    pitch=self.pitch
                )

                sub_events: List[Dict[str, Any]] = []
                audio_chunks = []

                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                    elif chunk["type"] == "SentenceBoundary":
                        # offset and duration are in 100-nanosecond units (1s = 10,000,000 units)
                        start_sec = chunk["offset"] / 10_000_000.0
                        duration_sec = chunk["duration"] / 10_000_000.0
                        end_sec = start_sec + duration_sec
                        sub_events.append({
                            "type": chunk["type"],
                            "text": chunk["text"],
                            "start": start_sec,
                            "end": end_sec,
                            "duration": duration_sec
                        })

                if not audio_chunks:
                    raise edge_tts.exceptions.NoAudioReceived("No audio chunks received.")

                with open(output_audio_path, "wb") as f:
                    for b in audio_chunks:
                        f.write(b)

                return {
                    "audio_path": str(output_audio_path),
                    "events": sub_events
                }
            except Exception as e:
                if attempt == max_retries:
                    raise e
                print(f"      ⚠️ Внимание: сбой Edge-TTS (попытка {attempt}/{max_retries}): {e}. Повтор через 1.5 сек...")
                await asyncio.sleep(1.5)

    def generate_speech(self, text: str, output_audio_path: Path) -> Dict[str, Any]:
        """Synchronous wrapper for generate_speech_async."""
        return asyncio.run(self.generate_speech_async(text, output_audio_path))

