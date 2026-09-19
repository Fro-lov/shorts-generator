"""
Outro Motion UI Renderer for GameBug / Onter's inn Shorts Engine.
Renders a high-end 30 FPS HTML/CSS motion animation of the universal subscribe banner using:
- Real icons from assets/icons/ (YouTube Shorts, TikTok, 3D Cursor)
- 3D cursor movement, button click press pop, dynamic Emerald color transition ("ВЫ ПОДПИСАНЫ! ✓")
- Precise sound effect sync with click.mp3 (offset 2.25s silence)
- Robust batch screenshot rendering via Headless Chrome
"""

import base64
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import FFMPEG_PATH, VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ, FPS

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

TEMP_DIR = BASE_DIR / "output" / "temp" / "outro_motion_job"


def get_base64_data_uri(file_path: Path, mime_type: str) -> str:
    raw = Path(file_path).read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def prepare_trimmed_click_sound(output_wav: Path) -> Path:
    """Trims leading 2.25s silence from assets/sfx/click.mp3 so the click starts at t=0s."""
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    input_mp3 = BASE_DIR / "assets" / "sfx" / "click.mp3"

    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", "2.25",
        "-i", str(input_mp3),
        "-t", "0.6",
        "-c:a", "pcm_s16le",
        str(output_wav)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_wav


def build_outro_html_template() -> str:
    yt_b64 = get_base64_data_uri(BASE_DIR / "assets" / "icons" / "Youtube_shorts_icon.svg.webp", "image/webp")
    tt_b64 = get_base64_data_uri(BASE_DIR / "assets" / "icons" / "tik-tok-glitch-icon-social-media-tik-tok-icon-vinnitsa-ukraine-february-22-02-2023_250246-536.avif", "image/avif")
    cursor_b64 = get_base64_data_uri(BASE_DIR / "assets" / "icons" / "pngtree-arrow-mouse-cursor-3d-cursor-png-image_10172240.png", "image/png")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Montserrat, Arial, sans-serif;
    }}
    body {{
        width: 1000px;
        height: 340px;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
    .card-container {{
        width: 980px;
        height: 320px;
        background: #141720;
        border: 2.5px solid #2e3444;
        border-radius: 24px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(225, 29, 72, 0.15);
        padding: 24px 30px;
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        overflow: hidden;
        transform-origin: center center;
    }}

    .top-row {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    .icon-badge {{
        width: 54px;
        height: 54px;
        border-radius: 14px;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }}
    .divider {{
        width: 2px;
        height: 40px;
        background: #2e3444;
    }}
    .channel-info {{
        display: flex;
        flex-direction: column;
    }}
    .title-row {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .channel-name {{
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
    }}
    .shorts-tag {{
        background: #e11d48;
        color: #ffffff;
        font-size: 14px;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .subtitle {{
        font-size: 18px;
        color: #94a3b8;
        font-weight: 500;
        margin-top: 2px;
    }}

    .sub-btn {{
        width: 100%;
        height: 125px;
        background: linear-gradient(135deg, #e11d48 0%, #be123c 100%);
        border: 2.5px solid #f43f5e;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.5px;
        box-shadow: 0 10px 25px rgba(225, 29, 72, 0.4);
        position: relative;
        transform-origin: center center;
    }}

    .sub-btn.subscribed {{
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        border-color: #10b981;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
    }}

    .cursor-img {{
        position: absolute;
        width: 72px;
        height: 72px;
        object-fit: contain;
        pointer-events: none;
        z-index: 10;
        filter: drop-shadow(0 8px 16px rgba(0,0,0,0.6));
        transform-origin: top left;
    }}

    .ripple {{
        position: absolute;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        border: 4px solid #ffffff;
        transform: scale(0);
        opacity: 0;
        pointer-events: none;
    }}
</style>
</head>
<body>

<div class="card-container" id="card">
    <div class="top-row">
        <img class="icon-badge" src="{yt_b64}" alt="YouTube Shorts">
        <img class="icon-badge" src="{tt_b64}" alt="TikTok">
        <div class="divider"></div>
        <div class="channel-info">
            <div class="title-row">
                <span class="channel-name">Onter's inn</span>
                <span class="shorts-tag">SHORTS</span>
            </div>
            <span class="subtitle">Свежие разборы багов каждый день!</span>
        </div>
    </div>

    <div class="sub-btn" id="btn">
        <span id="btnText">ПОДПИСАТЬСЯ НА КАНАЛ</span>
        <div class="ripple" id="ripple"></div>
    </div>

    <img class="cursor-img" id="cursor" src="{cursor_b64}" alt="Cursor">
</div>

<script>
function setTime(t) {{
    const card = document.getElementById('card');
    const btn = document.getElementById('btn');
    const btnText = document.getElementById('btnText');
    const cursor = document.getElementById('cursor');
    const ripple = document.getElementById('ripple');

    // 1. Entrance Pop (0.0s - 0.4s)
    if (t < 0.4) {{
        const progress = t / 0.4;
        const scale = 0.8 + 0.2 * Math.sin(progress * Math.PI / 2);
        card.style.transform = `scale(${{scale}})`;
        card.style.opacity = progress;
    }} else {{
        card.style.transform = 'scale(1)';
        card.style.opacity = 1;
    }}

    // 2. Cursor movement (0.4s - 1.4s)
    const startX = 760;
    const startY = 270;
    const targetX = 620;
    const targetY = 175;

    let curX = startX;
    let curY = startY;

    if (t < 0.4) {{
        curX = startX;
        curY = startY;
    }} else if (t < 1.4) {{
        const p = (t - 0.4) / 1.0;
        const ease = 1 - Math.pow(1 - p, 3);
        curX = startX + (targetX - startX) * ease;
        curY = startY + (targetY - startY) * ease;
    }} else {{
        curX = targetX;
        curY = targetY;
    }}

    // 3. Click Press & Reaction (1.4s - 1.5s press, 1.5s+ subscribed)
    const isClicked = t >= 1.5;
    const isPressing = t >= 1.4 && t < 1.5;

    if (isPressing) {{
        cursor.style.transform = 'scale(0.82)';
        btn.style.transform = 'scale(0.96)';
    }} else {{
        cursor.style.transform = 'scale(1)';
        btn.style.transform = 'scale(1)';
    }}

    if (isClicked) {{
        btn.classList.add('subscribed');
        btnText.innerText = 'ВЫ ПОДПИСАНЫ! ✓';

        // Ripple expansion (1.5s - 1.8s)
        if (t < 1.8) {{
            const rp = (t - 1.5) / 0.3;
            ripple.style.left = `${{targetX - 30}}px`;
            ripple.style.top = `${{targetY - 120}}px`;
            ripple.style.transform = `scale(${{rp * 1.8}})`;
            ripple.style.opacity = `${{1.0 - rp}}`;
        }} else {{
            ripple.style.opacity = 0;
        }}
    }} else {{
        btn.classList.remove('subscribed');
        btnText.innerText = 'ПОДПИСАТЬСЯ НА КАНАЛ';
        ripple.style.opacity = 0;
    }}

    cursor.style.left = `${{curX}}px`;
    cursor.style.top = `${{curY}}px`;
}}

const urlParams = new URLSearchParams(window.location.search);
const tVal = parseFloat(urlParams.get('t') || '0');
setTime(tVal);
</script>

</body>
</html>"""
    return html


def render_single_frame(html_path: Path, frame_idx: int, t_sec: float, frames_dir: Path) -> Path:
    out_png = frames_dir / f"frame_{frame_idx:04d}.png"
    target_url = f"file:///{html_path.resolve().as_posix()}?t={t_sec:.4f}"
    profile_dir = frames_dir / f"p_{frame_idx}"

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--default-background-color=00000000",
        f"--window-size=1000,340",
        f"--screenshot={out_png.resolve().as_posix()}",
        target_url
    ]
    subprocess.run(cmd, capture_output=True)
    if profile_dir.exists():
        shutil.rmtree(profile_dir, ignore_errors=True)
    return out_png


def render_outro_motion_video(output_mp4: Path, duration_sec: float = 3.5, fps: int = 30) -> Path:
    output_mp4 = Path(output_mp4)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    frames_dir = TEMP_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    # 1. Prepare trimmed click audio
    trimmed_audio = TEMP_DIR / "click_trimmed.wav"
    prepare_trimmed_click_sound(trimmed_audio)

    # 2. Write HTML file
    html_file = TEMP_DIR / "index.html"
    html_file.write_text(build_outro_html_template(), encoding="utf-8")

    total_frames = int(duration_sec * fps)
    print(f"[RENDER] Рендеринг {total_frames} кадров Outro Motion UI (30 FPS)...")

    # Parallel render using 4 Chrome worker threads for ultra-fast performance
    tasks = []
    for f_idx in range(total_frames):
        t_sec = f_idx / fps
        tasks.append((html_file, f_idx, t_sec, frames_dir))

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(render_single_frame, *task) for task in tasks]
        for idx, fut in enumerate(futures):
            fut.result()
            if (idx + 1) % 30 == 0 or (idx + 1) == total_frames:
                pct = int(((idx + 1) / total_frames) * 100)
                print(f"   ✓ Снято кадров: {pct}% ({idx+1}/{total_frames})...")

    t1 = time.time()
    print(f"   ✓ Все {total_frames} кадров сняты за {t1-t0:.2f} сек!")

    # 3. Composite Frames + Click SFX at t=1.5s via FFmpeg NVENC
    print("[FFMPEG] Сборка MP4 видеоклипа с синхронизированным кликом click.mp3 на t=1.5s...")
    cmd_ffmpeg = [
        FFMPEG_PATH, "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-itsoffset", "1.50",
        "-i", str(trimmed_audio),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-pix_fmt", "yuva420p" if VIDEO_CODEC == "libx264" else "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_mp4)
    ]
    subprocess.run(cmd_ffmpeg, capture_output=True, check=True)

    # Clean up temp
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"[SUCCESS] Итоговый Outro Motion видеоклип создан: {output_mp4}")
    return output_mp4


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    out_path = BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4"
    render_outro_motion_video(out_path)
