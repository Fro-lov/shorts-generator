import sys
import io
import re
import json
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from config.settings import (
    ASSETS_DIR, FFMPEG_PATH, DEFAULT_VOICE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ
)
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
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


def prepare_gameplay_background(raw_clip: Path, total_duration: float, output_bg: Path, temp_dir: Path) -> Path:
    """
    Creates a continuous looped 9:16 background video from Mafia II gameplay segment.
    """
    base_seg = temp_dir / "base_gameplay_loop.mp4"
    filter_complex = (
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},gblur=sigma=28[bg_blurred];"
        f"[0:v]scale=1020:-1[fg_scaled];"
        f"[bg_blurred][fg_scaled]overlay=(W-w)/2:220[v_comp]"
    )
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-i", str(raw_clip),
        "-filter_complex", filter_complex,
        "-map", "[v_comp]",
        "-map", "0:a?",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-c:a", "aac",
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
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-c:a", "aac",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    subprocess.run(cmd_loop, capture_output=True, check=True)
    return output_bg


def render_variant(variant_name: str, blocks_script: dict, visuals_dir: Path, out_dir: Path, raw_clip: Path):
    print(f"\n" + "=" * 65)
    print(f"🎬 РЕНДЕРИНГ ВАРИАНТА: {variant_name}")
    print("=" * 65)

    v_dir = out_dir / variant_name.lower().replace(" ", "_")
    v_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = v_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    voice_dir = v_dir / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)

    diagram_png = visuals_dir / variant_name.lower().replace(" ", "_") / "diagram.png"
    code_card_png = visuals_dir / variant_name.lower().replace(" ", "_") / "code_card.png"

    # 1. Edge-TTS Generation
    tts = TTSEngine(voice=DEFAULT_VOICE)
    INITIAL_OFFSET = 3.0
    current_time_offset = INITIAL_OFFSET

    block_audio_paths = {}
    block_timings = {}
    all_events = []

    for b_key, text in blocks_script.items():
        b_audio_path = voice_dir / f"block_{b_key}.mp3"
        res = tts.generate_speech(text, b_audio_path)
        b_events = res.get("events", [])
        dur = get_audio_duration(b_audio_path)

        for ev in b_events:
            all_events.append({
                "text": ev.get("text", ""),
                "start": ev.get("start", 0) + current_time_offset,
                "end": min(ev.get("end", dur), dur) + current_time_offset
            })

        block_timings[b_key] = {
            "start": current_time_offset,
            "end": current_time_offset + dur,
            "duration": dur
        }
        block_audio_paths[b_key] = b_audio_path
        current_time_offset += dur

    total_duration = current_time_offset
    print(f"  ✓ Голос сгенерирован. Общая длительность: {total_duration:.2f} сек.")

    # 2. Audio Concatenation
    silence_mp3 = temp_dir / "initial_silence.mp3"
    cmd_silence = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono:d={INITIAL_OFFSET:.2f}",
        "-c:a", "libmp3lame",
        str(silence_mp3)
    ]
    subprocess.run(cmd_silence, capture_output=True, check=True)

    concat_txt = temp_dir / "voice_concat.txt"
    silence_str = str(silence_mp3).replace("\\", "/")
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write(f"file '{silence_str}'\n")
        for b_key in blocks_script.keys():
            p_str = str(block_audio_paths[b_key]).replace("\\", "/")
            f.write(f"file '{p_str}'\n")

    voice_final_path = v_dir / "voice.mp3"
    cmd_concat = [
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-c", "copy", str(voice_final_path)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)

    # 3. Subtitles
    ass_path = v_dir / "subtitles.ass"
    sub_gen = SubtitleGenerator(
        font_name="Arial", font_size=48,
        primary_color="&H00FFFFFF", outline_width=4, margin_v=420
    )
    sub_gen.generate_ass_file(all_events, ass_path, max_words_per_line=3)

    # 4. Gameplay Background Loop
    temp_bg = v_dir / "bg_loop.mp4"
    prepare_gameplay_background(raw_clip, total_duration, temp_bg, temp_dir)

    # 5. Composite Final Video
    ambient_path = ASSETS_DIR / "music" / "ambient" / "To Pass Time - Godmode.mp3"
    outro_path = BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4"
    sfx_boom_mp3 = ASSETS_DIR / "sfx" / "vine_boom.mp3"

    meme_hacker_gif = ASSETS_DIR / "memes" / "hacker.gif"
    meme_riding_jpg = ASSETS_DIR / "memes" / "riding.jpg"

    hk_start = block_timings["hook"]["start"]
    hk_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    d1_start = block_timings["diagram_1"]["start"]
    d1_end = block_timings["diagram_1"]["end"]

    d2_start = block_timings["diagram_2"]["start"]
    d2_end = block_timings["diagram_2"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    inputs = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(ambient_path),
        "-loop", "1", "-i", str(diagram_png),
        "-loop", "1", "-i", str(code_card_png),
        "-ignore_loop", "0", "-i", str(meme_hacker_gif),
        "-loop", "1", "-i", str(meme_riding_jpg),
        "-i", str(sfx_boom_mp3),
        "-i", str(outro_path)
    ]

    rel_sub = str(ass_path.relative_to(BASE_DIR)).replace("\\", "/")

    # Visual Filter Complex
    filter_chains = [
        # Meme 1 (hacker.gif) during Hook
        f"[5:v]scale=-1:460,format=rgba,setpts=PTS-STARTPTS+{hk_start:.2f}/TB,fade=t=in:st={hk_start:.2f}:d=0.15:alpha=1,fade=t=out:st={hk_end-0.15:.2f}:d=0.15:alpha=1[m1]",
        f"[0:v][m1]overlay=(W-w)/2:860:enable='between(t,{hk_start:.2f},{hk_end:.2f})'[v0]",

        # Meme 2 (riding.jpg) during Investigation
        f"[6:v]scale=-1:460,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.15:alpha=1,fade=t=out:st={inv_end-0.15:.2f}:d=0.15:alpha=1[m2]",
        f"[v0][m2]overlay=(W-w)/2:860:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v1]",

        # 2D Diagram 1: Top 2/3 (Y=80..1360)
        f"[3:v]scale=1000:-1,format=rgba,fade=t=in:st={d1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={d1_end-0.25:.2f}:d=0.25:alpha=1[v_d1]",
        f"[v1][v_d1]overlay=(W-w)/2:80:enable='between(t,{d1_start:.2f},{d1_end:.2f})'[v2]",

        # Code Card 2: Top 2/3 (Y=450)
        f"[4:v]scale=980:-1,format=rgba,fade=t=in:st={d2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={d2_end-0.25:.2f}:d=0.25:alpha=1[v_code]",
        f"[v2][v_code]overlay=(W-w)/2:450:enable='between(t,{d2_start:.2f},{d2_end:.2f})'[v3]"
    ]

    last_v = "[v3]"

    # Outro Green Screen Video Overlay
    outro_play_end = min(outro_end, outro_start + 3.14)
    filter_chains.extend([
        f"[8:v]chromakey=0x00FF00:0.28:0.15,format=rgba,setpts=PTS-STARTPTS+{outro_start:.2f}/TB[v_outro]",
        f"{last_v}[v_outro]overlay=(W-w)/2:860:enable='between(t,{outro_start:.2f},{outro_play_end:.2f})'[v_outro_mix]"
    ])
    last_v = "[v_outro_mix]"

    filter_chains.append(f"{last_v}subtitles=filename='{rel_sub}'[v_final]")

    # Audio Mix
    inv_start_ms = int(inv_start * 1000)
    hk_start_ms = int(hk_start * 1000)
    outro_audio_delay_ms = int(outro_start * 1000)

    audio_mix_inputs = [
        "[0:a]volume='if(lt(t,3.0),0.8,0.0)':eval=frame[a_gameplay]",
        "[1:a]volume=1.0[a_voice]",
        f"[2:a]volume=0.14,adelay={inv_start_ms}|{inv_start_ms}[a_bgm]",
        f"[7:a]volume=0.40,adelay={hk_start_ms}|{hk_start_ms}[a_sfx]",
        f"[8:a]volume=0.9,adelay={outro_audio_delay_ms}|{outro_audio_delay_ms}[a_outro]",
        "[a_gameplay][a_voice][a_bgm][a_sfx][a_outro]amix=inputs=5:duration=first:dropout_transition=0[a_final]"
    ]

    filter_chains.extend(audio_mix_inputs)
    filter_graph = ";".join(filter_chains)

    final_mp4 = v_dir / "video.mp4"
    cmd_render = inputs + [
        "-filter_complex", filter_graph,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-t", f"{total_duration:.2f}",
        str(final_mp4)
    ]

    print(f"  [*] Запуск FFmpeg NVENC рендера ({variant_name})...")
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Ошибка рендера {variant_name}:")
        print(res.stderr[-2000:])
        sys.exit(1)

    print(f"  ✅ Вариант скомпилирован: {final_mp4}")
    return final_mp4, total_duration, block_timings


def build_all_ep18_variants():
    print("=" * 65)
    print("🚀 СБОРКА ВСЕХ 3 ВАРИАНТОВ ВЫПУСКА №18: Mafia II Definitive Edition Air Lockpick Bug")
    print("=" * 65)

    mgr = EpisodeOutputManager("18")
    raw_clip = mgr.temp_dir / "raw_download.mp4"
    visuals_dir = mgr.visuals_dir

    # 1. Variant 1 Script
    v1_script = {
        "hook": "Ты просто хотел сесть в тачку, но превратился в хакера несуществующего автомобиля!",
        "investigation": "В Illusion Engine кнопка входа проверяет водителя лишь один раз. Но дверной замок оказался заперт, а ИИ водителя об этом даже не узнал!",
        "diagram_1": "Пока Вито ковыряет замок отмычкой, у ИИ водителя истекает таймер ожидания — и он давит на газ, уезжая в закат!",
        "diagram_2": "В коде забыли подписку ИИ водителя на статус отмычки. Он должен замораживать двигатель до завершения взлома!",
        "fix": "Моддеры связали состояние замка с поведением НПС. Теперь водитель вежливо ждет, пока вы взломаете его дверь!",
        "outro": "Подписывайся, чтобы знать все секреты игровых движков!"
    }
    mp4_v1, dur_v1, timings_v1 = render_variant("variant1", v1_script, visuals_dir, mgr.root_dir, raw_clip)

    # 2. Variant 2 Script
    v2_script = {
        "hook": "Водитель удрал в закат, а коп выписывает арест за взлом пустого места!",
        "investigation": "Дверь заперта, но координаты Вито забыли привязать к кузову машины. Автомобиль уехал, а персонаж застрял в мировых координатах!",
        "diagram_1": "ИИ полиции видит только флаг состояния взлома, но не дистанцию до машины. Коп вешает розыск за кражу невидимого транспорта!",
        "diagram_2": "Решение — сброс анимации отмычек, если расстояние до машины превышает два метра!",
        "fix": "Код прерывает взлом при отдалении авто, спасая Вито от нелепого ареста!",
        "outro": "Подписывайся, чтобы не получать штрафы за невидимый взлом!"
    }
    mp4_v2, dur_v2, timings_v2 = render_variant("variant2", v2_script, visuals_dir, mgr.root_dir, raw_clip)

    # 3. Variant 3 Script
    v3_script = {
        "hook": "Мафия 2 в своем репертуаре: ты становишься хакером воздуха прямо перед лицом полиции!",
        "investigation": "При нажатии кнопки входа Конечный Автомат переключается на взлом, но забывает уведомить сущность водителя!",
        "diagram_1": "НПС не получает событие старта отмычки и начинает движение по расписанию, оставляя Вито в вечном цикле отмычек!",
        "diagram_2": "В коде необходимо явно вызывать HoldPosition для водителя при входе в LockpickState!",
        "fix": "Исправление синхронизирует сущность водителя с замком двери!",
        "outro": "Подписывайся на Onter's inn!"
    }
    mp4_v3, dur_v3, timings_v3 = render_variant("variant3", v3_script, visuals_dir, mgr.root_dir, raw_clip)

    # Copy primary video.mp4 (Variant 1) to episode root output/18/video.mp4
    main_video = mgr.root_dir / "video.mp4"
    shutil.copy(mp4_v1, main_video)
    print(f"\n[+] Основной файл сохранен в корень: {main_video}")

    # Generate metadata.json and description.txt for episode 18
    meta_gen = MetadataGenerator()
    meta_data = {
        "episode_id": "18",
        "title": "Взлом невидимой машины и сошедший с ума ИИ в Mafia II 🚗💥 #mafia #shorts",
        "game": "Mafia II: Definitive Edition",
        "bug_summary": "При запертой двери Вито переходит в LockpickState, но ИИ водителя не опрашивает статус отмычек и уезжает, оставляя персонажа взламывать воздух на глазах у полиции.",
        "duration": dur_v1,
        "timings": timings_v1,
        "memes": ["hacker.gif", "riding.jpg"],
        "music": "To Pass Time - Godmode.mp3"
    }
    meta_gen.generate(meta_data, mgr.root_dir)

    print("\n" + "=" * 65)
    print("✅ СБОРКА ВСЕХ 3 ВАРИАНТОВ ВЫПУСКА №18 УСПЕШНО ЗАВЕРШЕНА!")
    print(f"🎬 Вариант 1: {mp4_v1}")
    print(f"🎬 Вариант 2: {mp4_v2}")
    print(f"🎬 Вариант 3: {mp4_v3}")
    print(f"🎬 Итоговый файл в корне: {main_video}")
    print("=" * 65)


if __name__ == "__main__":
    build_all_ep18_variants()
