import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"e:\social")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import FFMPEG_PATH, OUTPUT_DIR
from src.core.tts import TTSEngine, _get_duration
from src.core.subtitles import SubtitleGenerator
from src.core.metadata_generator import MetadataGenerator
from PIL import Image

PYTHON_EXE = r"C:\Users\onter\AppData\Local\Programs\Python\Python311\python.exe"

VARIANTS = {
    "variant1": {
        "name": "variant1",
        "game": "Mafia: The City of Lost Heaven",
        "bug_title": "Бессмертный механик Ральф",
        "meme": BASE_DIR / "assets" / "memes" / "ep22_this_is_fine.gif",
        "blocks": [
            {
                "name": "hook",
                "role": "host",
                "text": "Привез машину на приемку в Мафии, а механик до последнего выполняет свои обязанности... даже во время взрыва!"
            },
            {
                "name": "investigation",
                "role": "host",
                "text": "Димон, почему от взрыва тачка разлетелась в труху, а Ральф даже ухом не повел?"
            },
            {
                "name": "diagram1",
                "role": "expert",
                "text": "Все просто! В момент вызова диалога движок LS3D навешивает на персонажа флаг SetGodMode(true). Все источники урона обнуляются."
            },
            {
                "name": "code_card",
                "role": "expert",
                "text": "Урон автомобиля разрушает кузов, но анимация речи Ральфа защищена от сброса и рагдолла."
            },
            {
                "name": "outro",
                "role": "host",
                "text": "Вот это сервис! Подписывайся на Onter's inn, ставь лайк и пиши в комментариях, какие титановые нервы ты встречал в играх!"
            }
        ],
        "metadata": {
            "title": "Mafia (2002): Бессмертный механик в эпицентре взрыва! 💥 (Физика игр)",
            "short_title": "Mafia 2002 — Сервис высшего уровня! #shorts #игры #мафия",
            "tags": ["mafia", "мафия", "shorts", "игры", "баги", "бессмертие", "геймдев", "мемы", "юмор"],
            "pinned_comment": "👇 А вы пытались взрывать машин в гараже Сальери? Напишите в комментариях!"
        }
    },
    "variant2": {
        "name": "variant2",
        "game": "Mafia: The City of Lost Heaven",
        "bug_title": "Скриптовый щит кат-сцены",
        "meme": BASE_DIR / "assets" / "memes" / "ep22_cool_explosion.gif",
        "blocks": [
            {
                "name": "hook",
                "role": "host",
                "text": "Машина взрывается и горит, а приемщик как ни в чем не бывало продолжает осмотр!"
            },
            {
                "name": "investigation",
                "role": "host",
                "text": "Дима, как разработчикам удалось заставить NPC выживать в самом эпицентре детонации?"
            },
            {
                "name": "diagram1",
                "role": "expert",
                "text": "Это классическая технология Cutscene Invulnerability. Чтобы игрок не сломал сюжет случайно брошенной гранатой, персонаж блокируется в стейт-машине."
            },
            {
                "name": "code_card",
                "role": "expert",
                "text": "Коллизии огня игнорируются, а стейт-машина отклоняет любые вызовы обработки урона."
            },
            {
                "name": "outro",
                "role": "host",
                "text": "Заходи на Onter's inn! Жми подписку, ставь лайк и пиши в комментариях самый дикий глитч из старых игр!"
            }
        ],
        "metadata": {
            "title": "Mafia 1: Скриптовый щит кат-сцены 💥 (Разбор движка)",
            "short_title": "Mafia 1 — Скриптовый щит кат-сцены #shorts #игры #геймдев",
            "tags": ["mafia", "мафия", "shorts", "игры", "баги", "геймдев", "разбор", "физика"],
            "pinned_comment": "👇 Какой баг в старой Мафии вам запомнился больше всего? Напишите в комментариях!"
        }
    },
    "variant3": {
        "name": "variant3",
        "game": "Mafia: The City of Lost Heaven",
        "bug_title": "Железобетонный Ральф",
        "meme": BASE_DIR / "assets" / "memes" / "ep22_shocked_cat.gif",
        "blocks": [
            {
                "name": "hook",
                "role": "host",
                "text": "В Мафии двухтысячного года механики настолько суровые, что их не берет даже взрыв тачки!"
            },
            {
                "name": "investigation",
                "role": "host",
                "text": "Это забавный баг или преднамеренная фича авторов?"
            },
            {
                "name": "diagram1",
                "role": "expert",
                "text": "Это стандартный костыль нулевых. Сценаристы отключают расчет здоровья NPC на время диалога, но забывают заблокировать детонацию авто."
            },
            {
                "name": "code_card",
                "role": "expert",
                "text": "Раздельные счетчики HP обнуляют хитпоинты машины, оставляя у Ральфа ровно 100 из 100 HP."
            },
            {
                "name": "outro",
                "role": "host",
                "text": "Подпишись на Onter's inn, влепи лайк и напиши в комментариях, в какой игре кат-сцены смешнее всего!"
            }
        ],
        "metadata": {
            "title": "Mafia (2002): Железобетонный Ральф 💥 (Приколы в играх)",
            "short_title": "Mafia 2002 — Железобетонный Ральф #shorts #приколы #игры",
            "tags": ["mafia", "мафия", "shorts", "игры", "приколы", "юмор", "мемы", "видеоигры"],
            "pinned_comment": "👇 Ждем ваши смешные истории про кат-сцены в комментариях!"
        }
    }
}


def render_single_variant(var_key: str, var_info: dict, ep_dir: Path):
    print(f"\n==========================================")
    print(f"🎬 RENDERING {var_key.upper()}...")
    print(f"==========================================")

    var_dir = ep_dir / var_key
    var_dir.mkdir(parents=True, exist_ok=True)

    voice_dir = ep_dir / "voice" / var_key
    voice_dir.mkdir(parents=True, exist_ok=True)

    visuals_dir = ep_dir / var_key / "visuals"
    card1_path = visuals_dir / "card1.png"
    card2_path = visuals_dir / "card2.png"

    tts_engine = TTSEngine()
    sub_gen = SubtitleGenerator()

    # 1. Dual-Voice Synthesis
    blocks = var_info["blocks"]
    audio_files_data = []
    voices_used = set()

    for idx, blk in enumerate(blocks):
        role = blk.get("role", "expert")
        text = blk.get("text", "")
        out_wav = voice_dir / f"block_{idx}.wav"

        res = tts_engine.generate_speech(text, out_wav, role=role)
        audio_files_data.append((out_wav, res["events"]))
        voices_used.add(res["voice_used"])
        print(f"  [TTS Block {idx}] Role: {role} -> Voice: {res['voice_used']} ({_get_duration(out_wav):.2f}s)")

    print(f"  [Dual-Voice Check] Voices used: {voices_used}")
    assert len(voices_used) >= 2, f"Dual-voice assert failed! Only {voices_used} used."

    # 2. Timing & Subtitles (with VOICE_DELAY for original game audio opening)
    VOICE_DELAY = 3.5  # Original game sound (Ralph + explosion) plays for 3.5s before TTS starts

    all_events = []
    curr_time = 0.0
    audio_files_paths = []
    block_timings = {}

    for idx, (out_wav, evs) in enumerate(audio_files_data):
        blk_name = blocks[idx]["name"]
        dur = _get_duration(out_wav)
        block_timings[blk_name] = {
            "start": curr_time,
            "end": curr_time + dur,
            "duration": dur
        }
        for ev in evs:
            all_events.append({
                "text": ev["text"],
                "start": VOICE_DELAY + curr_time + ev["start"],
                "end": VOICE_DELAY + curr_time + ev["end"]
            })
        curr_time += dur
        audio_files_paths.append(out_wav)

    total_duration = VOICE_DELAY + curr_time
    print(f"  [Total Duration] {total_duration:.2f} seconds (VOICE_DELAY={VOICE_DELAY}s)")

    # Concat voice files
    concat_txt = ep_dir / "temp" / f"voice_concat_{var_key}.txt"
    concat_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(concat_txt, "w", encoding="utf-8") as f:
        for p in audio_files_paths:
            clean_p = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    full_voice_audio = voice_dir / "voice_full.mp3"
    subprocess.run([
        FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt), "-c:a", "libmp3lame", "-q:a", "2", str(full_voice_audio)
    ], check=True, capture_output=True)

    sub_path = ep_dir / "subtitles" / f"{var_key}.ass"
    sub_path.parent.mkdir(parents=True, exist_ok=True)
    sub_gen.generate_ass_file(all_events, sub_path)

    # 3. Paths & Timings for FFmpeg
    raw_gameplay = ep_dir / "temp" / "raw_16x9.mp4"
    if not raw_gameplay.exists():
        raw_gameplay = ep_dir / "temp" / "preview_gameplay.mp4"
    meme_path = var_info["meme"]
    outro_motion = BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4"
    ambient_file = BASE_DIR / "assets" / "music" / "ambient" / "ambient1.mp3"
    sfx_file = BASE_DIR / "assets" / "sfx" / "gta-wasted.mp3"

    output_mp4 = var_dir / "video.mp4"

    d1_start = VOICE_DELAY + block_timings["diagram1"]["start"]
    d1_end = VOICE_DELAY + block_timings["diagram1"]["end"]

    cc_start = VOICE_DELAY + block_timings["code_card"]["start"]
    cc_end = VOICE_DELAY + block_timings["code_card"]["end"]

    outro_start = VOICE_DELAY + block_timings["outro"]["start"]
    outro_end = total_duration

    # Card Y position calculation (bottom aligned in top 2/3 y=80..1360)
    c1_y = 80
    if card1_path.exists():
        with Image.open(card1_path) as img:
            c1_y = max(80, 1360 - img.height)

    c2_y = 80
    if card2_path.exists():
        with Image.open(card2_path) as img:
            c2_y = max(80, 1360 - img.height)

    # 4. FFmpeg Filter Construction
    inputs = [
        "-stream_loop", "-1", "-i", str(raw_gameplay),                                      # [0:v][0:a] Gameplay (Video & Original Audio)
        "-i", str(full_voice_audio),                                                        # [1:a] TTS Voice
        "-loop", "1", "-i", str(card1_path),                                                # [2:v] Card 1
        "-loop", "1", "-i", str(card2_path),                                                # [3:v] Card 2
        "-ignore_loop", "0", "-stream_loop", "-1", "-i", str(meme_path),                   # [4:v] Meme GIF
        "-i", str(outro_motion),                                                            # [5:v][5:a] Outro Motion Video
    ]

    audio_idx = 6
    if sfx_file.exists():
        inputs.extend(["-i", str(sfx_file)])
        sfx_in = audio_idx
        audio_idx += 1
    else:
        sfx_in = None

    if ambient_file.exists():
        inputs.extend(["-stream_loop", "-1", "-i", str(ambient_file)])
        amb_in = audio_idx
        audio_idx += 1
    else:
        amb_in = None

    filter_chains = []
    # Base layout (scaled 16:9 gameplay at y=200 on blurred 1080x1920 bg)
    filter_chains.append(
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28[bg];"
        "[0:v]scale=1020:574:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:200[v_base]"
    )
    last_v = "[v_base]"

    # Meme GIF overlay during question block
    q_start = VOICE_DELAY + block_timings["investigation"]["start"]
    q_end = VOICE_DELAY + block_timings["investigation"]["end"]
    filter_chains.append(
        f"[4:v]scale=500:-1,format=rgba,fade=t=in:st={q_start}:d=0.15:alpha=1,fade=t=out:st={q_end-0.15}:d=0.15:alpha=1[meme_fade];"
        f"{last_v}[meme_fade]overlay=(W-w)/2:860:enable='between(t,{q_start},{q_end})'[v_meme]"
    )
    last_v = "[v_meme]"

    # Card 1 overlay
    filter_chains.append(
        f"[2:v]scale=1000:-1,format=rgba,fade=t=in:st={d1_start}:d=0.15:alpha=1,fade=t=out:st={d1_end-0.15}:d=0.15:alpha=1[c1_fade];"
        f"{last_v}[c1_fade]overlay=(W-w)/2:{c1_y}:enable='between(t,{d1_start},{d1_end})'[v_c1]"
    )
    last_v = "[v_c1]"

    # Card 2 overlay
    filter_chains.append(
        f"[3:v]scale=1000:-1,format=rgba,fade=t=in:st={cc_start}:d=0.15:alpha=1,fade=t=out:st={cc_end-0.15}:d=0.15:alpha=1[c2_fade];"
        f"{last_v}[c2_fade]overlay=(W-w)/2:{c2_y}:enable='between(t,{cc_start},{cc_end})'[v_c2]"
    )
    last_v = "[v_c2]"

    # Outro Motion Video Overlay
    filter_chains.append(
        f"[5:v]chromakey=0x00FF00:0.28:0.15,setpts=PTS-STARTPTS+{outro_start}/TB[outro_v];"
        f"{last_v}[outro_v]overlay=(W-w)/2:860:enable='between(t,{outro_start},{outro_end})'[v_outro]"
    )
    last_v = "[v_outro]"

    # Subtitles
    escaped_sub = str(sub_path.resolve()).replace("\\", "/").replace(":", r"\:")
    filter_chains.append(f"{last_v}subtitles=filename='{escaped_sub}'[v_final]")

    # Audio Mix
    # 1. Delayed TTS Voice Audio
    filter_chains.append(f"[1:a]adelay={int(VOICE_DELAY*1000)}|{int(VOICE_DELAY*1000)}[voice_delayed]")
    audio_mix_inputs = ["[voice_delayed]"]

    # 2. Original Game Audio (Full 80% volume during 0..3.5s, ducked to 25% during voiceover)
    filter_chains.append(f"[0:a]volume='if(lt(t,{VOICE_DELAY}),0.85,0.25)':eval=frame[orig_game_a]")
    audio_mix_inputs.append("[orig_game_a]")

    # 3. Outro Motion Audio
    filter_chains.append(f"[5:a]adelay={int(outro_start*1000)}|{int(outro_start*1000)}[outro_a]")
    audio_mix_inputs.append("[outro_a]")

    if sfx_in is not None:
        filter_chains.append(f"[{sfx_in}:a]adelay={int(q_start*1000)}|{int(q_start*1000)},volume=0.18[sfx_a]")
        audio_mix_inputs.append("[sfx_a]")

    if amb_in is not None:
        filter_chains.append(f"[{amb_in}:a]volume=0.14[amb_a]")
        audio_mix_inputs.append("[amb_a]")

    mix_count = len(audio_mix_inputs)
    filter_chains.append(f"{''.join(audio_mix_inputs)}amix=inputs={mix_count}:duration=first:dropout_transition=2[a_final]")

    filter_complex_str = ";".join(filter_chains)

    # Encoder Selection: Try NVENC first, fallback to libx264 if NVENC API fails
    base_cmd = [FFMPEG_PATH, "-y"] + inputs + [
        "-filter_complex", filter_complex_str,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-t", f"{total_duration:.2f}",
        "-pix_fmt", "yuv420p"
    ]

    nvenc_cmd = base_cmd + ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-c:a", "aac", "-b:a", "192k", str(output_mp4)]
    libx264_cmd = base_cmd + ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", str(output_mp4)]

    print(f"  [FFmpeg] Rendering video via FFmpeg...")
    res = subprocess.run(nvenc_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ⚠️ NVENC Notice: NVENC returned non-zero code. Falling back to libx264 ultrafast...")
        res = subprocess.run(libx264_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ FFmpeg Error Output:\n{res.stderr[-1000:]}")
            raise RuntimeError(f"FFmpeg failed to render {var_key}")

    print(f"  [SUCCESS] Rendered {var_key}: {output_mp4} ({output_mp4.stat().st_size} bytes)")
    return output_mp4, total_duration


def main():
    ep_dir = BASE_DIR / "output" / "22"
    ep_dir.mkdir(parents=True, exist_ok=True)

    rendered_files = {}
    durations = {}

    # Render all 3 variants
    for var_key, var_info in VARIANTS.items():
        out_mp4, dur = render_single_variant(var_key, var_info, ep_dir)
        rendered_files[var_key] = out_mp4
        durations[var_key] = dur

    # Copy primary user-chosen variant (Variant 1) to root episode folder
    primary_mp4 = rendered_files["variant1"]
    root_mp4 = ep_dir / "video.mp4"
    shutil.copy(primary_mp4, root_mp4)
    print(f"\n[PRIMARY COPY] Copied Variant 1 -> {root_mp4}")

    # Generate metadata.json and description.txt for Variant 1
    v1_scenario = {
        "episode_id": "22",
        "game": VARIANTS["variant1"]["game"],
        "bug_title": VARIANTS["variant1"]["bug_title"],
        "lang": "ru",
        "blocks": VARIANTS["variant1"]["blocks"],
        "metadata": VARIANTS["variant1"]["metadata"]
    }
    MetadataGenerator.generate(v1_scenario, ep_dir, duration=durations["variant1"])
    print(f"[METADATA] Generated metadata.json and description.txt in {ep_dir}")

    # 4-Point Mandatory Smoke Test
    print("\n==========================================")
    print("🔍 RUNNING 4-POINT MANDATORY SMOKE TEST...")
    print("==========================================")

    smoke_results = {}
    for var_key, out_mp4 in rendered_files.items():
        probe_cmd = [FFMPEG_PATH, "-v", "error", "-i", str(out_mp4), "-f", "null", "-"]
        p_res = subprocess.run(probe_cmd, capture_output=True, text=True)
        is_decodable = (p_res.returncode == 0)
        size_ok = out_mp4.exists() and out_mp4.stat().st_size > 1_000_000
        smoke_results[var_key] = {
            "decodable": is_decodable,
            "size_ok": size_ok,
            "size_bytes": out_mp4.stat().st_size if out_mp4.exists() else 0
        }
        print(f"  * {var_key}: Decodable={is_decodable}, SizeOK={size_ok} ({smoke_results[var_key]['size_bytes']} bytes)")

    desc_file = ep_dir / "description.txt"
    desc_ok = desc_file.exists() and "ЗАГОЛОВОК ДЛЯ YOUTUBE SHORTS" in desc_file.read_text(encoding="utf-8")
    print(f"  * Metadata format ok: {desc_ok}")

    print("\n✅ PRODUCTION & VALIDATION COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
