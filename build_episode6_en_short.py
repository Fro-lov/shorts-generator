import sys
import io
import subprocess
from pathlib import Path

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
from src.core.html_motion_renderer import HTMLMotionRenderer
from src.core.output_manager import EpisodeOutputManager
from src.core.music_generator import get_random_bgm
from src.core.metadata_generator import MetadataGenerator


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


def build_episode_6_en():
    print("=" * 60)
    print("🚀 STARTING BUILD EPISODE #6_EN (Assetto Corsa: Quaternions & Wide Memes)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/6] Preparing file structure in output/6_en/...")
    mgr = EpisodeOutputManager("6_en")
    paths = mgr.get_paths("video.mp4")

    # Clean gameplay clip (4.84s loop of pure racing car)
    gameplay_src = ASSETS_DIR / "downloads" / "clean_wheel_bug.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/
    diag1a_path = mgr.visuals_dir / "scheme1a_normal_en.png"
    diag1b_path = mgr.visuals_dir / "scheme1b_glitch_en.png"
    diag2a_path = mgr.visuals_dir / "scheme2a_physics_en.png"
    diag2b_path = mgr.visuals_dir / "scheme2b_visual_en.png"
    code_path = mgr.visuals_dir / "scheme3_code_fix_en.png"

    # Contextual pure Memes
    meme_helicopter2_gif = ASSETS_DIR / "memes" / "helicopter2.gif"
    meme_wolf_img = ASSETS_DIR / "memes" / "wolf_captioned_en.png"

    # SFX
    sfx_helicopter = ASSETS_DIR / "sfx" / "helicopter.mp3"
    sfx_transformers = ASSETS_DIR / "sfx" / "transformers.mp3"

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
            "text": "In Assetto Corsa, a GT3 racer speeds at full throttle, but the front wheel decided to become a helicopter!",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "Yet the car holds its racing line perfectly. How is that possible? Let's investigate!",
            "trigger_bgm": True
        },
        {
            "id": "scheme1",
            "text": "In game engines, rotation isn't just simple 3D angles, but four-dimensional quaternions. When the car drives, steers, and rolls the tire simultaneously, calculations get tangled into a crazy axis!",
            "trigger_bgm": False
        },
        {
            "id": "scheme2",
            "text": "Meanwhile, the physics raycast collider runs completely separate from graphics. So the car grips 100%, while the 3D tire breakdances at 3,500 RPM.",
            "trigger_bgm": False
        },
        {
            "id": "fix",
            "text": "The developers simply need to normalize the quaternion properly and decouple steering yaw from wheel roll.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "Now the racer stays glued to the tarmac. Or maybe the car just skipped leg day yesterday? Subscribe for more crazy game bugs!",
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

        for ev in events:
            all_subtitle_events.append({
                "text": ev["text"],
                "start": b_start + ev["start"],
                "end": b_start + ev["end"]
            })

        block_audio_paths.append(b_audio)
        current_time = b_end + 0.15

    total_duration = current_time + 0.5
    print(f"   ✓ Generated {len(scene_blocks_def)} voice blocks.")
    print(f"   ✓ Total duration: {total_duration:.2f}s.")
    print(f"   ✓ Ambient music start: {bgm_start_time:.2f}s.")

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
    print("\n[3/6] Generating stylized subtitles (MarginV=420)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",
        outline_width=5,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visual Cards using CSS HTMLMotionRenderer (English)
    print("\n[4/6] Generating English CSS Motion UI visual cards (Large Typography)...")
    html_renderer = HTMLMotionRenderer(width=1000, height=540)
    html_renderer.render_scheme1a_normal(diag1a_path, lang="en")
    html_renderer.render_scheme1b_glitch(diag1b_path, lang="en")
    html_renderer.render_scheme2a_physics(diag2a_path, lang="en")
    html_renderer.render_scheme2b_visual(diag2b_path, lang="en")
    html_renderer.render_scheme3_code_fix(code_path, lang="en")

    # 5. Background Video with Continuous Looping Gameplay
    print("\n[5/6] Preparing pure looped 9:16 background gameplay...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg (Zero-Overlap Grid)
    print(f"\n[6/6] Rendering final video & audio mix in FFmpeg (NVENC GPU)...")

    hook_start = block_timings["hook"]["start"]
    hook_end = block_timings["hook"]["end"]

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    sch1_start = block_timings["scheme1"]["start"]
    sch1_end = block_timings["scheme1"]["end"]
    sch1_mid = sch1_start + (sch1_end - sch1_start) * 0.48

    sch2_start = block_timings["scheme2"]["start"]
    sch2_end = block_timings["scheme2"]["end"]
    sch2_mid = sch2_start + (sch2_end - sch2_start) * 0.50

    fix_start = block_timings["fix"]["start"]
    fix_end = block_timings["fix"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # SFX Delays in ms
    sfx_heli_delay_ms = int(max(0, hook_start * 1000))
    sfx_trans_delay_ms = int(max(0, inv_start * 1000))
    bgm_delay_ms = int(max(0, bgm_start_time * 1000))

    filter_chains = [
        # Hook: Helicopter engineer meme scaled full width (980px) in safe zone y=860
        f"[5:v]scale=980:-1,format=rgba,fade=t=in:st={hook_start:.2f}:d=0.2:alpha=1,fade=t=out:st={hook_end-0.2:.2f}:d=0.2:alpha=1[m_heli]",
        f"[0:v][m_heli]overlay=(W-w)/2:860:enable='between(t,{hook_start:.2f},{hook_end:.2f})'[v1]",

        # Investigation: Wolf quote meme scaled full width (1000px) in safe zone y=860
        f"[6:v]scale=1000:-1,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.25:alpha=1,fade=t=out:st={inv_end-0.25:.2f}:d=0.25:alpha=1[m_wolf]",
        f"[v1][m_wolf]overlay=(W-w)/2:860:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v2]",

        # Scheme 1A: Normal 3D Decoupled Rotation (lower zone y=860)
        f"[7:v]scale=1000:-1,format=rgba,fade=t=in:st={sch1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={sch1_mid-0.2:.2f}:d=0.2:alpha=1[v_d1a]",
        f"[v2][v_d1a]overlay=(W-w)/2:860:enable='between(t,{sch1_start:.2f},{sch1_mid:.2f})'[v3]",

        # Scheme 1B: Glitch 4D Quaternion Tangled (lower zone y=860)
        f"[8:v]scale=1000:-1,format=rgba,fade=t=in:st={sch1_mid:.2f}:d=0.2:alpha=1,fade=t=out:st={sch1_end-0.25:.2f}:d=0.25:alpha=1[v_d1b]",
        f"[v3][v_d1b]overlay=(W-w)/2:860:enable='between(t,{sch1_mid:.2f},{sch1_end:.2f})'[v4]",

        # Scheme 2A: Physics Solver 100% Grip (lower zone y=860)
        f"[9:v]scale=1000:-1,format=rgba,fade=t=in:st={sch2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={sch2_mid-0.2:.2f}:d=0.2:alpha=1[v_d2a]",
        f"[v4][v_d2a]overlay=(W-w)/2:860:enable='between(t,{sch2_start:.2f},{sch2_mid:.2f})'[v5]",

        # Scheme 2B: Visual 3D Mesh Breakdance 3500 RPM (lower zone y=860)
        f"[10:v]scale=1000:-1,format=rgba,fade=t=in:st={sch2_mid:.2f}:d=0.2:alpha=1,fade=t=out:st={sch2_end-0.25:.2f}:d=0.25:alpha=1[v_d2b]",
        f"[v5][v_d2b]overlay=(W-w)/2:860:enable='between(t,{sch2_mid:.2f},{sch2_end:.2f})'[v6]",

        # Scheme 3: CSS Extra Large Code Fix Card (lower zone y=860)
        f"[11:v]scale=1000:-1,format=rgba,fade=t=in:st={fix_start:.2f}:d=0.25:alpha=1,fade=t=out:st={fix_end-0.25:.2f}:d=0.25:alpha=1[v_fix]",
        f"[v6][v_fix]overlay=(W-w)/2:860:enable='between(t,{fix_start:.2f},{fix_end:.2f})'[v7]"
    ]

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v7]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing: Voice + Ambient + Helicopter SFX + Transformers SFX
    filter_chains.append(
        f"[1:a]volume=1.0[a_voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[3:a]adelay={sfx_heli_delay_ms}|{sfx_heli_delay_ms},volume=0.35[a_heli];"
        f"[4:a]adelay={sfx_trans_delay_ms}|{sfx_trans_delay_ms},volume=0.35[a_trans];"
        f"[a_voice][a_bgm][a_heli][a_trans]amix=inputs=4:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_helicopter),
        "-i", str(sfx_transformers),
        "-ignore_loop", "0", "-i", str(meme_helicopter2_gif),
        "-loop", "1", "-i", str(meme_wolf_img),
        "-loop", "1", "-i", str(diag1a_path),
        "-loop", "1", "-i", str(diag1b_path),
        "-loop", "1", "-i", str(diag2a_path),
        "-loop", "1", "-i", str(diag2b_path),
        "-loop", "1", "-i", str(code_path),
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

    # Generate preview frames
    print("\n📸 Generating preview frames in output/6_en/frames/...")
    frame_times = [
        hook_start + 1.0,
        inv_start + 1.0,
        sch1_start + 1.0,
        sch1_mid + 1.0,
        sch2_start + 1.0,
        sch2_mid + 1.0,
        fix_start + 1.0,
        outro_start + 1.0
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

    # 7. Generate Metadata & Description
    print("\n📝 Generating metadata & description...")
    scenario_data = {
        "episode_id": "6_en",
        "game": "Assetto Corsa",
        "bug_title": "Propeller Wheel Glitch (4D Quaternion Bug)",
        "lang": "en",
        "blocks": [
            {"id": "hook", "title": "Propeller Wheel", "start": hook_start, "end": hook_end},
            {"id": "investigation", "title": "Bug Investigation", "start": inv_start, "end": inv_end},
            {"id": "scheme1", "title": "4D Quaternion Rotation", "start": sch1_start, "end": sch1_end},
            {"id": "scheme2", "title": "Physics vs Visual Breakdance", "start": sch2_start, "end": sch2_end},
            {"id": "fix", "title": "Quaternion Code Fix", "start": fix_start, "end": fix_end},
            {"id": "outro", "title": "Skipped Leg Day", "start": outro_start, "end": outro_end}
        ],
        "metadata": {
            "tags": ["assettocorsa", "simracing", "racingglitch", "gamephysics", "gamedev", "quaternion", "shorts", "gaming", "bugs"]
        }
    }
    MetadataGenerator.generate(
        scenario_data=scenario_data,
        output_dir=mgr.root_dir,
        duration=total_duration
    )

    print(f"\n✨ [SUCCESS] EPISODE #6_EN (EN) BUILT & SAVED TO: {final_video}")
    return final_video, block_timings, total_duration, bgm_path.name


if __name__ == "__main__":
    build_episode_6_en()
