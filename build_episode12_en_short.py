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
    ASSETS_DIR, FFMPEG_PATH, VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ
)
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode12_en_visuals import Episode12ENVisualsGenerator
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
    Creates a full 9:16 background from the clean gameplay clip:
    - 16:9 cropped sharp gameplay centered in top window (y=200..774, width 1020, height 574)
    - Vertically blurred background across the whole 1080x1920 canvas.
    - Loops seamlessly for the entire video duration.
    """
    base_seg = temp_dir / "base_seg_en.mp4"

    # Precise crop focusing on the ball save and the goalkeeper launch
    crop_w, crop_h = 576, 324
    crop_x, crop_y = 0, 180

    cmd_base = [
        FFMPEG_PATH, "-y",
        "-i", str(gameplay_mp4),
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=28:8[bg];"
        f"[0:v]crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1020:574[fg];"
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


def build_short():
    print("=" * 60)
    print("🚀 STARTING EPISODE #12 (ENGLISH): FIFA 22 Goalkeeper Yeeted To Orbit")
    print("=" * 60)

    # 1. Setup Output Structure in output/12_en/
    print("\n[1/7] Initializing output directory in output/12_en/...")
    mgr = EpisodeOutputManager("12_en")
    paths = mgr.get_paths("video.mp4")

    # Gameplay clip
    gameplay_src = ASSETS_DIR / "downloads" / "12.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    card1_path = mgr.visuals_dir / "card1_impulse_explosion_en.png"
    card2_path = mgr.visuals_dir / "card2_fix_en.png"

    # Contextual Memes
    meme_catch = ASSETS_DIR / "memes" / "catch.jfif"
    meme_flying = ASSETS_DIR / "memes" / "flying.jfif"
    meme_plane_landing = ASSETS_DIR / "memes" / "plane_landing_en.png"

    # SFX
    sfx_sokol = ASSETS_DIR / "sfx" / "sokol_ssha.mp3"
    sfx_samoletik = ASSETS_DIR / "sfx" / "samoletik.mp3"

    # 2. Scene-based TTS Blocks Definition (English)
    print("\n[2/7] Generating English speech by semantic blocks (Edge-TTS)...")
    tts = TTSEngine(voice="en-US-ChristopherNeural", rate="+8%")

    # Initial pure gameplay buffer duration (original music from TikTok plays at 100%)
    INITIAL_GAMEPLAY_BUFFER = 2.5

    scene_blocks_def = [
        {
            "id": "hook",
            "text": "How it feels when a goalkeeper actually catches this strike!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Seems like a routine low-corner save. But why did the goalkeeper's model yeet straight into orbit?",
            "trigger_bgm": True
        },
        {
            "id": "card1_pipeline1",
            "text": "It's a classic conflict between animation and physics! The ball was flying under the physics solver, while the engine triggered a save animation and locked the keeper's hand bones to the ball's socket.",
            "trigger_bgm": False
        },
        {
            "id": "card2_pipeline2",
            "text": "Right at that moment, the striker kicked the ball! The ball got a massive upward impulse and towed the locked goalkeeper straight into the stratosphere! The fix? Simply abort the catch if the ball's velocity exceeds limits.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Eventually, the keeper returned from vacation, touched down on the grass, and cleanly finished the save. Now that's what I call a true professional! Drop a like and subscribe to GameBug!",
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

    total_duration = current_time + 0.5
    print(f"   ✓ First {INITIAL_GAMEPLAY_BUFFER:.1f}s: TikTok music plays at 100% volume.")
    print(f"   ✓ Generated {len(scene_blocks_def)} speech blocks.")
    print(f"   ✓ Total video duration: {total_duration:.2f}s.")

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
    print("\n[3/7] Generating styled dynamic subtitles (MarginV=420)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",
        outline_width=5,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visuals: 2D Graphic Cards
    print("\n[4/7] Generating English graphic cards (dense layout, zero empty space)...")
    vis_gen = Episode12ENVisualsGenerator(width=1000, height=1280)
    vis_gen.render_card1_pipeline_part1(card1_path)
    vis_gen.render_card2_pipeline_part2(card2_path)

    # 5. Background Video with Continuous Looping Pure Gameplay
    print("\n[5/7] Preparing gameplay background video (9:16 + centered top window y=200..774)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg (Zero-Overlap Grid + Top 2/3 Diagrams)
    print(f"\n[6/7] Compositing visual layers and audio tracks in FFmpeg (NVENC GPU)...")

    hook_start = block_timings["hook"]["start"]
    hook_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    card1_start = block_timings["card1_pipeline1"]["start"]
    card1_end = block_timings["card1_pipeline1"]["end"]

    card2_start = block_timings["card2_pipeline2"]["start"]
    card2_end = block_timings["card2_pipeline2"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")

    # Timings for audio delays in ms
    voice_delay_ms = int(INITIAL_GAMEPLAY_BUFFER * 1000)
    sfx_sokol_delay_ms = int(hook_start * 1000)
    sfx_samoletik_delay_ms = int(outro_start * 1000)

    filter_chains = [
        # Hook meme: Eagle catching ball in zone y=880
        f"[5:v]scale=-1:500,format=rgba,fade=t=in:st={hook_start:.2f}:d=0.2:alpha=1,fade=t=out:st={hook_end-0.2:.2f}:d=0.2:alpha=1[m_catch]",
        f"[0:v][m_catch]overlay=(W-w)/2:880:enable='between(t,{hook_start:.2f},{hook_end:.2f})'[v0]",

        # Investigation meme: Camel parachuting in zone y=860
        f"[6:v]scale=-1:520,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.2:alpha=1,fade=t=out:st={inv_end-0.2:.2f}:d=0.2:alpha=1[m_fly]",
        f"[v0][m_fly]overlay=(W-w)/2:860:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v1]",

        # Card 1 (Pipeline Part 1): Top 2/3 at y=80
        f"[7:v]scale=1000:-1,format=rgba,fade=t=in:st={card1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v1][v_c1]overlay=(W-w)/2:80:enable='between(t,{card1_start:.2f},{card1_end:.2f})'[v2]",

        # Card 2 (Pipeline Part 2 & Fix): Top 2/3 at y=80
        f"[8:v]scale=1000:-1,format=rgba,fade=t=in:st={card2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v2][v_c2]overlay=(W-w)/2:80:enable='between(t,{card2_start:.2f},{card2_end:.2f})'[v3]",

        # Outro meme: Plane landing captioned in zone y=880
        f"[9:v]scale=840:-1,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.2:alpha=1,fade=t=out:st={outro_end-0.2:.2f}:d=0.2:alpha=1[m_plane]",
        f"[v3][m_plane]overlay=(W-w)/2:880:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v_ass_pre]",

        # Burn-in styled Subtitles (.ass)
        f"[v_ass_pre]subtitles=filename='{rel_sub_path}'[v_final]",

        # Audio mixing:
        # Original TikTok music: 1.0 volume in initial buffer (0..2.5s), ducked to 0.12 during voiceover
        # SFX Sokol at 0.18 (normalized)
        # SFX Samoletik at 0.06 (balanced so it never drowns out voice)
        f"[1:a]volume=enable='between(t,0,{INITIAL_GAMEPLAY_BUFFER})':volume=1.0,volume=enable='gte(t,{INITIAL_GAMEPLAY_BUFFER})':volume=0.12[a_game]",
        f"[2:a]adelay={voice_delay_ms}|{voice_delay_ms},volume=1.0[a_voice]",
        f"[3:a]adelay={sfx_sokol_delay_ms}|{sfx_sokol_delay_ms},volume=0.18[a_sokol]",
        f"[4:a]adelay={sfx_samoletik_delay_ms}|{sfx_samoletik_delay_ms},volume=0.12[a_samolet]",
        f"[a_game][a_voice][a_sokol][a_samolet]amix=inputs=4:duration=longest:normalize=0[a_final]"
    ]

    cmd_render = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(gameplay_src),
        "-i", str(voice_final_path),
        "-i", str(sfx_sokol),
        "-i", str(sfx_samoletik),
        "-loop", "1", "-i", str(meme_catch),
        "-loop", "1", "-i", str(meme_flying),
        "-loop", "1", "-i", str(card1_path),
        "-loop", "1", "-i", str(card2_path),
        "-loop", "1", "-i", str(meme_plane_landing),
        "-filter_complex", ";".join(filter_chains),
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", str(VIDEO_CQ),
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-t", f"{total_duration:.2f}",
        str(final_video)
    ]

    print("   ► Running FFmpeg NVENC hardware accelerated render...")
    subprocess.run(cmd_render, check=True)
    print(f"   ✓ Video rendered successfully: {final_video}")

    # 7. Generate Description and Metadata (English)
    print("\n[7/7] Generating metadata and description files...")
    scenario_data = {
        "episode_id": "12_en",
        "lang": "en",
        "game": "FIFA 22",
        "bug_title": "Goalkeeper Yeeted Straight To Orbit",
        "blocks": scene_blocks_def,
        "metadata": {
            "title": "FIFA 22 Goalkeeper Launched Into Orbit On A Tow Cable! 🚀⚽",
            "short_title": "Goalkeeper launched into orbit on a tow cable! #shorts #gaming",
            "description": (
                "How it feels when a goalkeeper actually catches this strike!\n"
                "Seems like a routine low-corner save. But why did the goalkeeper's model yeet straight into orbit?\n\n"
                "Bug Breakdown:\n"
                "00:00 - Routine Save\n"
                "00:04 - Yeeted to Orbit\n"
                "00:10 - Bug Pipeline (Steps 1-3: Bone Lock Trap)\n"
                "00:20 - Bug Pipeline (Steps 4-5: Stratosphere Launch & C++ Fix)\n"
                "00:30 - Preparing for Landing!\n\n"
                "#fifa22 #ea #gamedev #gamephysics #shorts #gaming #glitch"
            ),
            "tags": ["fifa22", "fifa", "easports", "gamephysics", "gaming", "gamedev", "shorts", "glitch", "funnygaming"]
        }
    }
    MetadataGenerator.generate(
        scenario_data=scenario_data,
        output_dir=mgr.root_dir,
        duration=total_duration
    )
    print("   ✓ metadata.json and description.txt generated successfully.")

    print("\n" + "=" * 60)
    print("🎉 EPISODE #12 (ENGLISH) BUILD COMPLETE!")
    print(f"📁 Directory: {mgr.root_dir}")
    print(f"🎬 Final Video: {final_video}")
    print(f"⏱ Duration: {total_duration:.2f}s")
    print("=" * 60)
    return final_video


if __name__ == "__main__":
    build_short()
