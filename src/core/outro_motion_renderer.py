"""
Outro Motion UI Renderer for GameBug / Onter's inn Shorts Engine.
Renders a 4.5s 30 FPS Green Screen (#00FF00) motion animation of the universal subscribe banner:
- Assets from assets/icons/ (YouTube Shorts, TikTok, 3D Cursor)
- Pure Green Screen background (#00FF00) for seamless FFmpeg Chroma Keying (colorkey=0x00FF00)
- 3D cursor movement, button click press pop, dynamic Emerald color transition ("ВЫ ПОДПИСАНЫ! ✓")
- Precise sound effect sync with click.mp3 trimmed at exact click transient (t=1.48s)
- 4.5 second duration for comfortable viewing and loop integration
"""

import base64
import json
import os
import shutil
import subprocess
import sys
import time
import threading
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
    """
    Trims silence and the leading 'Noice' voice from assets/sfx/click.mp3
    so that only the sharp mouse click sound at t=1.48s is extracted.
    """
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    input_mp3 = BASE_DIR / "assets" / "sfx" / "click.mp3"

    # Click peak starts at 1.48s in click.mp3
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", "1.48",
        "-i", str(input_mp3),
        "-t", "0.35",
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
        background: #00ff00; /* Pure Green Screen for Chroma Keying */
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
    canvas {{
        width: 1000px;
        height: 340px;
        display: block;
        background: #00ff00;
    }}
</style>
</head>
<body>
<canvas id="c" width="1000" height="340"></canvas>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

const imgYT = new Image();
const imgTT = new Image();
const imgCursor = new Image();

imgYT.src = "{yt_b64}";
imgTT.src = "{tt_b64}";
imgCursor.src = "{cursor_b64}";

function drawRoundedRect(ctx, x, y, w, h, r, fill, stroke, strokeWidth) {{
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
    if (fill) {{
        ctx.fillStyle = fill;
        ctx.fill();
    }}
    if (stroke) {{
        ctx.strokeStyle = stroke;
        ctx.lineWidth = strokeWidth || 1;
        ctx.stroke();
    }}
}}

function renderFrame(t) {{
    // 1. Clear with Green Screen background (#00FF00)
    ctx.fillStyle = '#00ff00';
    ctx.fillRect(0, 0, 1000, 340);

    ctx.save();

    // Entrance animation (0.0s - 0.4s)
    let cardScale = 1.0;
    let cardAlpha = 1.0;
    if (t < 0.4) {{
        const p = t / 0.4;
        cardScale = 0.8 + 0.2 * Math.sin(p * Math.PI / 2);
        cardAlpha = p;
    }}

    ctx.globalAlpha = cardAlpha;
    ctx.translate(500, 170);
    ctx.scale(cardScale, cardScale);
    ctx.translate(-500, -170);

    // Main Dark Box Container (#141720)
    drawRoundedRect(ctx, 10, 10, 980, 320, 24, '#141720', '#2e3444', 2.5);
    // Top highlight line
    drawRoundedRect(ctx, 10, 10, 980, 12, 6, '#2e3440', null);

    // 2. Logos & Branding
    // YouTube Shorts Icon Badge
    ctx.save();
    drawRoundedRect(ctx, 40, 42, 54, 54, 14, '#000000', null);
    ctx.clip();
    ctx.drawImage(imgYT, 40, 42, 54, 54);
    ctx.restore();

    // TikTok Icon Badge
    ctx.save();
    drawRoundedRect(ctx, 106, 42, 54, 54, 14, '#000000', null);
    ctx.clip();
    ctx.drawImage(imgTT, 106, 42, 54, 54);
    ctx.restore();

    // Vertical Divider
    ctx.fillStyle = '#2e3444';
    ctx.fillRect(178, 46, 2, 46);

    // Channel Title Text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 32px Arial, sans-serif';
    ctx.fillText("Onter's inn", 196, 75);

    // SHORTS Tag
    const nameWidth = ctx.measureText("Onter's inn").width;
    const tagX = 196 + nameWidth + 14;
    drawRoundedRect(ctx, tagX, 48, 86, 28, 7, '#e11d48', null);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 14px Arial, sans-serif';
    ctx.fillText("SHORTS", tagX + 10, 67);

    // Subtitle
    ctx.fillStyle = '#94a3b8';
    ctx.font = '500 18px Arial, sans-serif';
    ctx.fillText("Свежие разборы багов каждый день!", 196, 102);

    // 3. Subscribe Button
    const isClicked = t >= 1.5;
    const isPressing = t >= 1.4 && t < 1.5;

    let btnY = 135;
    let btnH = 150;
    let btnFill = isClicked ? '#059669' : '#e11d48';
    let btnStroke = isClicked ? '#10b981' : '#f43f5e';
    let btnText = isClicked ? "ВЫ ПОДПИСАНЫ! ✓" : "ПОДПИСАТЬСЯ НА КАНАЛ";

    ctx.save();
    if (isPressing) {{
        ctx.translate(500, 210);
        ctx.scale(0.97, 0.97);
        ctx.translate(-500, -210);
    }}

    drawRoundedRect(ctx, 40, btnY, 920, btnH, 20, btnFill, btnStroke, 3);

    // Button Text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 32px Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(btnText, 500, btnY + btnH / 2);

    // Click Ripple Animation (1.5s - 1.8s)
    if (t >= 1.5 && t < 1.8) {{
        const rp = (t - 1.5) / 0.3;
        const radius = rp * 140;
        const alpha = 1.0 - rp;
        ctx.beginPath();
        ctx.arc(680, 210, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 255, 255, ${{alpha}})`;
        ctx.lineWidth = 4;
        ctx.stroke();
    }}
    ctx.restore();

    // 4. Animated 3D Mouse Cursor Movement
    const startX = 820;
    const startY = 280;
    const targetX = 640;
    const targetY = 180;

    let curX = startX;
    let curY = startY;

    if (t >= 0.4 && t < 1.4) {{
        const p = (t - 0.4) / 1.0;
        const ease = 1 - Math.pow(1 - p, 3);
        curX = startX + (targetX - startX) * ease;
        curY = startY + (targetY - startY) * ease;
    }} else if (t >= 1.4) {{
        curX = targetX;
        curY = targetY;
    }}

    let cursorScale = 1.0;
    if (isPressing) {{
        cursorScale = 0.82;
    }}

    ctx.save();
    ctx.translate(curX, curY);
    ctx.scale(cursorScale, cursorScale);
    ctx.drawImage(imgCursor, 0, 0, 72, 72);
    ctx.restore();

    ctx.restore();
}}

const urlParams = new URLSearchParams(window.location.search);
const tVal = parseFloat(urlParams.get('t') || '0');
renderFrame(tVal);
</script>
</body>
</html>"""
    return html


def render_single_frame(html_path: Path, frame_idx: int, t_sec: float, frames_dir: Path) -> Path:
    out_png = frames_dir / f"frame_{frame_idx:04d}.png"
    target_url = f"file:///{html_path.resolve().as_posix()}?t={t_sec:.4f}"

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--default-background-color=00ff00ff",
        f"--window-size=1000,340",
        f"--screenshot={out_png.resolve().as_posix()}",
        target_url
    ]
    subprocess.run(cmd, capture_output=True)
    return out_png


def render_outro_motion_video(output_mp4: Path, duration_sec: float = 4.5, fps: int = 30) -> Path:
    output_mp4 = Path(output_mp4)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    frames_dir = TEMP_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    # 1. Prepare trimmed click audio (extract sharp click sound at t=1.48s)
    trimmed_audio = TEMP_DIR / "click_trimmed.wav"
    prepare_trimmed_click_sound(trimmed_audio)

    # 2. Write HTML file
    html_file = TEMP_DIR / "index.html"
    html_file.write_text(build_outro_html_template(), encoding="utf-8")

    total_frames = int(duration_sec * fps)
    print(f"[RENDER] Рендеринг {total_frames} кадров Green Screen Outro Motion UI ({duration_sec}s, 30 FPS)...")

    # Parallel render using 4 Chrome worker threads
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

    # 3. Composite Frames + Click SFX at t=1.50s via FFmpeg NVENC
    print("[FFMPEG] Сборка 4.5s MP4 видеоклипа с точным щелчком click.mp3 на t=1.5s...")
    cmd_ffmpeg = [
        FFMPEG_PATH, "-y",
        "-r", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-itsoffset", "1.50",
        "-i", str(trimmed_audio),
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_mp4)
    ]
    subprocess.run(cmd_ffmpeg, capture_output=True, check=True)

    # Clean up temp
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"[SUCCESS] Итоговый 4.5s Green Screen Outro Motion видеоклип создан: {output_mp4}")
    return output_mp4


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    out_path = BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4"
    render_outro_motion_video(out_path, duration_sec=4.5)
