import sys
import io
import re
import subprocess
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

# Set UTF-8 output safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from config.settings import (
    ASSETS_DIR, FFMPEG_PATH, DEFAULT_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ
)
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode13_visuals import Episode13VisualsGenerator
from src.core.output_manager import EpisodeOutputManager
from src.core.metadata_generator import MetadataGenerator


def get_audio_duration(file_path: Path) -> float:
    cmd = [FFMPEG_PATH, "-i", str(file_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        h, mn, s = m.groups()
        return int(h) * 3600 + int(mn) * 60 + float(s)
    return 3.0


def prepare_gameplay_background(gameplay_mp4: Path, total_duration: float, output_bg: Path, temp_dir: Path) -> Path:
    """
    Creates a full 9:16 background from gameplay clip cut at 5.0 seconds (before death screen):
    - Cut first 5.0 seconds
    - Crop top and bottom by 15% (crop=576:716:0:154)
    - Scale & place in gameplay window (y=200..774, width 1020, height 574)
    - Loops continuously throughout total video duration.
    """
    base_seg = temp_dir / "base_seg_5s.mp4"
    
    # 15% top & bottom crop from 576x1024:
    # 1024 * 0.15 = 153.6 (crop y=154, height=716)
    filter_complex = (
        f"[0:v]crop=576:716:0:154[cropped];"
        f"[cropped]split=2[bg][fg];"
        f"[bg]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=24:6[bg_blurred];"
        f"[fg]scale=1020:574:force_original_aspect_ratio=increase,crop=1020:574[fg_scaled];"
        f"[bg_blurred][fg_scaled]overlay=(W-w)/2:200[v_comp]"
    )
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-ss", "00:00:00",
        "-t", "5.0",
        "-i", str(gameplay_mp4),
        "-filter_complex", filter_complex,
        "-map", "[v_comp]",
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "20",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(base_seg)
    ]
    subprocess.run(cmd_base, capture_output=True, check=True)

    cmd_loop = [
        FFMPEG_PATH, "-y",
        "-stream_loop", "-1",
        "-i", str(base_seg),
        "-t", f"{total_duration:.2f}",
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "20",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    subprocess.run(cmd_loop, capture_output=True, check=True)
    return output_bg


def build_episode_13():
    print("=" * 60)
    print("🚀 НАЧАЛО СБОРКИ ВЫПУСКА №13 (CS2: Sub-Tick & Prediction Rollback)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/7] Подготовка файловой структуры в output/13/...")
    mgr = EpisodeOutputManager("13")
    paths = mgr.get_paths("video.mp4")

    gameplay_src = ASSETS_DIR / "downloads" / "13.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Memes provided by user:
    meme_surrender = ASSETS_DIR / "memes" / "surrender.jpg"
    meme_ricoshet = ASSETS_DIR / "memes" / "ricoshet.webp"

    # Visual assets in visuals/
    card1_path = mgr.visuals_dir / "card1_client_prediction.png"
    card2_path = mgr.visuals_dir / "card2_server_rollback.png"

    # Ambient Music
    ambient_music = ASSETS_DIR / "music" / "ambient" / "ambient_tech.mp3"
    if not ambient_music or not ambient_music.exists():
        amb_files = list((ASSETS_DIR / "music" / "ambient").glob("*.mp3"))
        if amb_files:
            ambient_music = amb_files[0]
        else:
            ambient_music = None

    # 2. Scene-based TTS Blocks Definition
    print("\n[2/7] Генерация озвучки по смысловым блокам (Edge-TTS)...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+8%")

    INITIAL_GAMEPLAY_BUFFER = 0.5

    scene_blocks_def = [
        {
            "id": "hook",
            "text": "Посмотрите на этого героя фразы: Меня победили, но я не сдался. Неужели тер думает что играет в танки и затанчил пробитие?",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Ты четко видишь выстрел в голову и анимацию отлета на спавн. И это в лучшей киберспортивной игре, почему же это правильно?",
            "trigger_bgm": True
        },
        {
            "id": "card1_prediction",
            "text": "Чтобы сохранить плавность, твой ПК занимается предсказанием. Нажимая ЛКМ, твой клиент сразу рисует попадание и отлет врага, отправляя на сервер точный субтик времени.",
            "trigger_bgm": False
        },
        {
            "id": "card2_rollback",
            "text": "Но главный здесь — сервер! Он отматывает мир назад, сверяет позиции и видит промах из-за пинга. Сервер отклоняет выстрел и принудительно воскрешает противника!",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Если понравилось - ставь лайк, подписывайся на Онтерс инн и оставляй коментарий какой баг разобрать следущим",
            "trigger_bgm": False
        }
    ]

    block_timings = {}
    current_time = INITIAL_GAMEPLAY_BUFFER
    all_subtitle_events = []
    block_audio_paths = []

    for idx, b in enumerate(scene_blocks_def):
        b_id = b["id"]
        b_audio = mgr.voice_dir / f"block_{idx+1}_{b_id}.mp3"
        res = tts.generate_speech(b["text"], b_audio)
        events = res["events"]
        actual_dur = get_audio_duration(b_audio)

        b_start = current_time
        b_end = current_time + actual_dur

        block_timings[b_id] = {
            "start": b_start,
            "end": b_end,
            "duration": actual_dur,
            "audio": b_audio
        }

        # Format subtitles display text for Onter's inn
        for ev in events:
            txt = ev["text"]
            if "Онтерс инн" in txt:
                txt = txt.replace("Онтерс инн", "Onter's inn")
            all_subtitle_events.append({
                "text": txt,
                "start": b_start + ev["start"],
                "end": b_start + min(ev["end"], actual_dur)
            })

        block_audio_paths.append(b_audio)
        current_time = b_end

    total_duration = current_time + 0.5
    print(f"   ✓ Сгенерировано {len(scene_blocks_def)} речевых блоков.")
    print(f"   ✓ Общая длительность видео: {total_duration:.2f} сек.")

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

    # 3. Dynamic Subtitles (.ass) in safe zone (margin_v=420 -> y=1480-1540)
    print("\n[3/7] Генерация стилизованных субтитров (MarginV=420)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",
        outline_width=5,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visuals (2D Diagrams)
    print("\n[4/7] Генерация визуальных карточек (Top 2/3 Diagram Coverage)...")
    vis_gen = Episode13VisualsGenerator(width=1000, height=1280)
    vis_gen.render_card1_client_prediction(card1_path)
    vis_gen.render_card2_server_rollback(card2_path)

    # 5. Background Video with 5s loop cut
    print("\n[5/7] Подготовка фона с геймплеем (без экрана смерти, crop 15% top/bottom)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg
    print("\n[6/7] Сборка видеоряда, мемов и аудиодорожек в FFmpeg (NVENC GPU)...")

    hk_start = block_timings["hook"]["start"]
    hk_dur = block_timings["hook"]["duration"]

    # Divide hook into 2 halves for surrender.jpg and ricoshet.webp
    m1_start = hk_start
    m1_end = hk_start + (hk_dur / 2.0)
    m2_start = m1_end
    m2_end = hk_start + hk_dur

    c1_start = block_timings["card1_prediction"]["start"]
    c1_end = block_timings["card1_prediction"]["end"]

    c2_start = block_timings["card2_rollback"]["start"]
    c2_end = block_timings["card2_rollback"]["end"]

    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    voice_delay_ms = int(INITIAL_GAMEPLAY_BUFFER * 1000)

    # Inputs:
    # 0: temp_bg (video)
    # 1: voice_final (audio)
    # 2: meme_surrender (image)
    # 3: meme_ricoshet (image)
    # 4: card1_path (image)
    # 5: card2_path (image)
    # 6: ambient_music (audio)
    # 7: gameplay_src (audio original)

    inputs = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-loop", "1", "-i", str(meme_surrender),
        "-loop", "1", "-i", str(meme_ricoshet),
        "-loop", "1", "-i", str(card1_path),
        "-loop", "1", "-i", str(card2_path)
    ]

    has_bgm = ambient_music and ambient_music.exists()
    if has_bgm:
        inputs.extend(["-i", str(ambient_music)])

    # Add gameplay audio input
    inputs.extend(["-i", str(gameplay_src)])
    gameplay_audio_idx = 6 if not has_bgm else 7

    filter_chains = [
        # Hook meme 1: surrender.jpg in visual zone y=860
        f"[2:v]scale=-1:520,format=rgba,fade=t=in:st={m1_start:.2f}:d=0.15:alpha=1,fade=t=out:st={m1_end-0.15:.2f}:d=0.15:alpha=1[m1]",
        f"[0:v][m1]overlay=(W-w)/2:860:enable='between(t,{m1_start:.2f},{m1_end:.2f})'[v0]",

        # Hook meme 2: ricoshet.webp in visual zone y=860
        f"[3:v]scale=-1:520,format=rgba,fade=t=in:st={m2_start:.2f}:d=0.15:alpha=1,fade=t=out:st={m2_end-0.15:.2f}:d=0.15:alpha=1[m2]",
        f"[v0][m2]overlay=(W-w)/2:860:enable='between(t,{m2_start:.2f},{m2_end:.2f})'[v1]",

        # Card 1 (Client Prediction): Top 2/3 at y=80
        f"[4:v]scale=1000:-1,format=rgba,fade=t=in:st={c1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={c1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v1][v_c1]overlay=(W-w)/2:80:enable='between(t,{c1_start:.2f},{c1_end:.2f})'[v2]",

        # Card 2 (Server Rollback): Top 2/3 at y=80
        f"[5:v]scale=1000:-1,format=rgba,fade=t=in:st={c2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={c2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v2][v_c2]overlay=(W-w)/2:80:enable='between(t,{c2_start:.2f},{c2_end:.2f})'[v_sub_pre]",

        # Burn-in ASS Subtitles
        f"[v_sub_pre]subtitles=filename='{rel_sub_path}'[v_final]"
    ]

    # Audio mixing (Original gameplay audio preserved, BGM during investigation, voiceover)
    if has_bgm:
        bgm_delay_ms = int(block_timings["investigation"]["start"] * 1000)
        filter_chains.extend([
            f"[1:a]adelay={voice_delay_ms}|{voice_delay_ms},volume=1.0[a_voice]",
            f"[6:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.10[a_bgm]",
            f"[{gameplay_audio_idx}:a]volume=0.18[a_orig]",
            f"[a_voice][a_bgm][a_orig]amix=inputs=3:duration=first:normalize=0[a_final]"
        ])
    else:
        filter_chains.extend([
            f"[1:a]adelay={voice_delay_ms}|{voice_delay_ms},volume=1.0[a_voice]",
            f"[{gameplay_audio_idx}:a]volume=0.20[a_orig]",
            f"[a_voice][a_orig]amix=inputs=2:duration=first:normalize=0[a_final]"
        ])

    cmd_render = inputs + [
        "-filter_complex", ";".join(filter_chains),
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", str(VIDEO_CQ),
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", str(FPS),
        "-t", f"{total_duration:.2f}",
        "-pix_fmt", "yuv420p",
        str(final_video)
    ]

    print("   ► Запуск аппаратного рендеринга FFmpeg NVENC...")
    res_render = subprocess.run(cmd_render, capture_output=True, text=True)
    if res_render.returncode != 0:
        print("❌ Ошибка рендера FFmpeg:")
        print(res_render.stderr)
        raise RuntimeError("FFmpeg NVENC render failed")

    print(f"   ✓ Видео успешно отрендерено: {final_video}")

    # 7. Metadata & Description
    print("\n[7/7] Генерация метаданных и описания...")
    scenario_data = {
        "episode_id": "13",
        "lang": "ru",
        "game": "Counter-Strike 2",
        "bug_title": "Sub-Tick Client Prediction & Server Rollback Rejection",
        "blocks": scene_blocks_def,
        "metadata": {
            "title": "Затанчил пробитие? Баг Sub-Tick & Предсказания в CS2 🎯🔄",
            "short_title": "Затанчил пробитие в CS2 #shorts #cs2 #ontersinn",
            "description": (
                "Посмотрите на этого героя фразы: Меня победили, но я не сдался. Неужели тер думает что играет в танки и затанчил пробитие?\n\n"
                "Разбор бага в CS2:\n"
                "00:00 - Затанчил пробитие?\n"
                "00:05 - Почему выстрел в голову не засчитали\n"
                "00:10 - Клиентское предсказание (Client Prediction & Sub-tick)\n"
                "00:20 - Серверный роллбэк (Server Authority & Hit Rejection)\n"
                "00:30 - Ставь лайк и подписывайся на Onter's inn!\n\n"
                "#cs2 #counterstrike2 #csgo #ontersinn #геймдев #баги #физика #шортс #shorts"
            ),
            "tags": ["cs2", "counter strike 2", "csgo", "subtick", "onters inn", "баги", "игры", "геймдев", "шортс", "shorts"]
        }
    }
    MetadataGenerator.generate(
        scenario_data=scenario_data,
        output_dir=mgr.root_dir,
        duration=total_duration
    )
    print("   ✓ metadata.json и description.txt сформированы.")

    print("\n" + "=" * 60)
    print(f"🎉 ВЫПУСК №13 УСПЕШНО СОБРАН!")
    print(f"📁 Директория: {mgr.root_dir}")
    print(f"🎬 Финальный файл: {final_video}")
    print(f"⏱ Хронометраж: {total_duration:.2f} сек.")
    print("=" * 60)


if __name__ == "__main__":
    build_episode_13()
