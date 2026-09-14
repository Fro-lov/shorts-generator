import sys
import io

# Set UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
from pathlib import Path
from config.settings import OUTPUT_DIR, DEFAULT_VOICE
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.code_card import CodeCardGenerator
from src.core.compositor import VideoCompositor


def generate_demo_preview():
    print("[1/5] Инициализация генератора тестового видео...")

    game_title = "Civilization (1991)"
    bug_name = "Ядерный Ганди: Underflow ошибка"

    script_text = (
        "Почему миролюбивый Ганди в первой Цивилизации внезапно начинал ядерную войну? "
        "В коде игры его базовая агрессия равнялась единице. "
        "Но когда Индия принимала демократию, уровень агрессии снижался на два пункта. "
        "Переменная была беззнаковым восьмибитным числом, поэтому один минус два давало двести пятьдесят пять! "
        "Ганди мгновенно превращался в самого опасного маньяка на карте."
    )

    audio_path = OUTPUT_DIR / "demo_voice.mp3"
    ass_path = OUTPUT_DIR / "demo_subtitles.ass"
    card_path = OUTPUT_DIR / "demo_code_card.png"
    final_video_path = OUTPUT_DIR / "demo_preview.mp4"

    # Step 1: TTS Generation
    print("[2/5] Генерация озвучки через Edge-TTS...")
    tts = TTSEngine(voice=DEFAULT_VOICE)
    tts_result = tts.generate_speech(script_text, audio_path)

    events = tts_result["events"]
    total_duration = events[-1]["end"] + 0.8 if events else 15.0
    print(f"   ✓ Аудио сгенерировано. Длительность: {total_duration:.2f} сек.")

    # Step 2: Dynamic Subtitles
    print("[3/5] Генерация динамических субтитров (ASS)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",  # Bright Yellow
        outline_width=5,
        margin_v=240
    )
    sub_gen.generate_ass_file(events, ass_path, max_words_per_line=3)
    print(f"   ✓ Субтитры сохранены: {ass_path}")

    # Step 3: Code Card Generator
    print("[4/5] Генерация карточки с кодом бага и фикса...")
    code_gen = CodeCardGenerator(width=980)
    code_lines = [
        {"text": "uint8_t aggression = 1; // Base Gandhi peace", "type": "normal", "line_no": "42"},
        {"text": "aggression -= 2; // BUG: 1 - 2 = 255 (Underflow!)", "type": "bug", "line_no": "43"},
        {"text": "int aggression = 1;", "type": "normal", "line_no": "42"},
        {"text": "aggression = max(0, aggression - 2); // FIX", "type": "fix", "line_no": "43"}
    ]
    code_gen.generate_card("civilization_ai.c (Underflow Bug)", code_lines, card_path)
    print(f"   ✓ Карточка кода сгенерирована: {card_path}")

    # Step 4: Video Composition
    print("[5/5] Монтаж итогового видео через FFmpeg...")
    compositor = VideoCompositor()

    # Code card shows during technical explanation (e.g. from 6.0s to 18.0s)
    card_timing = {
        "start": 6.5,
        "end": min(total_duration - 2.0, 18.5)
    }

    compositor.render_clip(
        duration=total_duration,
        audio_path=audio_path,
        ass_subtitles_path=ass_path,
        output_video_path=final_video_path,
        background_video=None,  # Will use auto-generated stylish placeholder!
        game_title=game_title,
        bug_name=bug_name,
        code_card_img=card_path,
        code_card_timing=card_timing
    )

    print(f"\n[OK] ГОТОВО! Видео сохранено в: {final_video_path}")
    return final_video_path


if __name__ == "__main__":
    generate_demo_preview()
