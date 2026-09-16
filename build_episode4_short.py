import sys
import io
import subprocess
from pathlib import Path

# Set UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config.settings import ASSETS_DIR, FFMPEG_PATH, DEFAULT_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS, VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode4_visuals import Episode4VisualsGenerator
from src.core.output_manager import EpisodeOutputManager
from src.core.music_generator import get_random_bgm


def prepare_gameplay_background(gameplay_mp4: Path, cut_time: float, total_duration: float, output_bg: Path, temp_dir: Path) -> Path:
    """
    Creates a full 9:16 background from gameplay:
    - Formats 16:9 gameplay to 9:16 (blurred background + foreground at y=220)
    - Loops the 5-10s gameplay snippet continuously throughout the entire video duration without freezing.
    """
    base_seg = temp_dir / "base_seg.mp4"
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-ss", "00:00:00",
        "-t", f"{cut_time:.2f}",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=22:6[bg];"
        f"[0:v]scale=1020:-1[fg];"
        f"[bg][fg]overlay=(W-w)/2:220[v_comp]",
        "-map", "[v_comp]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(base_seg)
    ]
    subprocess.run(cmd_base, capture_output=True, check=True)

    # Continuous stream loop until total_duration
    cmd_loop = [
        FFMPEG_PATH, "-y",
        "-stream_loop", "-1",
        "-i", str(base_seg),
        "-t", f"{total_duration:.2f}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    subprocess.run(cmd_loop, capture_output=True, check=True)
    return output_bg


def build_episode_4():
    print("=" * 60)
    print("🚀 НАЧАЛО СБОРКИ ВЫПУСКА №4 (Marvel's Avengers: Летающий Стул)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/6] Подготовка файловой структуры в output/4/...")
    mgr = EpisodeOutputManager("4")
    paths = mgr.get_paths("chair_bug_glitch.mp4")

    gameplay_src = ASSETS_DIR / "downloads" / "chair_bug_wide.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    diag1_path = mgr.visuals_dir / "step1_anatomy.png"
    diag2_path = mgr.visuals_dir / "step2_chaos.png"
    code_path = mgr.visuals_dir / "chair_fix_card.png"

    # Contextual Memes
    meme_thor = ASSETS_DIR / "memes" / "thor_framed.png"
    meme_hydra = ASSETS_DIR / "memes" / "hydra_framed.png"

    # SFX
    sfx_vine_boom = ASSETS_DIR / "sfx" / "vine_boom.mp3"
    sfx_thunder = ASSETS_DIR / "sfx" / "thunder.mp3"
    sfx_what = ASSETS_DIR / "sfx" / "what.mp3"
    sfx_boing = ASSETS_DIR / "sfx" / "boing.mp3"
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
            "text": "Капитан Америка повидал многое, но летающий офисный стул его явно сломал. Кажется, где-то в соседней комнате Тор пытается притянуть его к себе вместо Мьёльнира! Но почему ножка и сиденье летают раздельно?",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Начинаем расследование! Вы удивитесь, но в коде игры этот стул — франкенштейн из двух отдельных физических тел: Сиденья и Колёсиков.",
            "trigger_bgm": True
        },
        {
            "id": "scheme1",
            "text": "Чтобы стул мог крутиться, движок даёт Верхнему телу и Нижнему телу свободу, но связывает их невидимой физической резинкой — джойнтом.",
            "trigger_bgm": False
        },
        {
            "id": "scheme2",
            "text": "Но стоило Кэпу задеть стул, как два тела столкнулись. Они изо всех сил отталкиваются, но резинка дёргает их обратно! Получается вечный махач, порождающий антигравитацию.",
            "trigger_bgm": False
        },
        {
            "id": "fix",
            "text": "Программистам нужно было всего лишь отключить коллизию между ними: \"Парни, вы из одной мебели, не бейте друг друга!\"",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Моя честная реакция, когда Капитан Америка сказал \"Хайль Гидра\"... А какой самый дикий баг видели вы? Пишите в комменты и подписывайтесь!",
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
        current_time = b_end + 0.15  # Small pause between blocks

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
    vis_gen = Episode4VisualsGenerator(width=1000, height=560)
    vis_gen.generate_chair_anatomy(diag1_path)
    vis_gen.generate_chair_chaos(diag2_path)
    vis_gen.generate_chair_fix_card(code_path)

    # 5. Background Video with Continuous Looping Gameplay
    print("\n[5/6] Подготовка фона с геймплеем (9:16 + непрерывный луп)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        cut_time=5.2,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg
    print(f"\n[6/6] Сборка видеоряда и аудиодорожек в FFmpeg...")

    # Timings for overlays:
    hook_start = block_timings["hook"]["start"]
    hook_mid = hook_start + (block_timings["hook"]["duration"] * 0.35)
    hook_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    sch1_start = block_timings["scheme1"]["start"]
    sch1_end = block_timings["scheme1"]["end"]

    sch2_start = block_timings["scheme2"]["start"]
    sch2_end = block_timings["scheme2"]["end"]

    fix_start = block_timings["fix"]["start"]
    fix_end = block_timings["fix"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # SFX Delays in ms
    sfx_boom_delay_ms = int(max(0, hook_start * 1000))
    sfx_thunder_delay_ms = int(max(0, hook_mid * 1000))
    sfx_what_delay_ms = int(max(0, inv_start * 1000))
    sfx_boing_delay_ms = int(max(0, sch2_start * 1000))
    sfx_mario_delay_ms = int(max(0, fix_start * 1000))
    sfx_hydra_boom_delay_ms = int(max(0, outro_start * 1000))
    bgm_delay_ms = int(max(0, bgm_start_time * 1000))

    # Inputs list for FFmpeg:
    # 0: temp_bg (video)
    # 1: voice_final (audio)
    # 2: bgm (audio)
    # 3: sfx_vine_boom (audio)
    # 4: sfx_thunder (audio)
    # 5: sfx_what (audio)
    # 6: sfx_boing (audio)
    # 7: sfx_mario (audio)
    # 8: meme_thor (image)
    # 9: diag1 (image)
    # 10: diag2 (image)
    # 11: code_card (image)
    # 12: meme_hydra (image)

    filter_chains = [
        # Meme 1: Thor Summoning Chair (Hook Mid to Hook End, lower half y=860)
        f"[8:v]scale=960:-1,format=rgba,fade=t=in:st={hook_mid:.2f}:d=0.2:alpha=1,fade=t=out:st={hook_end-0.2:.2f}:d=0.2:alpha=1[m_thor]",
        f"[0:v][m_thor]overlay=(W-w)/2:860:enable='between(t,{hook_mid:.2f},{hook_end:.2f})'[v1]",

        # Diagram 1: Anatomy of chair (Scheme 1 block, lower half y=840)
        f"[9:v]scale=980:-1,format=rgba,fade=t=in:st={sch1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={sch1_end-0.25:.2f}:d=0.25:alpha=1[v_d1]",
        f"[v1][v_d1]overlay=(W-w)/2:840:enable='between(t,{sch1_start:.2f},{sch1_end:.2f})'[v2]",

        # Diagram 2: Chaos loop (Scheme 2 block, lower half y=840)
        f"[10:v]scale=980:-1,format=rgba,fade=t=in:st={sch2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={sch2_end-0.25:.2f}:d=0.25:alpha=1[v_d2]",
        f"[v2][v_d2]overlay=(W-w)/2:840:enable='between(t,{sch2_start:.2f},{sch2_end:.2f})'[v3]",

        # Code Fix Card (Fix block, lower half y=840)
        f"[11:v]scale=980:-1,format=rgba,fade=t=in:st={fix_start:.2f}:d=0.25:alpha=1,fade=t=out:st={fix_end-0.25:.2f}:d=0.25:alpha=1[v_fix]",
        f"[v3][v_fix]overlay=(W-w)/2:840:enable='between(t,{fix_start:.2f},{fix_end:.2f})'[v4]",

        # Meme 2: Hail Hydra Reaction Meme (Outro start to Outro end, lower half y=860)
        f"[12:v]scale=960:-1,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.25:alpha=1,fade=t=out:st={outro_end-0.25:.2f}:d=0.25:alpha=1[m_hydra]",
        f"[v4][m_hydra]overlay=(W-w)/2:860:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v5]"
    ]

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v5]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing
    filter_chains.append(
        f"[1:a]volume=1.0[a_voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[3:a]adelay={sfx_boom_delay_ms}|{sfx_boom_delay_ms},volume=0.30[a_boom1];"
        f"[4:a]adelay={sfx_thunder_delay_ms}|{sfx_thunder_delay_ms},volume=0.35[a_thunder];"
        f"[5:a]adelay={sfx_what_delay_ms}|{sfx_what_delay_ms},volume=0.30[a_what];"
        f"[6:a]adelay={sfx_boing_delay_ms}|{sfx_boing_delay_ms},volume=0.35[a_boing];"
        f"[7:a]adelay={sfx_mario_delay_ms}|{sfx_mario_delay_ms},volume=0.35[a_mario];"
        f"[a_voice][a_bgm][a_boom1][a_thunder][a_what][a_boing][a_mario]amix=inputs=7:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_vine_boom),
        "-i", str(sfx_thunder),
        "-i", str(sfx_what),
        "-i", str(sfx_boing),
        "-i", str(sfx_mario),
        "-loop", "1", "-i", str(meme_thor),
        "-loop", "1", "-i", str(diag1_path),
        "-loop", "1", "-i", str(diag2_path),
        "-loop", "1", "-i", str(code_path),
        "-loop", "1", "-i", str(meme_hydra),
        "-filter_complex", full_filter,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(total_duration),
        "-pix_fmt", "yuv420p",
        str(final_video)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg render error:\n{res.stderr}")

    # Generate preview frames in output/4/frames/
    print("\n📸 Генерация превью-кадров в output/4/frames/...")
    frame_times = [
        1.5,
        hook_mid + 1.0,
        inv_start + 1.0,
        sch1_start + 1.0,
        sch2_start + 1.0,
        fix_start + 1.0,
        outro_start + 1.5
    ]
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

    print(f"\n✨ [УСПЕХ] ВЫПУСК №4 СОБРАН И СОХРАНЕН В: {final_video}")
    return final_video, block_timings, total_duration, bgm_path.name


if __name__ == "__main__":
    build_episode_4()
