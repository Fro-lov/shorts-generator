import sys
import io
import re
import subprocess
from pathlib import Path

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
from src.core.episode7_visuals import Episode7VisualsGenerator
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
        f"[0:v]scale=1020:-1[fg];"
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


def build_episode_7_en():
    print("=" * 60)
    print("🚀 STARTING BUILD EPISODE #7_EN (Red Dead Redemption 2: Horseback T-Pose)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/6] Preparing file structure in output/7_en/...")
    mgr = EpisodeOutputManager("7_en")
    paths = mgr.get_paths("video.mp4")

    # Clean gameplay clip
    gameplay_src = ASSETS_DIR / "downloads" / "rdr_tpose_clean.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    card1_path = mgr.visuals_dir / "card1_causes_en.png"
    card2_path = mgr.visuals_dir / "card2_fallback_en.png"

    # Contextual Memes & Diagrams
    meme_hook = ASSETS_DIR / "memes" / "tpose.jfif"
    meme_plane = ASSETS_DIR / "memes" / "tposeplane.jfif"
    meme_bones = ASSETS_DIR / "memes" / "bones.png"
    meme_anim_gif = ASSETS_DIR / "memes" / "animation.gif"

    # SFX
    sfx_what = ASSETS_DIR / "sfx" / "what.mp3"
    sfx_win_error = ASSETS_DIR / "sfx" / "windows_error.mp3"

    # Ambient Music
    ambient_dir = ASSETS_DIR / "music" / "ambient"
    bgm_path = get_random_bgm(ambient_dir)
    print(f"   ✓ Selected YouTube Safe Ambient Music: {bgm_path.name}")

    # 2. Scene-based TTS Blocks Definition (English)
    print("\n[2/6] Generating voiceover by semantic blocks...")
    tts = TTSEngine(voice="en-US-ChristopherNeural", rate="+6%")

    scene_blocks_def = [
        {
            "id": "hook",
            "text": "Dutch van der Linde is so confident in his plan that he is asserting total T-pose dominance while riding horseback!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "In Red Dead Redemption 2, every single detail is hyper-realistic. So why did Dutch suddenly turn into an airplane? Let's investigate!",
            "trigger_bgm": True
        },
        {
            "id": "bones",
            "text": "Every 3D character is rigged to a skeletal bone hierarchy. Without active animation clips, all joints sit at zero rotations — that is the default Bind Pose.",
            "trigger_bgm": False
        },
        {
            "id": "graph",
            "text": "The game engine runs a massive animation state machine. When mounting a horse, the graph requests the riding animation. If it isn't ready in memory, the engine falls back to default.",
            "trigger_bgm": False
        },
        {
            "id": "card1",
            "text": "Why does the animation fail to load in time? In a huge open world, the animation asset couldn't stream from disk to VRAM in time, or the state transition returned a null pointer.",
            "trigger_bgm": False
        },
        {
            "id": "card2",
            "text": "To prevent a crash or freeze, the engine resets all bone angles to zero. The T-pose is actually a fail-safe fuse protecting the game from crashes.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "The T-pose bug happens across many games, and the technical root causes are almost always the same. Drop a like and subscribe for more game physics breakdowns!",
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
    print(f"   ✓ Сгенерировано {len(scene_blocks_def)} речевых блоков.")
    print(f"   ✓ Общая длительность озвучки: {current_time:.2f} сек (итоговое видео: {total_duration:.2f} сек).")
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
    print("\n[3/6] Генерация стилизованных субтитров (MarginV=420)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",
        outline_width=5,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visual Cards using Episode7VisualsGenerator
    print("\n[4/6] Rendering graphics cards (Strict Minimal Dark + Large Text)...")
    vis_gen = Episode7VisualsGenerator(width=1000, height=540)
    vis_gen.render_card1_causes_en(card1_path)
    vis_gen.render_card2_fallback_en(card2_path)

    # 5. Background Video with Continuous Looping Pure Gameplay
    print("\n[5/6] Preparing background video (9:16 + continuous loop)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg (Strict Zero-Overlap Grid)
    print("\n[6/6] Rendering video and composite layers with FFmpeg (NVENC GPU)...")

    hook_start = block_timings["hook"]["start"]
    hook_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    bones_start = block_timings["bones"]["start"]
    bones_end = block_timings["bones"]["end"]

    graph_start = block_timings["graph"]["start"]
    graph_end = block_timings["graph"]["end"]

    card1_start = block_timings["card1"]["start"]
    card1_end = block_timings["card1"]["end"]

    card2_start = block_timings["card2"]["start"]
    card2_end = block_timings["card2"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # SFX Delays in ms
    sfx_what_delay_ms = int(max(0, inv_start * 1000))
    sfx_err_delay_ms = int(max(0, card1_start * 1000))
    bgm_delay_ms = int(max(0, bgm_start_time * 1000))

    # Inputs:
    # 0: temp_bg (video)
    # 1: voice_final (audio)
    # 2: bgm (audio)
    # 3: sfx_what (audio)
    # 4: sfx_win_error (audio)
    # 5: tpose.jfif (image)
    # 6: tposeplane.jfif (image)
    # 7: bones.png (image)
    # 8: animation.gif (GIF)
    # 9: card1_causes_en.png (image)
    # 10: card2_fallback_en.png (image)

    filter_chains = [
        # Hook: tpose meme (max height 520px in zone y=860..1400)
        f"[5:v]scale=-1:520,format=rgba,fade=t=in:st={hook_start:.2f}:d=0.2:alpha=1,fade=t=out:st={hook_end-0.2:.2f}:d=0.2:alpha=1[m_hook]",
        f"[0:v][m_hook]overlay=(W-w)/2:870:enable='between(t,{hook_start:.2f},{hook_end:.2f})'[v1]",

        # Investigation: tpose plane meme (scale=900:-1)
        f"[6:v]scale=900:-1,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.25:alpha=1,fade=t=out:st={inv_end-0.25:.2f}:d=0.25:alpha=1[m_plane]",
        f"[v1][m_plane]overlay=(W-w)/2:890:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v2]",

        # Bones Anatomy: bones.png (scale=-1:500)
        f"[7:v]scale=-1:500,format=rgba,fade=t=in:st={bones_start:.2f}:d=0.25:alpha=1,fade=t=out:st={bones_end-0.25:.2f}:d=0.25:alpha=1[m_bones]",
        f"[v2][m_bones]overlay=(W-w)/2:880:enable='between(t,{bones_start:.2f},{bones_end:.2f})'[v3]",

        # Animation Graph: animation.gif (scale=860:-1)
        f"[8:v]scale=860:-1,format=rgba,fade=t=in:st={graph_start:.2f}:d=0.25:alpha=1,fade=t=out:st={graph_end-0.25:.2f}:d=0.25:alpha=1[m_graph]",
        f"[v3][m_graph]overlay=(W-w)/2:880:enable='between(t,{graph_start:.2f},{graph_end:.2f})'[v4]",

        # Card 1: Causes (scale=1000:-1)
        f"[9:v]scale=1000:-1,format=rgba,fade=t=in:st={card1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v4][v_c1]overlay=(W-w)/2:860:enable='between(t,{card1_start:.2f},{card1_end:.2f})'[v5]",

        # Card 2: Fallback & Protection (scale=1000:-1)
        f"[10:v]scale=1000:-1,format=rgba,fade=t=in:st={card2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v5][v_c2]overlay=(W-w)/2:860:enable='between(t,{card2_start:.2f},{card2_end:.2f})'[v6]"
    ]

    # Outro meme overlay (show tpose hook meme during outro)
    filter_chains.append(
        f"[5:v]scale=-1:520,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.25:alpha=1,fade=t=out:st={outro_end-0.25:.2f}:d=0.25:alpha=1[m_outro];"
        f"[v6][m_outro]overlay=(W-w)/2:870:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v7]"
    )

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v7]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing: Voice + Ambient + SFX
    filter_chains.append(
        f"[1:a]volume=1.0[a_voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[3:a]adelay={sfx_what_delay_ms}|{sfx_what_delay_ms},volume=0.32[a_what];"
        f"[4:a]adelay={sfx_err_delay_ms}|{sfx_err_delay_ms},volume=0.32[a_err];"
        f"[a_voice][a_bgm][a_what][a_err]amix=inputs=4:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_what),
        "-i", str(sfx_win_error),
        "-loop", "1", "-i", str(meme_hook),
        "-loop", "1", "-i", str(meme_plane),
        "-loop", "1", "-i", str(meme_bones),
        "-ignore_loop", "0", "-i", str(meme_anim_gif),
        "-loop", "1", "-i", str(card1_path),
        "-loop", "1", "-i", str(card2_path),
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

    print("   Running hardware rendering with NVENC...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError("Video rendering failed!")

    print(f"\n🎉 Video rendered successfully: {final_video}")

    # 7. Extract preview frames into frames/
    print("\n[7/8] Extracting preview frames into frames/...")
    frames_dir = mgr.frames_dir
    test_moments = [
        (hook_start + 1.0, "01_hook_tpose"),
        (inv_start + 1.0, "02_investigation_plane"),
        (bones_start + 1.0, "03_bones_bindpose"),
        (graph_start + 1.5, "04_animation_graph"),
        (card1_start + 1.5, "05_card1_causes"),
        (card2_start + 1.5, "06_card2_fallback"),
        (outro_start + 1.0, "07_outro")
    ]
    for ts, name in test_moments:
        frame_out = frames_dir / f"shot_{name}.jpg"
        cmd_f = [
            FFMPEG_PATH, "-y",
            "-ss", f"{ts:.2f}",
            "-i", str(final_video),
            "-vframes", "1",
            "-q:v", "2",
            str(frame_out)
        ]
        subprocess.run(cmd_f, capture_output=True)

    # 8. Metadata Generation
    print("\n[8/8] Generating description and metadata...")
    scenario_info = {
        "episode_id": "7_en",
        "lang": "en",
        "game": "Red Dead Redemption 2",
        "bug_title": "Horseback T-Pose Glitch (Animation State Machine & Bind Pose)",
        "blocks": scene_blocks_def
    }
    MetadataGenerator.generate(
        scenario_data=scenario_info,
        output_dir=mgr.root_dir,
        duration=total_duration
    )

    print("\n" + "=" * 60)
    print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
    print(f"📁 Output Video: {final_video.resolve()}")
    print("=" * 60)
    return final_video


if __name__ == "__main__":
    build_episode_7_en()
