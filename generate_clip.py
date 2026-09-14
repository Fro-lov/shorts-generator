import sys
import io
import json
import argparse
from pathlib import Path

# Fix Windows console UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config.settings import OUTPUT_DIR, DEFAULT_VOICE
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.code_card import CodeCardGenerator
from src.core.compositor import VideoCompositor


def build_clip_from_manifest(manifest: dict, output_filename: str = "final_short.mp4") -> Path:
    """
    Renders a complete short-form video from a JSON scenario manifest.
    Manifest format:
    {
        "game_title": "Skyrim",
        "bug_name": "Ведра на головах торговцев",
        "script": "Текст озвучки...",
        "gameplay_video": "path/to/gameplay.mp4" (optional),
        "code_card": {
            "title": "stealth_detection.cpp",
            "lines": [
                {"text": "if (is_line_of_sight_blocked())", "type": "bug", "line_no": "104"},
                {"text": "if (is_valid_occluder(bucket))", "type": "fix", "line_no": "104"}
            ],
            "start_time": 8.0,
            "end_time": 20.0
        }
    }
    """
    game_title = manifest.get("game_title", "РАЗБОР БАГА")
    bug_name = manifest.get("bug_name", "Геймплейный глитч")
    script_text = manifest["script"]
    voice = manifest.get("voice", DEFAULT_VOICE)
    gameplay_video = manifest.get("gameplay_video")

    slug = "".join(c if c.isalnum() else "_" for c in bug_name.lower())[:25]
    audio_path = OUTPUT_DIR / f"{slug}_voice.mp3"
    ass_path = OUTPUT_DIR / f"{slug}_subtitles.ass"
    card_path = OUTPUT_DIR / f"{slug}_code.png"
    output_video_path = OUTPUT_DIR / output_filename

    print(f"[*] Генерация ролика для: {game_title} - {bug_name}")

    # 1. TTS
    print("  [1/4] Синтез речи (Edge-TTS)...")
    tts = TTSEngine(voice=voice)
    tts_result = tts.generate_speech(script_text, audio_path)
    events = tts_result["events"]
    total_duration = events[-1]["end"] + 0.8 if events else 15.0

    # 2. Subtitles
    print("  [2/4] Формирование субтитров...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",  # Yellow
        outline_width=5,
        margin_v=240
    )
    sub_gen.generate_ass_file(events, ass_path, max_words_per_line=3)

    # 3. Code Card
    card_timing = None
    if "code_card" in manifest and manifest["code_card"].get("lines"):
        print("  [3/4] Рендеринг карточки с кодом...")
        c_info = manifest["code_card"]
        code_gen = CodeCardGenerator(width=980)
        code_gen.generate_card(c_info.get("title", "code_snippet.cpp"), c_info["lines"], card_path)
        card_timing = {
            "start": float(c_info.get("start_time", 6.0)),
            "end": float(c_info.get("end_time", min(total_duration - 2.0, 18.0)))
        }

    # 4. Composite
    print("  [4/4] Финальный монтаж видео...")
    compositor = VideoCompositor()
    compositor.render_clip(
        duration=total_duration,
        audio_path=audio_path,
        ass_subtitles_path=ass_path,
        output_video_path=output_video_path,
        background_video=Path(gameplay_video) if gameplay_video else None,
        game_title=game_title,
        bug_name=bug_name,
        code_card_img=card_path if card_timing else None,
        code_card_timing=card_timing,
        memes=manifest.get("memes")
    )

    print(f"[+] Успешно скомпилировано видео: {output_video_path}")
    return output_video_path


def main():
    parser = argparse.ArgumentParser(description="Автоматический генератор коротких видео (Shorts/TikTok)")
    parser.add_argument("--manifest", type=str, help="Путь к JSON файлу сценария")
    parser.add_argument("--output", type=str, default="rendered_short.mp4", help="Имя выходного файла")
    args = parser.parse_args()

    if args.manifest:
        with open(args.manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        build_clip_from_manifest(data, args.output)
    else:
        print("Используйте --manifest scenario.json или запустите python preview_demo.py")


if __name__ == "__main__":
    main()
