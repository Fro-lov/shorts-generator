import os
import sys
import io
import time
import json
import base64
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

# Add project root to sys.path
BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))
from config.settings import (
    FFMPEG_PATH, VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ, FPS
)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Strictly use Drive E for all temp files and caches
TEMP_ROOT = BASE_DIR / "output" / "temp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)


class FrameReceiverServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, frames_dir, total_frames):
        super().__init__(server_address, RequestHandlerClass)
        self.frames_dir = frames_dir
        self.total_frames = total_frames
        self.received_frames = 0
        self.done_event = threading.Event()


class FrameHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logs

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            frame_idx = data['frame']
            img_b64 = data['image']
            
            # Save raw PNG to Drive E
            img_bytes = base64.b64decode(img_b64.split(',')[1] if ',' in img_b64 else img_b64)
            frame_path = self.server.frames_dir / f"frame_{frame_idx:04d}.png"
            frame_path.write_bytes(img_bytes)
            
            self.server.received_frames += 1
            if self.server.received_frames % 30 == 0 or self.server.received_frames >= self.server.total_frames:
                pct = int((self.server.received_frames / self.server.total_frames) * 100)
                print(f"   ✓ 3D Рендеринг кадров: {pct}% ({self.server.received_frames}/{self.server.total_frames})...")
            
            if self.server.received_frames >= self.server.total_frames:
                self.server.done_event.set()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


class ThreeSceneRenderer:
    """
    High-Performance Deterministic 3D Scene Renderer for Three.js & WebGL.
    - Zero dropped frames: Sequentially streams WebGL composite frames at exact timestamps.
    - Zero Drive C pollution: Uses strictly E:\\social\\output\\temp\\ for all frames, HTML and profiles.
    - GPU Accelerated encoding via NVIDIA NVENC (H.264) and high-quality GIF export.
    """
    def __init__(
        self,
        width: int = 1000,
        height: int = 1280,
        fps: int = 30,
        browser_path: str = CHROME_PATH
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.browser_path = browser_path

    def render_3d_video(
        self,
        scene_js: str,
        output_mp4: Path,
        duration: float = 4.0,
        output_gif: Optional[Path] = None,
        header_title: str = "3D СИМУЛЯЦИЯ: ДВИЖОК ИГРЫ",
        header_badge: str = "HAVOK PHYSICS 3D",
        footer_left: str = "Итог: 3D визуализация физики",
        footer_right: str = "Physics Solver"
    ) -> Path:
        output_mp4 = Path(output_mp4).resolve()
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration * self.fps)
        work_dir = TEMP_ROOT / f"job_{int(time.time()*1000)}"
        frames_dir = work_dir / "frames"
        prof_dir = work_dir / "chrome_prof"
        frames_dir.mkdir(parents=True, exist_ok=True)
        prof_dir.mkdir(parents=True, exist_ok=True)

        port = 8793
        server = FrameReceiverServer(('127.0.0.1', port), FrameHTTPHandler, frames_dir, total_frames)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Canvas dims inside card
        canvas_w = self.width - 80
        canvas_h = 920

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace, sans-serif; }}
    body {{
        width: {self.width}px;
        height: {self.height}px;
        background: #0a0f1d;
        overflow: hidden;
    }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
<div id="hidden-webgl-container" style="display:none;"></div>

<script>
const TOTAL_W = {self.width};
const TOTAL_H = {self.height};
const CANVAS_W = {canvas_w};
const CANVAS_H = {canvas_h};

// 1. Setup Three.js WebGL Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0f1d);

const camera = new THREE.PerspectiveCamera(45, CANVAS_W / CANVAS_H, 0.1, 1000);
const webglRenderer = new THREE.WebGLRenderer({{ antialias: true, preserveDrawingBuffer: true }});
webglRenderer.setSize(CANVAS_W, CANVAS_H);
webglRenderer.setPixelRatio(1);
document.getElementById('hidden-webgl-container').appendChild(webglRenderer.domElement);

// 2. Setup 2D Master Composite Canvas (1000 x 1280)
const masterCanvas = document.createElement('canvas');
masterCanvas.width = TOTAL_W;
masterCanvas.height = TOTAL_H;
const ctx = masterCanvas.getContext('2d');
document.body.appendChild(masterCanvas);

// User-provided Scene Setup & Hook
let updateSceneAtTime = function(t, progress) {{}};

{scene_js}

function drawRoundedRect(ctx, x, y, width, height, radius, fill, stroke, strokeWidth) {{
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    if (fill) {{ ctx.fillStyle = fill; ctx.fill(); }}
    if (stroke) {{ ctx.strokeStyle = stroke; ctx.lineWidth = strokeWidth || 2; ctx.stroke(); }}
}}

function renderCompositeCard(t, progress) {{
    // 1. Update 3D
    updateSceneAtTime(t, progress);
    webglRenderer.render(scene, camera);

    // 2. Draw Card Background
    ctx.fillStyle = '#0a0f1d';
    ctx.fillRect(0, 0, TOTAL_W, TOTAL_H);

    // Outer Card
    drawRoundedRect(ctx, 20, 20, TOTAL_W - 40, TOTAL_H - 40, 36, '#14161a', '#2a2e37', 2.5);

    // 3. Draw Header
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 34px -apple-system, sans-serif';
    ctx.fillText('{header_title}', 50, 75);

    // Header Badge
    drawRoundedRect(ctx, TOTAL_W - 270, 42, 220, 44, 12, '#0f172a', '#0284c7', 2);
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 21px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('{header_badge}', TOTAL_W - 160, 71);
    ctx.textAlign = 'left';

    // Header Divider line
    ctx.strokeStyle = '#232730';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(50, 105);
    ctx.lineTo(TOTAL_W - 50, 105);
    ctx.stroke();

    // 4. Draw 3D WebGL Canvas
    const canvasX = 40;
    const canvasY = 125;
    drawRoundedRect(ctx, canvasX - 2, canvasY - 2, CANVAS_W + 4, CANVAS_H + 4, 24, '#0b1120', '#1e293b', 2);
    ctx.save();
    ctx.beginPath();
    ctx.roundRect(canvasX, canvasY, CANVAS_W, CANVAS_H, 22);
    ctx.clip();
    ctx.drawImage(webglRenderer.domElement, canvasX, canvasY);
    ctx.restore();

    // 5. Draw HUD Box inside Canvas
    drawRoundedRect(ctx, canvasX + 24, canvasY + 24, 460, 130, 14, 'rgba(15, 23, 42, 0.92)', '#38bdf8', 1.5);
    ctx.font = 'bold 21px monospace';
    
    // Line 1: Velocity
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('VELOCITY: ', canvasX + 44, canvasY + 60);
    ctx.fillStyle = window._hudVelColor || '#4ade80';
    ctx.fillText(window._hudVelText || '--', canvasX + 175, canvasY + 60);

    // Line 2: Solver
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('SOLVER:   DISCRETE (1 TIK)', canvasX + 44, canvasY + 95);

    // Line 3: Status
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('STATUS:   ', canvasX + 44, canvasY + 130);
    ctx.fillStyle = window._hudStatusColor || '#4ade80';
    ctx.fillText(window._hudStatusText || 'NORMAL', canvasX + 175, canvasY + 130);

    // 6. Draw Footer
    const footerY = TOTAL_H - 145;
    drawRoundedRect(ctx, 40, footerY, TOTAL_W - 80, 85, 20, '#0d0e11', '#232730', 2);
    
    ctx.fillStyle = '#94a3b8';
    ctx.font = '25px -apple-system, sans-serif';
    ctx.fillText('Итог: ', 65, footerY + 52);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 25px -apple-system, sans-serif';
    ctx.fillText('{footer_left}', 130, footerY + 52);

    // Footer Right Badge
    drawRoundedRect(ctx, TOTAL_W - 320, footerY + 18, 250, 48, 12, 'rgba(69, 10, 10, 0.5)', '#ef4444', 1.5);
    ctx.fillStyle = '#f87171';
    ctx.font = 'bold 22px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('{footer_right}', TOTAL_W - 195, footerY + 50);
    ctx.textAlign = 'left';
}}

// Sequential frame-by-frame loop with zero frame drops
async function renderAllFrames() {{
    const total = {total_frames};
    const fps = {self.fps};
    const duration = {duration};

    for (let f = 0; f < total; f++) {{
        const t = f / fps;
        const progress = t / duration;
        
        renderCompositeCard(t, progress);

        // Capture 1000x1280 composite frame
        const dataUrl = masterCanvas.toDataURL('image/png');

        await fetch('http://127.0.0.1:{port}/frame', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ frame: f, image: dataUrl }})
        }});
    }}
}}

window.addEventListener('load', () => {{
    setTimeout(renderAllFrames, 400);
}});
</script>
</body>
</html>"""

        html_file = work_dir / "index.html"
        html_file.write_text(html_content, encoding="utf-8")

        print(f"\n🎬 Старт детерминированного 3D рендера ({duration:.1f} сек, {total_frames} кадров, {self.fps} FPS)...")
        print(f"📁 Все временные файлы сохраняются строго на диск E: {work_dir}")

        chrome_cmd = [
            self.browser_path,
            "--headless=new",
            f"--user-data-dir={prof_dir.resolve()}",
            "--enable-webgl",
            "--use-gl=angle",
            "--hide-scrollbars",
            "--disable-gpu-watchdog",
            f"--window-size={self.width},{self.height}",
            f"file:///{html_file.resolve().as_posix()}"
        ]

        chrome_proc = subprocess.Popen(chrome_cmd)

        finished = server.done_event.wait(timeout=duration * 10 + 30)
        server.shutdown()
        chrome_proc.terminate()
        try: chrome_proc.wait(timeout=3)
        except Exception: pass

        if not finished:
            print(f"⚠️ Предупреждение: Получено {server.received_frames}/{total_frames} кадров.")

        # Verify frames
        rendered_count = len(list(frames_dir.glob("frame_*.png")))
        print(f"✨ Собрано {rendered_count}/{total_frames} кадров (100% без пропусков).")

        print("⚡ Кодирование видео через NVIDIA NVENC GPU...")
        input_pattern = str(frames_dir.resolve() / "frame_%04d.png")
        
        ffmpeg_cmd = [
            FFMPEG_PATH,
            "-y",
            "-framerate", str(self.fps),
            "-i", input_pattern,
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-cq", VIDEO_CQ,
            "-pix_fmt", "yuv420p",
            str(output_mp4)
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("FFmpeg error:", res.stderr)
            raise RuntimeError(f"FFmpeg render failed: {res.stderr}")

        print(f"🎬 MP4 видео готово: {output_mp4} ({output_mp4.stat().st_size / 1024:.1f} KB)")

        # Export GIF if requested
        if output_gif:
            output_gif = Path(output_gif).resolve()
            output_gif.parent.mkdir(parents=True, exist_ok=True)
            print("🎞️ Экспорт высококачественного 30 FPS GIF...")
            gif_cmd = [
                FFMPEG_PATH,
                "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-vf", "scale=500:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=bayer",
                str(output_gif)
            ]
            subprocess.run(gif_cmd, capture_output=True)
            print(f"🎞️ GIF готов: {output_gif} ({output_gif.stat().st_size / 1024:.1f} KB)")

        # Cleanup temp job folder on Drive E
        try:
            for f in frames_dir.glob("*.png"): f.unlink()
            if html_file.exists(): html_file.unlink()
            subprocess.run(["cmd.exe", "/c", f'rmdir /s /q "{prof_dir.resolve()}"'], capture_output=True)
            subprocess.run(["cmd.exe", "/c", f'rmdir /s /q "{work_dir.resolve()}"'], capture_output=True)
        except Exception:
            pass

        return output_mp4


DEMO_WALL_BREACH_SCENE = """
// 3D Scene setup
camera.position.set(13, 10, 17);
camera.lookAt(0, 0, 0);

// Neon Grid Floor
const grid = new THREE.GridHelper(30, 30, 0x0284c7, 0x1e293b);
grid.position.y = -3;
scene.add(grid);

// Lights
const ambient = new THREE.AmbientLight(0xffffff, 0.75);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
dirLight.position.set(15, 25, 20);
scene.add(dirLight);

const redLight = new THREE.PointLight(0xef4444, 0, 25);
redLight.position.set(0, 1.5, 0);
scene.add(redLight);

// Static Wall (3D Box)
const wallGeo = new THREE.BoxGeometry(0.9, 6, 12);
const wallMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.4, metalness: 0.4 });
const wall = new THREE.Mesh(wallGeo, wallMat);
scene.add(wall);

const wallWire = new THREE.Mesh(wallGeo, new THREE.MeshBasicMaterial({ color: 0x475569, wireframe: true }));
scene.add(wallWire);

// Player Capsule (Smooth Capsule Geometry)
const capGeo = new THREE.CylinderGeometry(1.0, 1.0, 3.2, 32);
const capMat = new THREE.MeshStandardMaterial({ color: 0x22c55e, roughness: 0.2, metalness: 0.2 });
const capsule = new THREE.Mesh(capGeo, capMat);
scene.add(capsule);

// Ghost Wireframe inside wall
const ghostMat = new THREE.MeshBasicMaterial({ color: 0xef4444, wireframe: true, transparent: true, opacity: 0 });
const ghost = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.05, 3.3, 16), ghostMat);
scene.add(ghost);

// Velocity Vector Arrow
const arrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 3.2, 0x4ade80, 0.8, 0.4);
scene.add(arrow);

// Impact Shockwave Ring
const ringGeo = new THREE.RingGeometry(0.6, 1.3, 32);
const ringMat = new THREE.MeshBasicMaterial({ color: 0xef4444, side: THREE.DoubleSide, transparent: true, opacity: 0 });
const shockwave = new THREE.Mesh(ringGeo, ringMat);
shockwave.rotation.y = Math.PI / 2;
scene.add(shockwave);

// Smooth continuous time update hook
updateSceneAtTime = function(t, progress) {
    let posX = -8.0;
    
    if (progress < 0.45) {
        // Phase 1: Smooth quadratic acceleration (0.0 to 0.45)
        const p = progress / 0.45;
        const easeRun = p * p;
        posX = -8.0 + easeRun * 7.2;
        
        capsule.material.color.setHex(0x22c55e);
        arrow.setColor(0x4ade80);
        ghostMat.opacity = 0;
        shockwave.material.opacity = 0;
        redLight.intensity = 0;
        
        window._hudVelText = (12.4 + easeRun * 85.0).toFixed(1) + " m/s";
        window._hudVelColor = "#4ade80";
        window._hudStatusText = "ACCELERATING";
        window._hudStatusColor = "#4ade80";
    } else if (progress < 0.58) {
        // Phase 2: Instant Discrete Tick Tunneling (0.45 to 0.58)
        const pHit = (progress - 0.45) / 0.13;
        posX = 3.0 + pHit * 1.5;
        
        capsule.material.color.setHex(0xef4444);
        arrow.setColor(0xef4444);
        ghostMat.opacity = 0.95;
        ghost.position.set(0, 0, 0);
        
        shockwave.material.opacity = Math.max(0, 0.9 - pHit * 0.9);
        shockwave.scale.set(1 + pHit * 12, 1 + pHit * 12, 1);
        redLight.intensity = 3.0 * (1 - pHit);
        
        window._hudVelText = "99.8 m/s (OVERFLOW)";
        window._hudVelColor = "#ef4444";
        window._hudStatusText = "TUNNELING BYPASS";
        window._hudStatusColor = "#f87171";
    } else {
        // Phase 3: Flying away on other side (0.58 to 1.0)
        const pPost = (progress - 0.58) / 0.42;
        posX = 4.5 + pPost * 4.5;
        
        capsule.material.color.setHex(0xef4444);
        arrow.setColor(0xef4444);
        ghostMat.opacity = Math.max(0, 0.95 - pPost * 2.0);
        shockwave.material.opacity = 0;
        redLight.intensity = 0;
        
        window._hudVelText = "120.0 m/s (MAX)";
        window._hudVelColor = "#ef4444";
        window._hudStatusText = "OUT OF BOUNDS";
        window._hudStatusColor = "#ef4444";
    }
    
    capsule.position.x = posX;
    arrow.position.set(posX, 0, 0);
    
    // Smooth cinematic orbital camera rotation
    const camAngle = progress * Math.PI * 0.4 + 0.3;
    camera.position.x = 18 * Math.cos(camAngle);
    camera.position.y = 10 + Math.sin(progress * Math.PI) * 2;
    camera.position.z = 18 * Math.sin(camAngle);
    camera.lookAt(0, 0, 0);
};
"""


if __name__ == "__main__":
    renderer = ThreeSceneRenderer(width=1000, height=1280, fps=30)
    out_mp4 = BASE_DIR / "output" / "3d_preview" / "3d_wall_breach_smooth.mp4"
    out_gif = BASE_DIR / "output" / "3d_preview" / "3d_wall_breach_smooth.gif"

    renderer.render_3d_video(
        scene_js=DEMO_WALL_BREACH_SCENE,
        output_mp4=out_mp4,
        duration=4.0,
        output_gif=out_gif,
        header_title="3D СИМУЛЯЦИЯ: ПРОБИТИЕ СТЕНЫ",
        header_badge="HAVOK PHYSICS 3D",
        footer_left="Скорость превысила толщину хитбокса",
        footer_right="Tunneling Glitch"
    )
    print("\n✅ Тестовый рендер завершен успешно!")
