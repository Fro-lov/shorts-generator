import sys
import io
import subprocess
from pathlib import Path

# Set UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config.settings import ASSETS_DIR, FFMPEG_PATH, DEFAULT_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode2_visuals import Episode2VisualsGenerator
from src.core.output_manager import EpisodeOutputManager
from src.core.music_generator import get_random_bgm


def prepare_gameplay_background(gameplay_mp4: Path, cut_time: float, total_duration: float, output_bg: Path) -> Path:
    """
    Creates a full 9:16 background from 16:9 gameplay:
    - 0 to cut_time: plays real gameplay
    - cut_time to total_duration: freezes cleanly on the dead NPC
    """
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", "00:00:00",
        "-to", f"00:00:{cut_time:04.1f}",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=22:6[bg];"
        f"[0:v]scale=1020:-1[fg];"
        f"[bg][fg]overlay=(W-w)/2:220[v_comp];"
        f"[v_comp]tpad=stop_mode=clone:stop_duration={max(0, total_duration - cut_time)}[v_out]",
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
        raise RuntimeError(f"Failed creating episode 2 background: {res.stderr}")
    return output_bg


def build_episode_2():
    print("[1/6] Подготовка окружения для Выпуска №2...")
    mgr = EpisodeOutputManager("2")
    paths = mgr.get_paths("door_kill_glitch.mp4")

    gameplay_src = ASSETS_DIR / "downloads" / "cyberpunk_door_kill.mp4"
    audio_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    diag1_path = mgr.visuals_dir / "step1_door.png"
    diag2_path = mgr.visuals_dir / "step2_impact.png"
    code_path = mgr.visuals_dir / "door_fix_card.png"

    # Audio assets
    ambient_dir = ASSETS_DIR / "music" / "ambient"
    bgm_path = get_random_bgm(ambient_dir)
    bell_sfx_path = ASSETS_DIR / "music" / "колокольня.mp3"

    # Memes
    meme_ispug = ASSETS_DIR / "memes" / "испуг.jpg"
    meme_krest = ASSETS_DIR / "memes" / "святой_крест.jfif"
    meme_splyushilo = ASSETS_DIR / "memes" / "сплющило.jpg"

    script_text = (
        "Вы спасли важного повстанца из тюрьмы, отбили десять волн спецназа... "
        "И тут его насмерть сбивает обычная межкомнатная дверь! Миссия провалена! "
        "Начинаем расследование: как дверь стала самым смертоносным киллером в игре? "
        "Оказывается, анимация открытия двигала дверь с бесконечной массой. "
        "Когда створка коснулась NPC, движок посчитал это как лобовой таран БелАЗом на скорости двести километров в час и списал всё здоровье за один миллисекундный тик! "
        "Мораль проста: никогда не бегите впереди двери, если её программировали в спешке к релизу!"
    )

    # 1. TTS Synthesis
    print("[2/6] Синтез озвучки (Edge-TTS)...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+8%")
    tts_res = tts.generate_speech(script_text, audio_path)
    events = tts_res["events"]
    total_duration = events[-1]["end"] + 1.0
    print(f"   ✓ Длительность озвучки: {total_duration:.2f} сек.")

    # Find the exact timestamp of "Начинаем расследование"
    investigation_start = 8.0
    for ev in events:
        if "расследование" in ev["text"].lower() or "киллером" in ev["text"].lower():
            investigation_start = max(6.0, ev["start"] - 0.5)
            break
    print(f"   ✓ Точка старта эмбиента (после хука): {investigation_start:.2f} сек.")

    # 2. Dynamic Subtitles
    print("[3/6] Генерация динамических субтитров...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",  # Yellow
        outline_width=5,
        margin_v=160
    )
    sub_gen.generate_ass_file(events, ass_path, max_words_per_line=3)

    # 3. Visuals Generation
    print("[4/6] Генерация 2D схем и карточки фикса...")
    vis_gen = Episode2VisualsGenerator(width=1000, height=560)
    vis_gen.generate_step1_door(diag1_path)
    vis_gen.generate_step2_impact(diag2_path)
    vis_gen.generate_door_fix_card(code_path)

    # 4. Background with freeze-frame
    print("[5/6] Подготовка видеоряда с геймплеем...")
    prepare_gameplay_background(gameplay_src, cut_time=5.3, total_duration=total_duration, output_bg=temp_bg)

    # 5. Composite Layers in FFmpeg
    print(f"[6/6] Монтаж финального ролика (фоновый трек: {bgm_path.name})...")
    bgm_delay_ms = int(investigation_start * 1000)

    filter_chains = [
        # Meme 1: Ispug in LOWER half (0.4s to 2.2s, y=860)
        f"[4:v]scale=540:-1,format=rgba,fade=t=in:st=0.4:d=0.25:alpha=1,fade=t=out:st=2.0:d=0.25:alpha=1[m1]",
        f"[0:v][m1]overlay=(W-w)/2:860:enable='between(t,0.4,2.2)'[v1]",

        # Meme 2: Krest in LOWER half (2.3s to 4.3s, y=860) + Bell Sound
        f"[5:v]scale=520:-1,format=rgba,fade=t=in:st=2.3:d=0.25:alpha=1,fade=t=out:st=4.1:d=0.25:alpha=1[m2]",
        f"[v1][m2]overlay=(W-w)/2:860:enable='between(t,2.3,4.3)'[v2]",

        # Meme 3: Splyushilo in LOWER half (4.5s to 8.0s, y=860)
        f"[6:v]scale=720:-1,format=rgba,fade=t=in:st=4.5:d=0.3:alpha=1,fade=t=out:st=7.8:d=0.3:alpha=1[m3]",
        f"[v2][m3]overlay=(W-w)/2:860:enable='between(t,4.5,8.0)'[v3]",

        # Diagram Step 1 (8.0s to 14.0s)
        f"[7:v]scale=980:-1,format=rgba,fade=t=in:st=8.0:d=0.3:alpha=1,fade=t=out:st=13.7:d=0.3:alpha=1[diag1]",
        f"[v3][diag1]overlay=(W-w)/2:840:enable='between(t,8.0,14.0)'[v4]",

        # Diagram Step 2 (14.0s to 20.0s)
        f"[8:v]scale=980:-1,format=rgba,fade=t=in:st=14.0:d=0.3:alpha=1,fade=t=out:st=19.7:d=0.3:alpha=1[diag2]",
        f"[v4][diag2]overlay=(W-w)/2:840:enable='between(t,14.0,20.0)'[v5]",

        # Simple Code Fix Card (20.0s to 29.0s)
        f"[9:v]scale=980:-1,format=rgba,fade=t=in:st=20.0:d=0.3:alpha=1,fade=t=out:st=28.7:d=0.3:alpha=1[code]",
        f"[v5][code]overlay=(W-w)/2:840:enable='between(t,20.0,29.0)'[v6]"
    ]

    # Subtitles filter
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v6]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing:
    # 1: voice (vol=1.0)
    # 2: bgm (delayed to investigation start, vol=0.15)
    # 3: bell sfx (delayed to 2.3s, vol=0.25)
    filter_chains.append(
        f"[1:a]volume=1.0[voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.15[bgm];"
        f"[3:a]adelay=2300|2300,volume=0.25[bell];"
        f"[voice][bgm][bell]amix=inputs=3:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(audio_path),
        "-i", str(bgm_path),
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

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render error:\n{res.stderr}")

    print(f"\n[OK] ВЫПУСК №2 УСПЕШНО СОБРАН: {final_video}")
    return final_video


if __name__ == "__main__":
    build_episode_2()
