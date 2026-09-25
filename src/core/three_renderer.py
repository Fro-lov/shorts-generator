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
from typing import Optional, Dict, Any, Union

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
        pass

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            frame_idx = data['frame']
            img_b64 = data['image']
            
            img_bytes = base64.b64decode(img_b64.split(',')[1] if ',' in img_b64 else img_b64)
            frame_path = self.server.frames_dir / f"frame_{frame_idx:04d}.png"
            frame_path.write_bytes(img_bytes)
            
            self.server.received_frames += 1
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
    Supports solid background rendering (Dark Graphite #14161a) or transparent rendering.
    """
    def __init__(
        self,
        width: int = 1000,
        height: int = 600,
        fps: int = 30,
        browser_path: str = CHROME_PATH
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.browser_path = browser_path

    def render_transparent_gif(
        self,
        scene_js: str,
        output_gif: Path,
        duration: float = 3.0,
        hud_title: str = "3D DEBUGGER",
        hud_pos: str = "POS: [0,0,0]",
        hud_force: str = "FORCE: 0 N",
        bg_color: Optional[str] = "#14161a"  # Solid dark graphite background by default
    ) -> Path:
        """
        Renders 3D scene GIF with solid dark graphite background or transparent background.
        """
        output_gif = Path(output_gif).resolve()
        output_gif.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration * self.fps)
        work_dir = TEMP_ROOT / f"job_gif_{int(time.time()*1000)}"
        frames_dir = work_dir / "frames"
        prof_dir = work_dir / "chrome_prof"
        frames_dir.mkdir(parents=True, exist_ok=True)
        prof_dir.mkdir(parents=True, exist_ok=True)

        port = 8794
        server = FrameReceiverServer(('127.0.0.1', port), FrameHTTPHandler, frames_dir, total_frames)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        is_solid = bg_color is not None and bg_color != "transparent"
        bg_css = bg_color if is_solid else "transparent"
        three_clear_color = bg_color.replace("#", "0x") if is_solid else "0x000000"
        alpha_val = "false" if is_solid else "true"
        clear_alpha = "1" if is_solid else "0"

        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: monospace; }}
    body {{
        width: {self.width}px;
        height: {self.height}px;
        background: {bg_css};
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    #canvas-container {{
        width: {self.width}px;
        height: {self.height}px;
        background: {bg_css};
        border-radius: 16px;
        overflow: hidden;
        position: relative;
    }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
<div id="canvas-container"></div>

<script>
const TOTAL_W = {self.width};
const TOTAL_H = {self.height};

const scene = new THREE.Scene();
{f'scene.background = new THREE.Color({three_clear_color});' if is_solid else ''}

const camera = new THREE.PerspectiveCamera(45, TOTAL_W / TOTAL_H, 0.1, 1000);
const webglRenderer = new THREE.WebGLRenderer({{ antialias: true, alpha: {alpha_val}, preserveDrawingBuffer: true }});
webglRenderer.setClearColor({three_clear_color}, {clear_alpha});
webglRenderer.setSize(TOTAL_W, TOTAL_H);
document.getElementById('canvas-container').appendChild(webglRenderer.domElement);

let updateSceneAtTime = function(t, progress) {{}};

{scene_js}

async function renderAllFrames() {{
    const total = {total_frames};
    const fps = {self.fps};
    const duration = {duration};

    for (let f = 0; f < total; f++) {{
        const t = f / fps;
        const progress = t / duration;
        
        updateSceneAtTime(t, progress);
        webglRenderer.render(scene, camera);

        const dataUrl = webglRenderer.domElement.toDataURL('image/png');
        await fetch('http://127.0.0.1:{port}/frame', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ frame: f, image: dataUrl }})
        }});
    }}
}}

window.addEventListener('load', () => {{
    setTimeout(renderAllFrames, 300);
}});
</script>
</body>
</html>"""

        html_file = work_dir / "index.html"
        html_file.write_text(html_content, encoding="utf-8")

        chrome_cmd = [
            self.browser_path,
            "--headless=new",
            f"--user-data-dir={prof_dir.resolve()}",
            "--enable-webgl",
            "--use-gl=angle",
            "--hide-scrollbars",
            f"--window-size={self.width},{self.height}",
            f"file:///{html_file.resolve().as_posix()}"
        ]

        chrome_proc = subprocess.Popen(chrome_cmd)
        finished = server.done_event.wait(timeout=duration * 10 + 20)
        server.shutdown()
        chrome_proc.terminate()
        try: chrome_proc.wait(timeout=2)
        except Exception: pass

        input_pattern = str(frames_dir.resolve() / "frame_%04d.png")

        if is_solid:
            # High quality solid GIF encoding
            gif_cmd = [
                FFMPEG_PATH, "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-filter_complex", "[0:v] split [a][b];[a] palettegen=stats_mode=full [p];[b][p] paletteuse=dither=sierra2_4a",
                str(output_gif)
            ]
        else:
            # Palettegen for transparent GIF
            gif_cmd = [
                FFMPEG_PATH, "-y",
                "-framerate", str(self.fps),
                "-i", input_pattern,
                "-filter_complex", "[0:v] split [a][b];[a] palettegen=reserve_transparent=on:transparency_color=00000000 [p];[b][p] paletteuse",
                str(output_gif)
            ]
        subprocess.run(gif_cmd, capture_output=True)

        # Cleanup
        try:
            for f in frames_dir.glob("*.png"): f.unlink()
            if html_file.exists(): html_file.unlink()
            subprocess.run(["cmd.exe", "/c", f'rmdir /s /q "{prof_dir.resolve()}"'], capture_output=True)
            subprocess.run(["cmd.exe", "/c", f'rmdir /s /q "{work_dir.resolve()}"'], capture_output=True)
        except Exception: pass

        return output_gif
