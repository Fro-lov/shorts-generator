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
from src.core.episode10_visuals import Episode10VisualsGenerator
from src.core.output_manager import EpisodeOutputManager
from src.core.music_generator import get_random_bgm
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
    Creates a full 9:16 background from the clean gameplay clip:
    - Formats 576x576 gameplay to 9:16 (blurred background + foreground centered at y=200..774)
    - Loops continuously throughout the total video duration.
    """
    base_seg = temp_dir / "base_seg.mp4"
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-t", "5.0",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=24:6[bg];"
        f"[0:v]scale=1020:1020[fg];"
        f"[bg][fg]overlay=(W-w)/2:200[v_comp]",
        "-map", "[v_comp]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
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
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        str(output_bg)
    ]
    subprocess.run(cmd_loop, capture_output=True, check=True)
    return output_bg


def build_episode_10():
    print("=" * 60)
    print("🚀 НАЧАЛО СБОРКИ ВЫПУСКА №10 (Ubisoft: Прямоходящий зверь в тумане)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/7] Подготовка файловой структуры в output/10/...")
    mgr = EpisodeOutputManager("10")
    paths = mgr.get_paths("video.mp4")

    # Gameplay clip
    gameplay_src = ASSETS_DIR / "memes" / "video" / "bear_tpose.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    card1_3d_video = mgr.visuals_dir / "card1_skeleton_3d.mp4"
    card2_path = mgr.visuals_dir / "card2_tree_vertical.png"
    card3_path = mgr.visuals_dir / "card3_fix_vertical.png"

    # Contextual Memes
    meme_holy_dog = ASSETS_DIR / "memes" / "святой_крест_clean.png"
    meme_cat_laugh = ASSETS_DIR / "memes" / "кот-смеётся.png"

    # SFX
    sfx_win_error = ASSETS_DIR / "sfx" / "windows_error.mp3"
    if not sfx_win_error.exists():
        sfx_win_error = ASSETS_DIR / "sfx" / "what.mp3"

    # Ambient Music
    ambient_dir = ASSETS_DIR / "music" / "ambient"
    bgm_path = get_random_bgm(ambient_dir)
    print(f"   ✓ Фоновый эмбиент из фонотеки YouTube: {bgm_path.name}")

    # 2. Scene-based TTS Blocks Definition
    print("\n[2/7] Генерация озвучки по смысловым блокам (Edge-TTS)...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+14%")

    # Initial pure gameplay buffer duration (original game sound only)
    INITIAL_GAMEPLAY_BUFFER = 5.0

    scene_blocks_def = [
        {
            "id": "batya",
            "text": "Ты крадешься в густом тумане, готовый к схватке... а встречаешь батю, который в три часа ночи пришел к холодильнику!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Хорошо, что у него нет ружья, хотя и так вероятность получить по морде выросла. Почему же эволюция произошла с этим животным моментально?",
            "trigger_bgm": True
        },
        {
            "id": "card1_3d",
            "text": "Всё дело в сбое анимационного графа. При подгрузке сущностей в тумане движок перепутал скелетные профили и натянул меш животного на базовый риг человека-стражника!",
            "trigger_bgm": False
        },
        {
            "id": "card2_tree",
            "text": "Движок честно выполнил приказ стейт-машины: взял позу покоя гуманоида и выпрямил хребет на девяносто градусов. Лапы по швам, морда кирпичом — патрулирование леса началось.",
            "trigger_bgm": False
        },
        {
            "id": "card3_fix",
            "text": "Баг лечится строгой проверкой иерархии костей перед вызовом стейта. Но теперь в этот лес хотя бы действительно страшно заходить!",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Ставь лайк и подписывайся на GameBug, здесь мы препарируем геймдев!",
            "trigger_bgm": False
        }
    ]

    block_timings = {}
    current_time = INITIAL_GAMEPLAY_BUFFER
    all_subtitle_events = []
    block_audio_paths = []
    bgm_start_time = 0.0

    for idx, b in enumerate(scene_blocks_def):
        b_id = b["id"]
        b_audio = mgr.voice_dir / f"block_{idx+1}_{b_id}.mp3"
        res = tts.generate_speech(b["text"], b_audio)
        events = res["events"]
        actual_dur = get_audio_duration(b_audio)

        b_start = current_time
        b_end = current_time + actual_dur

        if b["trigger_bgm"] and bgm_start_time == 0.0:
            bgm_start_time = b_start

        block_timings[b_id] = {
            "start": b_start,
            "end": b_end,
            "duration": actual_dur,
            "audio": b_audio
        }

        # Subtitle events aligned exactly with block audio (+5s offset)
        for ev in events:
            all_subtitle_events.append({
                "text": ev["text"],
                "start": b_start + ev["start"],
                "end": b_start + min(ev["end"], actual_dur)
            })

        block_audio_paths.append(b_audio)
        current_time = b_end

    total_duration = current_time + 0.3
    print(f"   ✓ Первые {INITIAL_GAMEPLAY_BUFFER:.1f} сек: оригинальный звук игры (без озвучки).")
    print(f"   ✓ Сгенерировано {len(scene_blocks_def)} речевых блоков.")
    print(f"   ✓ Общая длительность видео: {total_duration:.2f} сек.")
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

    # 4. Generate Visuals: 3D Skeleton Video + 2D Graphic Cards
    print("\n[4/7] Генерация 3D видеоролика и графических схем...")
    vis_gen = Episode10VisualsGenerator(width=1000, height=1280)
    
    # Render 3D Skeleton Simulation matching exact duration of card1_3d block
    card1_dur = block_timings["card1_3d"]["duration"]
    if not card1_3d_video.exists():
        print(f"   ► Рендеринг 3D сцены скелета ({card1_dur:.2f} сек)...")
        vis_gen.render_3d_skeleton_video(
            output_mp4=card1_3d_video,
            duration=card1_dur
        )
    else:
        print(f"   ✓ 3D сцена уже отрендерена: {card1_3d_video.name}")

    print("   ► Проверка 2D карточек архитектуры и фикса...")
    if not card2_path.exists():
        vis_gen.render_card2_tree(card2_path)
    if not card3_path.exists():
        vis_gen.render_card3_fix(card3_path)


    # 5. Background Video with Continuous Looping Pure Gameplay
    print("\n[5/7] Подготовка чистого фона с геймплеем (9:16 + непрерывный луп)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg (Zero-Overlap Grid + Top 2/3 Diagrams)
    print(f"\n[6/7] Сборка видеоряда и аудиодорожек в FFmpeg (NVENC GPU)...")

    batya_start = block_timings["batya"]["start"]
    batya_end = block_timings["batya"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    card1_start = block_timings["card1_3d"]["start"]
    card1_end = block_timings["card1_3d"]["end"]

    card2_start = block_timings["card2_tree"]["start"]
    card2_end = block_timings["card2_tree"]["end"]

    fix_start = block_timings["card3_fix"]["start"]
    fix_end = block_timings["card3_fix"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # Timings for audio delays in ms
    voice_delay_ms = int(INITIAL_GAMEPLAY_BUFFER * 1000)
    bgm_delay_ms = int(bgm_start_time * 1000)
    # Trigger Windows error sound right at skeleton glitch point in 3D (~35% into card1)
    sfx_win_delay_ms = int((card1_start + card1_dur * 0.35) * 1000)

    # FFmpeg Inputs:
    # 0: temp_bg (video, 1080x1920)
    # 1: gameplay_src (original video with sound)
    # 2: voice_final (audio)
    # 3: bgm (audio)
    # 4: sfx_win_error (audio)
    # 5: meme_holy_dog (image, dog with cross and bible)
    # 6: card1_3d_video (mp4, 3D WebGL skeleton animation 1000x1280)
    # 7: card2_path (image, blend tree diagram 1000x1280)
    # 8: card3_path (image, code fix diff 1000x1280)
    # 9: meme_cat_laugh (image, outro meme)

    filter_chains = [
        # Batya Block: holy dog meme in zone y=880 (from 5s to end of batya block)
        f"[5:v]scale=-1:500,format=rgba,fade=t=in:st={batya_start:.2f}:d=0.2:alpha=1,fade=t=out:st={batya_end-0.2:.2f}:d=0.2:alpha=1[m_dog]",
        f"[0:v][m_dog]overlay=(W-w)/2:880:enable='between(t,{batya_start:.2f},{batya_end:.2f})'[v1]",

        # Card 1 (3D Skeleton MP4): Top 2/3 at y=80
        # Sync 3D video playback with its start time via setpts
        f"[6:v]setpts=PTS-STARTPTS+{card1_start:.2f}/TB,scale=1000:-1,format=rgba,fade=t=in:st={card1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v1][v_c1]overlay=(W-w)/2:80:enable='between(t,{card1_start:.2f},{card1_end:.2f})'[v2]",

        # Card 2 (Blend Tree 2D PNG): Top 2/3 at y=80
        f"[7:v]scale=1000:-1,format=rgba,fade=t=in:st={card2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v2][v_c2]overlay=(W-w)/2:80:enable='between(t,{card2_start:.2f},{card2_end:.2f})'[v3]",

        # Card 3 (Code Fix 2D PNG): Top 2/3 at y=80
        f"[8:v]scale=1000:-1,format=rgba,fade=t=in:st={fix_start:.2f}:d=0.25:alpha=1,fade=t=out:st={fix_end-0.25:.2f}:d=0.25:alpha=1[v_c3]",
        f"[v3][v_c3]overlay=(W-w)/2:80:enable='between(t,{fix_start:.2f},{fix_end:.2f})'[v4]",

        # Outro Meme: laughing cat meme in zone y=880
        f"[9:v]scale=-1:500,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.25:alpha=1,fade=t=out:st={outro_end-0.25:.2f}:d=0.25:alpha=1[m_outro]",
        f"[v4][m_outro]overlay=(W-w)/2:880:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v5]"
    ]

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v5]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing:
    # 1) Original gameplay sound: active only during first 5.0s, fade out at 4.7s
    # 2) Voice: delayed by 5.0s, volume 1.0
    # 3) BGM: delayed by bgm_delay_ms, volume 0.14
    # 4) SFX win error: delayed by sfx_win_delay_ms, volume 0.32
    filter_chains.append(
        f"[1:a]atrim=0:5.0,afade=t=out:st=4.7:d=0.3,volume=1.0[a_orig];"
        f"[2:a]adelay={voice_delay_ms}|{voice_delay_ms},volume=1.0[a_voice];"
        f"[3:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[4:a]adelay={sfx_win_delay_ms}|{sfx_win_delay_ms},volume=0.32[a_sfx];"
        f"[a_orig][a_voice][a_bgm][a_sfx]amix=inputs=4:duration=longest:normalize=0[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(gameplay_src),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_win_error),
        "-loop", "1", "-i", str(meme_holy_dog),
        "-i", str(card1_3d_video),
        "-loop", "1", "-i", str(card2_path),
        "-loop", "1", "-i", str(card3_path),
        "-loop", "1", "-i", str(meme_cat_laugh),
        "-filter_complex", full_filter,
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

    print("   Запуск аппаратного рендеринга (NVENC)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError("Ошибка рендера видео!")

    print(f"\n🎉 Ролик успешно готов: {final_video}")

    # 7. Metadata Generation
    print("\n[7/7] Генерация описания и метаданных...")
    scenario_info = {
        "episode_id": "10",
        "lang": "ru",
        "game": "Ubisoft (Assassin's Creed)",
        "bug_title": "Сбой ретаргетинга скелета: Зверь-гуманоид (Skeleton Retargeting Mismatch)",
        "blocks": scene_blocks_def
    }
    MetadataGenerator.generate(
        scenario_data=scenario_info,
        output_dir=mgr.root_dir,
        duration=total_duration
    )

    # Frame extraction for preview
    preview_frame = mgr.frames_dir / "preview_thumbnail.png"
    subprocess.run([
        FFMPEG_PATH, "-y",
        "-ss", f"{card1_start + card1_dur * 0.5:.2f}",
        "-i", str(final_video),
        "-vframes", "1",
        str(preview_frame)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("\n" + "=" * 60)
    print("✅ ВСЕ ЭТАПЫ ВЫПОЛНЕНЫ УСПЕШНО!")
    print(f"📁 Итоговый файл: {final_video.resolve()}")
    print("=" * 60)
    return final_video


if __name__ == "__main__":
    build_episode_10()
