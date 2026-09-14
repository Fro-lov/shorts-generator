import sys
import io
import subprocess
from pathlib import Path

# Set UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config.settings import OUTPUT_DIR, ASSETS_DIR, FFMPEG_PATH, DEFAULT_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.simplified_visuals import SimplifiedVisualsGenerator
from src.core.music_generator import generate_investigation_bgm


def prepare_cyberpunk_background(gameplay_mp4: Path, total_duration: float, output_bg: Path) -> Path:
    """
    Creates a full 9:16 background from the 16:9 gameplay:
    - 0 to 4.0s: plays real gameplay (stops before WDF logo)
    - 4.0s to total_duration: freezes on the flat squashed car
    """
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", "00:00:00",
        "-to", "00:00:04.0",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=22:6[bg];"
        f"[0:v]scale=1020:-1[fg];"
        f"[bg][fg]overlay=(W-w)/2:220[v_comp];"
        f"[v_comp]tpad=stop_mode=clone:stop_duration={max(0, total_duration - 4.0)}[v_out]",
        "-map", "[v_out]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-t", str(total_duration),
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed creating cyberpunk background: {res.stderr}")
    return output_bg


def build_cyberpunk_video():
    print("[1/6] Подготовка сценария и ресурсов...")
    gameplay_src = ASSETS_DIR / "downloads" / "cyberpunk_car.mp4"
    audio_path = OUTPUT_DIR / "cyberpunk_voice.mp3"
    music_path = ASSETS_DIR / "music" / "investigation_ambient.wav"
    bell_sfx_path = ASSETS_DIR / "music" / "колокольня.mp3"
    ass_path = OUTPUT_DIR / "cyberpunk_subtitles.ass"
    
    diag1_path = OUTPUT_DIR / "diagram_step1.png"
    diag2_path = OUTPUT_DIR / "diagram_step2.png"
    code_path = OUTPUT_DIR / "simple_fix_card.png"

    temp_bg = OUTPUT_DIR / "cyberpunk_bg.mp4"
    final_video = OUTPUT_DIR / "cyberpunk_2077_car_glitch.mp4"

    # Ensure background music exists
    if not music_path.exists():
        generate_investigation_bgm(music_path, duration=50.0)

    # Memes
    meme_ispug = ASSETS_DIR / "memes" / "испуг.jpg"
    meme_krest = ASSETS_DIR / "memes" / "святой_крест.jfif"
    meme_splyushilo = ASSETS_DIR / "memes" / "сплющило.jpg"

    script_text = (
        "В Найт-Сити законы физики вышли из чата! "
        "Игрок просто хотел припарковаться, но машина решила схлопнуться в двухмерное измерение. "
        "Поздравляем, теперь у вас не спорткар, а коврик для мыши! "
        "Почему так произошло? Движок PhysX на высокой скорости не успел рассчитать коллизию и меш проник внутрь барьера. "
        "Алгоритм деформации попытался вытолкнуть вершины обратно, но перепутал коэффициенты и сжал всю геометрию по оси Z ровно в ноль! "
        "В коде банально забыли поставить ограничитель минимальной толщины кузова. "
        "Зато теперь у машины идеальная аэродинамика!"
    )

    # 1. Voiceover (TTS) with lively rate (+8%)
    print("[2/6] Синтез озвучки (Edge-TTS)...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+8%")
    tts_res = tts.generate_speech(script_text, audio_path)
    events = tts_res["events"]
    total_duration = events[-1]["end"] + 1.0
    print(f"   ✓ Длительность озвучки: {total_duration:.2f} сек.")

    # 2. Subtitles
    print("[3/6] Генерация динамических субтитров...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",  # Yellow
        outline_width=5,
        margin_v=160
    )
    sub_gen.generate_ass_file(events, ass_path, max_words_per_line=3)

    # 3. Simple Visual Cards Generator
    print("[4/6] Генерация наглядных 2D схем и карточки фикса...")
    vis_gen = SimplifiedVisualsGenerator(width=1000, height=560)
    vis_gen.generate_step1_penetration(diag1_path)
    vis_gen.generate_step2_collapse(diag2_path)
    vis_gen.generate_simple_fix_card(code_path)

    # 4. Background with cut at 4.0s (before WDF) and freeze-frame extension
    print("[5/6] Подготовка видеоряда...")
    prepare_cyberpunk_background(gameplay_src, total_duration, temp_bg)

    # 5. FFmpeg Composite
    # Inputs:
    # 0: temp_bg (video)
    # 1: voice (audio)
    # 2: bgm (audio)
    # 3: bell sfx (audio)
    # 4: meme ispug (loop 1)
    # 5: meme krest (loop 1)
    # 6: meme splyushilo (loop 1)
    # 7: diagram step 1 (loop 1)
    # 8: diagram step 2 (loop 1)
    # 9: simple fix card (loop 1)

    print("[6/6] Сборка видеоряда со звуковыми эффектами и слоями...")
    filter_chains = [
        # Meme 1: Ispug in LOWER half (0.4s to 2.2s, y=860) - doesn't block gameplay!
        f"[4:v]scale=540:-1,format=rgba,fade=t=in:st=0.4:d=0.25:alpha=1,fade=t=out:st=2.0:d=0.25:alpha=1[m1]",
        f"[0:v][m1]overlay=(W-w)/2:860:enable='between(t,0.4,2.2)'[v1]",

        # Meme 2: Krest in LOWER half (2.3s to 4.3s, y=860) - doesn't block gameplay!
        f"[5:v]scale=520:-1,format=rgba,fade=t=in:st=2.3:d=0.25:alpha=1,fade=t=out:st=4.1:d=0.25:alpha=1[m2]",
        f"[v1][m2]overlay=(W-w)/2:860:enable='between(t,2.3,4.3)'[v2]",

        # Meme 3: Splyushilo in LOWER half (4.5s to 8.5s, y=860)
        f"[6:v]scale=720:-1,format=rgba,fade=t=in:st=4.5:d=0.3:alpha=1,fade=t=out:st=8.2:d=0.3:alpha=1[m3]",
        f"[v2][m3]overlay=(W-w)/2:860:enable='between(t,4.5,8.5)'[v3]",

        # Diagram Step 1 (8.5s to 13.5s)
        f"[7:v]scale=980:-1,format=rgba,fade=t=in:st=8.5:d=0.3:alpha=1,fade=t=out:st=13.2:d=0.3:alpha=1[diag1]",
        f"[v3][diag1]overlay=(W-w)/2:840:enable='between(t,8.5,13.5)'[v4]",

        # Diagram Step 2 (13.5s to 18.5s)
        f"[8:v]scale=980:-1,format=rgba,fade=t=in:st=13.5:d=0.3:alpha=1,fade=t=out:st=18.2:d=0.3:alpha=1[diag2]",
        f"[v4][diag2]overlay=(W-w)/2:840:enable='between(t,13.5,18.5)'[v5]",

        # Simple Code Card (18.5s to 27.0s)
        f"[9:v]scale=980:-1,format=rgba,fade=t=in:st=18.5:d=0.3:alpha=1,fade=t=out:st=26.7:d=0.3:alpha=1[code]",
        f"[v5][code]overlay=(W-w)/2:840:enable='between(t,18.5,27.0)'[v6]"
    ]

    # Subtitles filter
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v6]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing:
    # 1: voice (vol=1.0)
    # 2: bgm (vol=0.15)
    # 3: bell sfx (delayed to 2.3s, vol=0.30)
    filter_chains.append(
        f"[1:a]volume=1.0[voice];"
        f"[2:a]volume=0.15[bgm];"
        f"[3:a]adelay=2300|2300,volume=0.30[bell];"
        f"[voice][bgm][bell]amix=inputs=3:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(audio_path),
        "-i", str(music_path),
        "-i", str(bell_sfx_path),
        "-loop", "1", "-i", str(meme_ispug),
        "-loop", "1", "-i", str(meme_krest),
        "-loop", "1", "-i", str(meme_splyushilo),
        "-loop", "1", "-i", str(diag1_path),
        "-loop", "1", "-i", str(diag2_path),
        "-loop", "1", "-i", str(code_path),
        "-filter_complex", full_filter,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(total_duration),
        "-pix_fmt", "yuv420p",
        str(final_video)
    ]

    print("[*] Рендеринг финального ролика...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render error:\n{res.stderr}")

    print(f"\n[OK] ВИДЕО УСПЕШНО СОБРАНО: {final_video}")
    return final_video


if __name__ == "__main__":
    build_cyberpunk_video()
