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
from src.core.episode11_visuals import Episode11VisualsGenerator
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
    - Formats 16:9 gameplay to 9:16 (blurred background + foreground centered at y=200..774)
    - Loops continuously throughout the total video duration.
    """
    base_seg = temp_dir / "base_seg.mp4"
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=24:6[bg];"
        f"[0:v]scale=1020:574[fg];"
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


def build_episode_11():
    print("=" * 60)
    print("🚀 НАЧАЛО СБОРКИ ВЫПУСКА №11 (Ghost of Tsushima: Монгол-Бумеранг)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/7] Подготовка файловой структуры в output/11/...")
    mgr = EpisodeOutputManager("11")
    paths = mgr.get_paths("video.mp4")

    # Gameplay clip
    gameplay_src = ASSETS_DIR / "gameplay" / "tsushima_cliff_clean.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    card1_path = mgr.visuals_dir / "card1_state_conflict.png"
    card2_path = mgr.visuals_dir / "card2_fix.png"

    # Contextual Memes
    meme_ressurection = ASSETS_DIR / "memes" / "ressurection.jpg"
    meme_mo = ASSETS_DIR / "memes" / "mo.jpg"
    meme_cat_laugh = ASSETS_DIR / "memes" / "кот-смеётся.png"

    # SFX
    sfx_boing = ASSETS_DIR / "sfx" / "boing.mp3"
    sfx_boom = ASSETS_DIR / "sfx" / "vine_boom.mp3"

    # Ambient Music
    ambient_dir = ASSETS_DIR / "music" / "ambient"
    bgm_path = get_random_bgm(ambient_dir)
    print(f"   ✓ Фоновый эмбиент из фонотеки YouTube: {bgm_path.name}")

    # 2. Scene-based TTS Blocks Definition
    print("\n[2/7] Генерация озвучки по смысловым блокам (Edge-TTS)...")
    tts = TTSEngine(voice=DEFAULT_VOICE, rate="+14%")

    # Initial pure gameplay buffer duration (original game sound only: kick and scream)
    INITIAL_GAMEPLAY_BUFFER = 3.5

    scene_blocks_def = [
        {
            "id": "hook",
            "text": "Ты сбросил монгола с обрыва прямо в бездну океана... Но этот воин принципиальный: раз анимацию смерти на земле не доиграл — изволь катапультироваться обратно!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Почему этот сын сюжета воскрес из преисподней, только чтобы отыграть предсмертную анимацию?",
            "trigger_bgm": True
        },
        {
            "id": "card1_state",
            "text": "Баг случился из двух совпадений! Первое: механизм защиты границ игрового мира вернул энписи обратно на последнюю подходящую поверхность. Второе: однако хэпэ уже было равно нулю, и всё, что оставалось этому бедолаге — проиграть анимацию смерти!",
            "trigger_bgm": False
        },
        {
            "id": "card2_fix",
            "text": "Чтобы трупы не работали бумерангами, движку нужно лишь проверять хэпэ. Если оно на нуле — система спасения отключается, а тело спокойно уходит на дно.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Самурайский кодекс суров, но баги движка ещё суровее. Ставь лайк и подписывайся на GameBug!",
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

        # Subtitle events aligned exactly with block audio
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

    # 4. Generate Visuals: 2D Graphic Cards
    print("\n[4/7] Генерация графических схем...")
    vis_gen = Episode11VisualsGenerator(width=1000, height=1280)
    print("   ► Проверка 2D карточек архитектуры и фикса...")
    vis_gen.render_card1_navmesh_state(card1_path)
    vis_gen.render_card2_fix(card2_path)

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

    hook_start = block_timings["hook"]["start"]
    hook_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    card1_start = block_timings["card1_state"]["start"]
    card1_end = block_timings["card1_state"]["end"]

    card2_start = block_timings["card2_fix"]["start"]
    card2_end = block_timings["card2_fix"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")

    # Timings for audio delays in ms
    voice_delay_ms = int(INITIAL_GAMEPLAY_BUFFER * 1000)
    bgm_delay_ms = int(bgm_start_time * 1000)
    # SFX Boing right when Mongol launches back into the air (~10.2s)
    sfx_boing_delay_ms = 10200
    # SFX Boom right when Mongol hits the ground (~11.8s)
    sfx_boom_delay_ms = 11800

    # FFmpeg Inputs:
    # 0: temp_bg (video, 1080x1920)
    # 1: gameplay_src (original video with sound)
    # 2: voice_final (audio)
    # 3: bgm (audio)
    # 4: sfx_boing (audio)
    # 5: sfx_boom (audio)
    # 6: meme_ressurection (image, Undertaker resurrection)
    # 7: meme_mo (image, Moe throwing Barney out)
    # 8: card1_path (image, 4-step diagram 1000x1280)
    # 9: card2_path (image, code fix diff 1000x1280)
    # 10: meme_cat_laugh (image, outro meme)

    # Undertaker resurrection meme pops up when Mongol lands (from 11.5s to hook_end)
    ressurect_start = 11.5
    ressurect_end = max(hook_end, 13.5)

    filter_chains = [
        # Hook meme: Undertaker resurrection in zone y=880 (when Mongol lands)
        f"[6:v]scale=920:-1,format=rgba,fade=t=in:st={ressurect_start:.2f}:d=0.2:alpha=1,fade=t=out:st={ressurect_end-0.2:.2f}:d=0.2:alpha=1[m_res]",
        f"[0:v][m_res]overlay=(W-w)/2:880:enable='between(t,{ressurect_start:.2f},{ressurect_end:.2f})'[v0]",

        # Investigation meme: Moe & Barney meme in zone y=870
        f"[7:v]scale=-1:520,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.2:alpha=1,fade=t=out:st={inv_end-0.2:.2f}:d=0.2:alpha=1[m_mo]",
        f"[v0][m_mo]overlay=(W-w)/2:870:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v1]",

        # Card 1 (4-step diagram): Top 2/3 at y=80
        f"[8:v]scale=1000:-1,format=rgba,fade=t=in:st={card1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v1][v_c1]overlay=(W-w)/2:80:enable='between(t,{card1_start:.2f},{card1_end:.2f})'[v2]",

        # Card 2 (Fix diff card): Top 2/3 at y=80
        f"[9:v]scale=1000:-1,format=rgba,fade=t=in:st={card2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v2][v_c2]overlay=(W-w)/2:80:enable='between(t,{card2_start:.2f},{card2_end:.2f})'[v3]",

        # Outro meme: Cat laugh in zone y=880
        f"[10:v]scale=-1:480,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.2:alpha=1,fade=t=out:st={outro_end-0.2:.2f}:d=0.2:alpha=1[m_cat]",
        f"[v3][m_cat]overlay=(W-w)/2:880:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v_ass_pre]",

        # Burn-in styled Subtitles (.ass)
        f"[v_ass_pre]subtitles=filename='{rel_sub_path}'[v_final]",

        # Audio mixing:
        # Original gameplay sound: full volume in buffer (0..3.5s), dipped to 0.12 during voiceover
        f"[1:a]volume=enable='between(t,0,{INITIAL_GAMEPLAY_BUFFER})':volume=1.0,volume=enable='gte(t,{INITIAL_GAMEPLAY_BUFFER})':volume=0.12[a_game]",
        f"[2:a]adelay={voice_delay_ms}|{voice_delay_ms},volume=1.0[a_voice]",
        f"[3:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm]",
        f"[4:a]adelay={sfx_boing_delay_ms}|{sfx_boing_delay_ms},volume=0.40[a_boing]",
        f"[5:a]adelay={sfx_boom_delay_ms}|{sfx_boom_delay_ms},volume=0.35[a_boom]",
        f"[a_game][a_voice][a_bgm][a_boing][a_boom]amix=inputs=5:duration=longest:normalize=0[a_final]"
    ]

    cmd_render = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(gameplay_src),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_boing),
        "-i", str(sfx_boom),
        "-loop", "1", "-i", str(meme_ressurection),
        "-loop", "1", "-i", str(meme_mo),
        "-loop", "1", "-i", str(card1_path),
        "-loop", "1", "-i", str(card2_path),
        "-loop", "1", "-i", str(meme_cat_laugh),
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

    # 7. Generate Metadata & Post-production report
    print("\n[7/7] Генерация описания и метаданных...")
    scenario_data = {
        "episode_id": "11",
        "lang": "ru",
        "game": "Ghost of Tsushima",
        "bug_title": "Монгол-бумеранг возвращается из бездны",
        "blocks": scene_blocks_def,
        "metadata": {
            "title": "Монгол-бумеранг забыл умереть в Ghost of Tsushima 💀",
            "short_title": "Монгол вернулся с того света ради анимации #shorts #игры",
            "description": (
                "Ты сбросил монгола с двухсотметрового обрыва в океан... Но этот воин принципиальный: "
                "раз анимацию смерти на земле не доиграл — изволь катапультироваться обратно!\n\n"
                "Разбираем курьёзный баг движка Ghost of Tsushima: почему State Machine и NavMesh Unstuck "
                "запустили тело обратно на вершину скалы точно к ногам Дзина Сакая.\n\n"
                "#shorts #ghostofjapan #ghostoftsushima #баги #игры #геймдев #игровыеприколы"
            ),
            "tags": [
                "ghostoftsushima", "ghost of tsushima", "дзин сакай", "цусима",
                "баги", "баги в играх", "геймдев", "игровые приколы", "физика в играх",
                "shorts", "игры", "gaming", "юмор"
            ]
        }
    }

    meta_res = MetadataGenerator.generate(
        scenario_data=scenario_data,
        output_dir=mgr.root_dir,
        duration=total_duration
    )
    print("   ✓ metadata.json и description.txt сформированы.")

    # Final summary output
    print("\n" + "=" * 60)
    print("🎉 ВЫПУСК №11 УСПЕШНО СОБРАН!")
    print(f"🎮 Игра и баг: Ghost of Tsushima — Монгол-Бумеранг (NavMesh Unstuck)")
    print(f"📁 Папка выпуска: {mgr.root_dir}")
    print(f"⏱ Хронометраж: {total_duration:.2f} сек")
    print(f"🎭 Мемы: Испуганный хомяк (момент приземления), Смеющийся кот (аутро)")
    print(f"🔊 Аудио: Эмбиент YouTube Audio Library, SFX Boing + Vine Boom, DmitryNeural TTS")
    print(f"🔗 Итоговый файл: {final_video}")
    print("=" * 60)


if __name__ == "__main__":
    build_episode_11()
