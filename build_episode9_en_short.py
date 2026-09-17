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
    ASSETS_DIR, FFMPEG_PATH, VIDEO_WIDTH, VIDEO_HEIGHT, FPS,
    VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ
)
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode9_en_visuals import Episode9ENVisualsGenerator
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
    - Loops continuously throughout the total video duration, trimmed at 15.4s to cut TikTok outro.
    """
    base_seg = temp_dir / "base_seg.mp4"
    cmd_base = [
        FFMPEG_PATH, "-y",
        "-t", "15.4",
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


def build_episode_9_en():
    print("=" * 60)
    print("🚀 STARTING BUILD EPISODE #9_EN (S.T.A.L.K.E.R. 2: Black Hole & Buffer Glitch)")
    print("=" * 60)

    # 1. Setup Output Structure
    print("\n[1/6] Preparing file structure in output/9_en/...")
    mgr = EpisodeOutputManager("9_en")
    paths = mgr.get_paths("video.mp4")

    # Clean gameplay clip
    gameplay_src = ASSETS_DIR / "downloads" / "stalker2_blackhole.mp4"
    voice_final_path = paths["voice"]
    ass_path = paths["subtitles"]
    temp_bg = paths["temp_bg"]
    final_video = paths["final_video"]

    # Visual assets paths in visuals/ (Top 2/3 Vertical Diagrams)
    card1_path = mgr.visuals_dir / "card1_camera_vertical_en.png"
    card2_path = mgr.visuals_dir / "card2_buffer_vertical_en.png"
    card3_path = mgr.visuals_dir / "card3_fix_vertical_en.png"

    # Contextual Memes
    meme_cat_bh = ASSETS_DIR / "memes" / "catblackhole.gif"
    meme_bolt = ASSETS_DIR / "memes" / "болт.jpg"
    meme_cat_laugh = ASSETS_DIR / "memes" / "кот-смеётся.png"

    # SFX
    sfx_zona = ASSETS_DIR / "sfx" / "zvuk_zony.mp3"
    sfx_armatura = ASSETS_DIR / "sfx" / "armatura.mp3"
    sfx_win_error = ASSETS_DIR / "sfx" / "windows_error.mp3"
    if not sfx_win_error.exists():
        sfx_win_error = ASSETS_DIR / "sfx" / "what.mp3"

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
            "text": "Players in S.T.A.L.K.E.R. 2 just discovered a bizarre black hole anomaly. The stalker throws a bolt into it, expecting a dangerous vortex of the Zone...",
            "trigger_bgm": False
        },
        {
            "id": "investigation",
            "text": "But in reality, the game's rendering math just completely broke! Let's investigate!",
            "trigger_bgm": True
        },
        {
            "id": "card1",
            "text": "How does a camera work in games? It projects 3D world coordinates onto your flat screen. But this object suffered a division by zero, throwing pixel coordinates to infinity. The GPU assumed the object is off-screen, and stopped rendering that area entirely!",
            "trigger_bgm": False
        },
        {
            "id": "card2",
            "text": "Why does the stalker's hand leave a frozen trail? When swinging, the GPU writes the glove into memory. But when the hand moves away, the void behind never refreshes! The old frame freezes permanently, just like dragging a window in Windows XP!",
            "trigger_bgm": False
        },
        {
            "id": "card3_fix",
            "text": "Developers fix this easily: by forcing the GPU to clear the full screen buffer with background color before every new frame.",
            "trigger_bgm": False
        },
        {
            "id": "outro",
            "text": "You can't fix broken VRAM with a bolt! Drop a like and subscribe to the channel for more game glitch breakdowns!",
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
    print(f"   ✓ Generated {len(scene_blocks_def)} speech blocks.")
    print(f"   ✓ Total voiceover duration: {current_time:.2f}s (video total: {total_duration:.2f}s).")
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
    print("\n[3/6] Generating stylized karaoke subtitles (MarginV=420)...")
    sub_gen = SubtitleGenerator(
        font_name="Arial",
        font_size=46,
        primary_color="&H0000FFFF",
        outline_width=5,
        margin_v=420
    )
    sub_gen.generate_ass_file(all_subtitle_events, ass_path, max_words_per_line=3)

    # 4. Generate Visual Cards using Episode9ENVisualsGenerator (1000x1280)
    print("\n[4/6] Generating vertical graphic diagrams (Top 2/3, 1000x1280)...")
    vis_gen = Episode9ENVisualsGenerator(width=1000, height=1280)
    vis_gen.render_card1_camera(card1_path)
    vis_gen.render_card2_buffer(card2_path)
    vis_gen.render_card3_fix(card3_path)

    # 5. Background Video with Continuous Looping Pure Gameplay
    print("\n[5/6] Preparing background gameplay (9:16 + continuous loop)...")
    prepare_gameplay_background(
        gameplay_mp4=gameplay_src,
        total_duration=total_duration,
        output_bg=temp_bg,
        temp_dir=mgr.temp_dir
    )

    # 6. Composite Layers in FFmpeg (Zero-Overlap Grid + Top 2/3 Diagrams)
    print(f"\n[6/6] Compositing video and audio tracks in FFmpeg (NVENC GPU)...")

    hook_start = block_timings["hook"]["start"]
    hook_end = block_timings["hook"]["end"]

    # Hook split: catblackhole for first 4 sec, bolt meme for the rest of hook
    cat_end = min(4.0, hook_end)
    bolt_start = cat_end
    bolt_end = hook_end

    inv_start = block_timings["investigation"]["start"]
    inv_end = block_timings["investigation"]["end"]

    card1_start = block_timings["card1"]["start"]
    card1_end = block_timings["card1"]["end"]

    card2_start = block_timings["card2"]["start"]
    card2_end = block_timings["card2"]["end"]

    fix_start = block_timings["card3_fix"]["start"]
    fix_end = block_timings["card3_fix"]["end"]

    outro_start = block_timings["outro"]["start"]
    outro_end = block_timings["outro"]["end"]

    # SFX Delays in ms
    sfx_zona_delay_ms = 0
    sfx_armatura_delay_ms = int(max(0, (bolt_start) * 1000))
    sfx_win_delay_ms = int(max(0, (card2_start + 4.0) * 1000))
    bgm_delay_ms = int(max(0, bgm_start_time * 1000))

    # Inputs:
    # 0: temp_bg (video)
    # 1: voice_final (audio)
    # 2: bgm (audio)
    # 3: sfx_zona (audio)
    # 4: sfx_armatura (audio)
    # 5: sfx_win_error (audio)
    # 6: catblackhole.gif (animated gif)
    # 7: bolt.jpg (image)
    # 8: meme_cat_laugh (image)
    # 9: card1_camera_vertical_en.png (image, 1000x1280)
    # 10: card2_buffer_vertical_en.png (image, 1000x1280)
    # 11: card3_fix_vertical_en.png (image, 1000x1280)

    filter_chains = [
        # Hook 1: catblackhole.gif in zone y=880 (first 4s)
        f"[6:v]scale=-1:500,format=rgba,fade=t=in:st={hook_start:.2f}:d=0.2:alpha=1,fade=t=out:st={cat_end-0.2:.2f}:d=0.2:alpha=1[m_cat]",
        f"[0:v][m_cat]overlay=(W-w)/2:880:enable='between(t,{hook_start:.2f},{cat_end:.2f})'[v1]",

        # Hook 2: bolt.jpg in zone y=880 (from 4s to end of hook)
        f"[7:v]scale=-1:500,format=rgba,fade=t=in:st={bolt_start:.2f}:d=0.2:alpha=1,fade=t=out:st={bolt_end-0.2:.2f}:d=0.2:alpha=1[m_bolt]",
        f"[v1][m_bolt]overlay=(W-w)/2:880:enable='between(t,{bolt_start:.2f},{bolt_end:.2f})'[v2]",

        # Investigation: laughing cat meme in zone y=880
        f"[8:v]scale=-1:500,format=rgba,fade=t=in:st={inv_start:.2f}:d=0.25:alpha=1,fade=t=out:st={inv_end-0.25:.2f}:d=0.25:alpha=1[m_inv]",
        f"[v2][m_inv]overlay=(W-w)/2:880:enable='between(t,{inv_start:.2f},{inv_end:.2f})'[v3]",

        # Card 1: Top 2/3 Vertical Camera Diagram (1000x1280 at y=80)
        f"[9:v]scale=1000:-1,format=rgba,fade=t=in:st={card1_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card1_end-0.25:.2f}:d=0.25:alpha=1[v_c1]",
        f"[v3][v_c1]overlay=(W-w)/2:80:enable='between(t,{card1_start:.2f},{card1_end:.2f})'[v4]",

        # Card 2: Top 2/3 Vertical Buffer Diagram (1000x1280 at y=80)
        f"[10:v]scale=1000:-1,format=rgba,fade=t=in:st={card2_start:.2f}:d=0.25:alpha=1,fade=t=out:st={card2_end-0.25:.2f}:d=0.25:alpha=1[v_c2]",
        f"[v4][v_c2]overlay=(W-w)/2:80:enable='between(t,{card2_start:.2f},{card2_end:.2f})'[v5]",

        # Card 3: Top 2/3 Vertical Fix Diagram (1000x1280 at y=80)
        f"[11:v]scale=1000:-1,format=rgba,fade=t=in:st={fix_start:.2f}:d=0.25:alpha=1,fade=t=out:st={fix_end-0.25:.2f}:d=0.25:alpha=1[v_c3]",
        f"[v5][v_c3]overlay=(W-w)/2:80:enable='between(t,{fix_start:.2f},{fix_end:.2f})'[v6]",

        # Outro: laughing cat meme in zone y=880
        f"[8:v]scale=-1:500,format=rgba,fade=t=in:st={outro_start:.2f}:d=0.25:alpha=1,fade=t=out:st={outro_end-0.25:.2f}:d=0.25:alpha=1[m_outro]",
        f"[v6][m_outro]overlay=(W-w)/2:880:enable='between(t,{outro_start:.2f},{outro_end:.2f})'[v7]"
    ]

    # Subtitles overlay
    rel_sub_path = Path(ass_path).resolve().as_posix().replace(":", "\\:")
    filter_chains.append(f"[v7]subtitles=filename='{rel_sub_path}'[v_final]")

    # Audio Mixing: Voice + Ambient + SFX
    filter_chains.append(
        f"[1:a]volume=1.0[a_voice];"
        f"[2:a]adelay={bgm_delay_ms}|{bgm_delay_ms},volume=0.14[a_bgm];"
        f"[3:a]adelay={sfx_zona_delay_ms}|{sfx_zona_delay_ms},volume=0.28[a_zona];"
        f"[4:a]adelay={sfx_armatura_delay_ms}|{sfx_armatura_delay_ms},volume=0.28[a_armatura];"
        f"[5:a]adelay={sfx_win_delay_ms}|{sfx_win_delay_ms},volume=0.30[a_win];"
        f"[a_voice][a_bgm][a_zona][a_armatura][a_win]amix=inputs=5:duration=first:dropout_transition=2[a_final]"
    )

    full_filter = ";".join(filter_chains)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(temp_bg),
        "-i", str(voice_final_path),
        "-i", str(bgm_path),
        "-i", str(sfx_zona),
        "-i", str(sfx_armatura),
        "-i", str(sfx_win_error),
        "-ignore_loop", "0", "-i", str(meme_cat_bh),
        "-loop", "1", "-i", str(meme_bolt),
        "-loop", "1", "-i", str(meme_cat_laugh),
        "-loop", "1", "-i", str(card1_path),
        "-loop", "1", "-i", str(card2_path),
        "-loop", "1", "-i", str(card3_path),
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

    print("   Starting GPU hardware accelerated rendering (NVENC)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError("Video rendering error!")

    print(f"\n🎉 English Short Ready: {final_video}")

    # 7. Metadata Generation
    print("\n[7/7] Generating description and metadata (English)...")
    scenario_info = {
        "episode_id": "9_en",
        "lang": "en",
        "game": "S.T.A.L.K.E.R. 2: Heart of Chornobyl",
        "bug_title": "Secret VRAM Black Hole Anomaly (Screen Space Culling & Hall of Mirrors)",
        "blocks": scene_blocks_def
    }
    MetadataGenerator.generate(
        scenario_data=scenario_info,
        output_dir=mgr.root_dir,
        duration=total_duration
    )

    print("\n" + "=" * 60)
    print("✅ ENGLISH EPISODE COMPLETED SUCCESSFULLY!")
    print(f"📁 Final File: {final_video.resolve()}")
    print("=" * 60)
    return final_video


if __name__ == "__main__":
    build_episode_9_en()
