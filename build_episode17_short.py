import sys
import io
import re
import json
import subprocess
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
from src.core.code_card import CodeCardGenerator
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
    Creates a continuous looped 9:16 background video from Fallout: NV gameplay segment.
    Starts from the trimmed clip with its original audio track preserved.
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
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "20",
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
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "20",
        "-c:a", "aac",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    subprocess.run(cmd_loop, capture_output=True, check=True)
    return output_bg


def build_episode_17():
    print("=" * 65)
    print("🚀 СБОРКА ВЫПУСКА №17: Fallout: New Vegas Malcolm Holmes World Freeze Bug")
    print("=" * 65)

    mgr = EpisodeOutputManager("17")
    paths = mgr.get_paths("video.mp4")

    raw_clip = mgr.temp_dir / "raw_download.mp4"
    if not raw_clip.exists():
        raw_clip = ASSETS_DIR / "downloads" / "ep17_raw.mp4"

    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # 1. Check Visual Assets
    print("\n[1/6] Проверка визуальных ассетов...")
    diagram1_png = mgr.visuals_dir / "diagram_pause_world.png"
    code_card_png = mgr.visuals_dir / "code_card_holmes.png"

    if not diagram1_png.exists() or not code_card_png.exists():
        print("  [*] Генерация 2D схем и карточки кода...")
        from src.core.episode17_visuals import generate_episode17_visuals
        generate_episode17_visuals()

    # 2. TTS Voiceover Generation
    print("\n[2/6] Синтез речи Edge-TTS по блокам (озвучка начинается с 3.0s)...")
    tts = TTSEngine(voice=DEFAULT_VOICE)

    blocks_script = {
        "hook": "Ты сражаешься с гигантским монстром, как вдруг время замирает, а перед лицом появляется он!",
        "investigation": "Это Маркольм Холмс. Как только ты подбираешь звездную крышку, его скрипт запускает безумный марафон через всю пустошь ради одной фразы!",
        "diagram_1": "Но почему монстр застыл в воздухе? В движке Gamebryo при вызове диалога включается режим Pause World. Физический шаг обнуляется, чтобы игрока не загрызли во время разговора!",
        "diagram_2": "NPC плевать на опасности! В коде забыли проверку на активный бой, поэтому диалог стартует прямо перед пастью врага!",
        "fix": "Моддеры исправили это проверкой IsInCombat. Теперь Маркольм вежливо ждет в стороне, пока ты расправишься с монстрами!",
        "outro": "Подписывайся, чтобы знать все секреты игровых движков!"
    }

    block_audio_paths = {}
    block_durations = {}
    all_events = []
    
    INITIAL_OFFSET = 3.0
    current_time_offset = INITIAL_OFFSET
    block_timings = {}

    for b_key, text in blocks_script.items():
        b_audio_path = mgr.voice_dir / f"block_{b_key}.mp3"
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
        block_durations[b_key] = dur
        current_time_offset += dur

    total_duration = current_time_offset
    print(f"  ✓ Голос сгенерирован. Первые {INITIAL_OFFSET}s - звук видео. Общая длительность: {total_duration:.2f} сек.")

    # 3. Concatenate Voice Audios
    print("\n[3/6] Объединение голосовых блоков...")
    silence_mp3 = mgr.temp_dir / "initial_silence.mp3"
    cmd_silence = [
        FFMPEG_PATH, "-y",
        "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono:d={INITIAL_OFFSET:.2f}",
        "-c:a", "libmp3lame",
        str(silence_mp3)
    ]
    subprocess.run(cmd_silence, capture_output=True, check=True)

    silence_p_str = str(silence_mp3).replace("\\", "/")
    concat_txt = mgr.temp_dir / "voice_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        f.write(f"file '{silence_p_str}'\n")
        for b_key in blocks_script.keys():
            p_str = str(block_audio_paths[b_key]).replace("\\", "/")
            f.write(f"file '{p_str}'\n")

    cmd_concat_audio = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(voice_final_path)
    ]
    subprocess.run(cmd_concat_audio, capture_output=True, check=True)

    # 4. Subtitles ASS
    print("\n[4/6] Генерация анимационных субтитров ASS...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=48,
        primary_color="&H00FFFFFF",
        outline_width=4,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_events, ass_path, max_words_per_line=3)

    # 5. Background Gameplay Loop
    print(f"\n[5/6] Создание лупа геймплея 9:16 (длительность {total_duration:.2f}s)...")
    prepare_gameplay_background(raw_clip, total_duration, temp_bg, mgr.temp_dir)

    # 6. Final Video Assembly
    print("\n[6/6] Финальный рендер через FFmpeg (NVENC GPU)...")
    ambient_path = ASSETS_DIR / "music" / "ambient" / "To Pass Time - Godmode.mp3"
    outro_path = (BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4").resolve()

    meme_wait_gif = ASSETS_DIR / "memes" / "wait.gif"
    sfx_boom_mp3 = ASSETS_DIR / "sfx" / "vine_boom.mp3"

    hk_start = block_timings["hook"]["start"]
    hk_end = block_timings["hook"]["end"]

    d1_start = block_timings["diagram_1"]["start"]
    d1_end = block_timings["diagram_1"]["end"]

    d2_start = block_timings["diagram_2"]["start"]
    d2_end = block_timings["diagram_2"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # Inputs:
    # 0: temp_bg (gameplay loop video + audio)
    # 1: voice.mp3
    # 2: ambient music
    # 3: diagram_pause_world.png
    # 4: code_card_holmes.png
    # 5: wait.gif (-ignore_loop 0)
    # 6: vine_boom.mp3
    # 7: outro_subscribe_motion.mp4

    inputs = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(ambient_path),
        "-loop", "1", "-i", str(diagram1_png),
        "-loop", "1", "-i", str(code_card_png),
        "-ignore_loop", "0", "-i", str(meme_wait_gif),
        "-i", str(sfx_boom_mp3),
        "-i", str(outro_path)
    ]

    rel_sub = "output/17/subtitles/subtitles.ass"

    filter_chains = [
        # Meme 1 (wait.gif) at Hook
        f"[5:v]scale=-1:480,format=rgba,setpts=PTS-STARTPTS+{hk_start:.2f}/TB,fade=t=in:st={hk_start:.2f}:d=0.15:alpha=1,fade=t=out:st={hk_end-0.15:.2f}:d=0.15:alpha=1[m1]",
        f"[0:v][m1]overlay=(W-w)/2:860:enable='between(t,{hk_start:.2f},{hk_end:.2f})'[v0]",

        # 2D Diagram 1: Top 2/3 (Y=80..1360)
        f"[3:v]scale=1000:-1,format=rgba,fade=t=in:st={d1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={d1_end-0.25:.2f}:d=0.25:alpha=1[v_d1]",
        f"[v0][v_d1]overlay=(W-w)/2:80:enable='between(t,{d1_start:.2f},{d1_end:.2f})'[v1]",

        # Code Card 2: Top 2/3 (Y=450)
        f"[4:v]scale=980:-1,format=rgba,fade=t=in:st={d2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={d2_end-0.25:.2f}:d=0.25:alpha=1[v_code]",
        f"[v1][v_code]overlay=(W-w)/2:450:enable='between(t,{d2_start:.2f},{d2_end:.2f})'[v2]"
    ]

    last_v = "[v2]"

    # Outro Green Screen Video Overlay
    outro_play_end = min(outro_end, outro_start + 3.14)
    filter_chains.extend([
        f"[7:v]chromakey=0x00FF00:0.28:0.15,format=rgba,setpts=PTS-STARTPTS+{outro_start:.2f}/TB[v_outro]",
        f"{last_v}[v_outro]overlay=(W-w)/2:860:enable='between(t,{outro_start:.2f},{outro_play_end:.2f})'[v_outro_mix]"
    ])
    last_v = "[v_outro_mix]"

    filter_chains.append(f"{last_v}subtitles=filename='{rel_sub}'[v_final]")

    # Audio Mix (Mutes gameplay audio after initial 3.0s when TTS starts)
    inv_start_ms = int(block_timings["investigation"]["start"] * 1000)
    hk_start_ms = int(hk_start * 1000)
    outro_audio_delay_ms = int(outro_start * 1000)

    audio_mix_inputs = [
        "[0:a]volume='if(lt(t,3.0),0.8,0.0)':eval=frame[a_gameplay]",
        "[1:a]volume=1.0[a_voice]",
        f"[2:a]volume=0.14,adelay={inv_start_ms}|{inv_start_ms}[a_bgm]",
        f"[6:a]volume=0.40,adelay={hk_start_ms}|{hk_start_ms}[a_sfx]",
        f"[7:a]volume=0.9,adelay={outro_audio_delay_ms}|{outro_audio_delay_ms}[a_outro]",
        "[a_gameplay][a_voice][a_bgm][a_sfx][a_outro]amix=inputs=5:duration=first:dropout_transition=0[a_final]"
    ]

    filter_chains.extend(audio_mix_inputs)
    filter_graph = ";".join(filter_chains)

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
        str(final_video)
    ]

    print("  [*] Запуск FFmpeg NVENC рендера...")
    res = subprocess.run(cmd_render, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ Ошибка рендера FFmpeg:")
        print(res.stderr[-2000:])
        sys.exit(1)

    # 7. Metadata Generation
    print("\n[7/7] Генерация метаданных и отчета...")
    meta_gen = MetadataGenerator()
    meta_data = {
        "episode_id": "17",
        "title": "Заморозка времени и Маркольм Холмс в Fallout: New Vegas ⏳💥 #fallout #shorts",
        "game": "Fallout: New Vegas",
        "bug_summary": "Маркольм Холмс вызывает диалог ForceDialogue прямо во время боя с гигантским муравьем. Движок Gamebryo переводит мир в Pause World (TimeScale=0.0f), замораживая монстра в воздухе.",
        "duration": total_duration,
        "timings": block_timings,
        "memes": ["wait.gif"],
        "music": "To Pass Time - Godmode.mp3"
    }
    meta_gen.generate(meta_data, mgr.root_dir)

    print("\n" + "=" * 65)
    print("✅ СБОРКА ВЫПУСКА №17 УСПЕШНО ЗАВЕРШЕНА!")
    print(f"🎬 Итоговый ролик: {final_video}")
    print("=" * 65)


if __name__ == "__main__":
    build_episode_17()
