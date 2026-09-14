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


def build_episode_3():
    print("=" * 60)
    print("🚀 НАЧАЛО СБОРКИ ВЫПУСКА №3 (Far Cry 6: Смертоносная Дверь)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/6] Подготовка файловой структуры в output/3/...")
    mgr = EpisodeOutputManager("3")
    paths = mgr.get_paths("door_kill_glitch.mp4")

    gameplay_src = ASSETS_DIR / "downloads" / "cyberpunk_door_kill.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    diag1_path = mgr.visuals_dir / "step1_door.png"
    diag2_path = mgr.visuals_dir / "step2_impact.png"
    code_path = mgr.visuals_dir / "door_fix_card.png"

    # Contextual Memes (High Quality Comic/Photo Framed Memes)
    meme_fbi = ASSETS_DIR / "memes" / "fbi_framed.png"
    meme_wasted = ASSETS_DIR / "memes" / "wasted_framed.png"
    meme_belaz = ASSETS_DIR / "memes" / "belaz_framed.png"

    # SFX from MyInstants
    sfx_metal_pipe = ASSETS_DIR / "sfx" / "metal_pipe.mp3"
    sfx_wasted = ASSETS_DIR / "sfx" / "gta_wasted.mp3"
    sfx_vine_boom = ASSETS_DIR / "sfx" / "vine_boom.mp3"
    sfx_win_error = ASSETS_DIR / "sfx" / "windows_error.mp3"
    sfx_mario = ASSETS_DIR / "sfx" / "mario_1up.mp3"

    # Ambient Music
    ambient_dir = ASSETS_DIR / "music" / "ambient"
    bgm_path = get_random_bgm(ambient_dir)
    print(f"   ✓ Фоновый эмбиент: {bgm_path.name}")

    # 2. Scene-based TTS Blocks Definition
    print("\n[2/6] Генерация озвучки по смысловым блокам...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+8%")

    scene_blocks_def = [
        {
            "id": "hook",
            "text": "Вы спасли важного повстанца из тюрьмы и отбили десять волн спецназа...",
            "trigger_bgm": False
        },
        {
            "id": "fail",
            "text": "И тут его насмерть сбивает обычная комнатная дверь! Миссия с треском провалена!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Начинаем расследование: как дверная створка превратилась в самого смертоносного киллера в игре?",
            "trigger_bgm": True
        },
        {
            "id": "step1",
            "text": "Оказывается, анимация открывания двигала дверь как кинематический объект с абсолютно бесконечной массой.",
            "trigger_bgm": False
        },
        {
            "id": "step2",
            "text": "В момент контакта движок посчитал это как лобовой таран БелАЗом на скорости двести километров в час и нанёс девять тысяч урона за один тик!",
            "trigger_bgm": False
        },
        {
            "id": "fix",
            "text": "Исправляется это элементарно: дверь должна проверять препятствия и не наносить физический урон союзникам.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Мораль: никогда не бегите впереди двери, если её программировали за ночь до релиза! Подписывайся на канал!",
            "trigger_bgm": False
        }
    ]

    block_timings = {}
    current_time = 0.0
    all_subtitle_events = []
    block_audio_paths = []
    bgm_start_time = 0.0

    for idx, b in enumerate(scene_blocks_def):
        b_id = b["id"]
        b_audio = mgr.voice_dir / f"block_{idx+1}_{b_id}.mp3"
        res = tts.generate_speech(b["text"], b_audio)
        events = res["events"]
        b_dur = events[-1]["end"] + 0.35 if events else 3.0

        b_start = current_time
        b_end = current_time + b_dur

        if b["trigger_bgm"] and bgm_start_time == 0.0:
            bgm_start_time = b_start

        block_timings[b_id] = {
            "start": b_start,
            "end": b_end,
            "duration": b_dur,
            "audio": b_audio
        }

        # Shift subtitles to global timeline
        for ev in events:
            all_subtitle_events.append({
                "text": ev["text"],
                "start": b_start + ev["start"],
                "end": b_start + ev["end"]
            })

        block_audio_paths.append(b_audio)
        current_time = b_end + 0.15  # Small natural pause between blocks

    total_duration = current_time + 0.5
    print(f"   ✓ Сгенерировано {len(scene_blocks_def)} речевых блоков.")
    print(f"   ✓ Общая длительность: {total_duration:.2f} сек.")
    print(f"   ✓ Старт эмбиента (блок расследования): {bgm_start_time:.2f} сек.")

    # Concat block audio files into voice.mp3
    concat_list_file = mgr.temp_dir / "voice_concat.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f_concat:
        for b_path in block_audio_paths:
            f_concat.write(f"file '{b_path.resolve().as_posix()}'\n")

    cmd_concat = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(voice_final_path)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # 3. Dynamic Subtitles (.ass)
    print("\n[3/6] Генерация стилизованных субтитров...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",  # Yellow
        outline_width=5,
        margin_v=160
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visual Cards
    print("\n[4/6] Генерация графических схем и карточки кода...")
    vis_gen = Episode2VisualsGenerator(width=1000, height=560)
    vis_gen.generate_step1_door(diag1_path)
    vis_gen.generate_step2_impact(diag2_path)
    vis_gen.generate_door_fix_card(code_path)

    # 5. Background Video with Freeze Frame
    print("\n[5/6] Подготовка фона с геймплеем (9:16)...")
    prepare_gameplay_background(gameplay_src, cut_time=5.3, total_duration=total_duration, output_bg=temp_bg)

    # 6. Composite Layers in FFmpeg
    print(f"\n[6/6] Сборка видеоряда и аудиодорожек в FFmpeg...")

    # Calculate exact dynamic timings for overlays
    fail_start = block_timings["fail"]["start"]
    fail_mid = fail_start + (block_timings["fail"]["duration"] * 0.45)
    fail_end = block_timings["fail"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    step1_start = block_timings["step1"]["start"]
    step1_end = block_timings["step1"]["end"]

    step2_start = block_timings["step2"]["start"]
    step2_mid = step2_start + (block_timings["step2"]["duration"] * 0.5)
    step2_end = block_timings["step2"]["end"]

    fix_start = block_timings["fix"]["start"]
    fix_end = block_timings["fix"]["end"]

    # SFX Delays in ms
    pipe_delay_ms = int(max(0, fail_start * 1000))
    wasted_delay_ms = int(max(0, fail_mid * 1000))
    inv_boom_delay_ms = int(max(0, inv_start * 1000))
    winerr_delay_ms = int(max(0, step1_start * 1000))
    belaz_boom_delay_ms = int(max(0, step2_start * 1000))
    mario_delay_ms = int(max(0, fix_start * 1000))
    bgm_delay_ms = int(max(0, bgm_start_time * 1000))

    # Inputs list for FFmpeg:
    # 0: temp_bg (video)
    # 1: voice_final (audio)
    # 2: bgm (audio)
    # 3: sfx_metal_pipe (audio)
    # 4: sfx_wasted (audio)
    # 5: sfx_vine_boom (audio)
    # 6: sfx_win_error (audio)
    # 7: sfx_mario (audio)
    # 8: meme_fbi (image)
    # 9: meme_wasted (image)
    # 10: meme_belaz (image)
    # 11: diag1 (image)
    # 12: diag2 (image)
    # 13: code_card (image)

    filter_chains = [
        # Meme 1: FBI SWAT Breach Meme (Fail Start to Fail Mid, lower half y=840)
        f"[8:v]scale=960:-1,format=rgba,fade=t=in:st={fail_start:.2f}:d=0.2:alpha=1,fade=t=out:st={fail_mid-0.2:.2f}:d=0.2:alpha=1[m_fbi]",
        f"[0:v][m_fbi]overlay=(W-w)/2:840:enable='between(t,{fail_start:.2f},{fail_mid:.2f})'[v1]",

        # Meme 2: Wasted / Mission Failed (Fail Mid to Fail End, lower half y=840)
        f"[9:v]scale=960:-1,format=rgba,fade=t=in:st={fail_mid:.2f}:d=0.2:alpha=1,fade=t=out:st={fail_end-0.2:.2f}:d=0.2:alpha=1[m_wasted]",
        f"[v1][m_wasted]overlay=(W-w)/2:840:enable='between(t,{fail_mid:.2f},{fail_end:.2f})'[v2]",

        # Diagram Step 1: Kinematic Door (Step 1 block, lower half y=840)
        f"[11:v]scale=980:-1,format=rgba,fade=t=in:st={step1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={step1_end-0.25:.2f}:d=0.25:alpha=1[v_d1]",
        f"[v2][v_d1]overlay=(W-w)/2:840:enable='between(t,{step1_start:.2f},{step1_end:.2f})'[v3]",

        # Step 2 Part A: Diagram 2 Impact (step2_start to step2_mid, lower half y=840)
        f"[12:v]scale=980:-1,format=rgba,fade=t=in:st={step2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={step2_mid-0.25:.2f}:d=0.25:alpha=1[v_d2]",
        f"[v3][v_d2]overlay=(W-w)/2:840:enable='between(t,{step2_start:.2f},{step2_mid:.2f})'[v4]",

        # Step 2 Part B: BelAZ Ram Meme (step2_mid to step2_end, lower half y=840)
        f"[10:v]scale=960:-1,format=rgba,fade=t=in:st={step2_mid:.2f}:d=0.25:alpha=1,fade=t=out:st={step2_end-0.25:.2f}:d=0.25:alpha=1[v_belaz]",
        f"[v4][v_belaz]overlay=(W-w)/2:840:enable='between(t,{step2_mid:.2f},{step2_end:.2f})'[v5]",

        # Code Fix Card (Fix block, lower half y=840)
        f"[13:v]scale=980:-1,format=rgba,fade=t=in:st={fix_start:.2f}:d=0.25:alpha=1,fade=t=out:st={fix_end-0.25:.2f}:d=0.25:alpha=1[v_fix]",
        f"[v5][v_fix]overlay=(W-w)/2:840:enable='between(t,{fix_start:.2f},{fix_end:.2f})'[v6]"
    ]

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v6]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing:
    # 1: voice (vol=1.0)
    # 2: bgm (vol=0.14) delayed to investigation
    # 3: metal pipe (vol=0.35)
    # 4: wasted (vol=0.4)
    # 5: vine boom (vol=0.3)
    # 6: windows error (vol=0.3)
    # 7: mario 1up (vol=0.35)
    filter_chains.append(
        f"[1:a]volume=1.0[a_voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[3:a]adelay={pipe_delay_ms}|{pipe_delay_ms},volume=0.35[a_pipe];"
        f"[4:a]adelay={wasted_delay_ms}|{wasted_delay_ms},volume=0.40[a_wasted];"
        f"[5:a]adelay={inv_boom_delay_ms}|{inv_boom_delay_ms},volume=0.30[a_boom];"
        f"[6:a]adelay={winerr_delay_ms}|{winerr_delay_ms},volume=0.30[a_winerr];"
        f"[7:a]adelay={mario_delay_ms}|{mario_delay_ms},volume=0.35[a_mario];"
        f"[a_voice][a_bgm][a_pipe][a_wasted][a_boom][a_winerr][a_mario]amix=inputs=7:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_metal_pipe),
        "-i", str(sfx_wasted),
        "-i", str(sfx_vine_boom),
        "-i", str(sfx_win_error),
        "-i", str(sfx_mario),
        "-loop", "1", "-i", str(meme_fbi),
        "-loop", "1", "-i", str(meme_wasted),
        "-loop", "1", "-i", str(meme_belaz),
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

    # Generate preview frames in output/3/frames/
    print("\n📸 Генерация превью-кадров в output/3/frames/...")
    frame_times = [1.0, fail_start + 0.5, fail_mid + 0.5, inv_start + 0.5, step1_start + 0.5, step2_start + 0.5, fix_start + 0.5]
    for idx, t in enumerate(frame_times):
        if t < total_duration:
            f_path = mgr.frames_dir / f"frame_{idx+1}_{t:.1f}s.jpg"
            f_cmd = [
                FFMPEG_PATH, "-y",
                "-ss", str(t),
                "-i", str(final_video),
                "-vframes", "1",
                "-q:v", "2",
                str(f_path)
            ]
            subprocess.run(f_cmd, capture_output=True)

    print(f"\n✨ [УСПЕХ] ВЫПУСК №3 СОБРАН И СОХРАНЕН В: {final_video}")
    return final_video, block_timings, total_duration, bgm_path.name


if __name__ == "__main__":
    build_episode_3()
