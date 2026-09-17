import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    FFMPEG_PATH, VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ, FPS
)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class ThreeSceneRenderer:
    """
    High-performance deterministic 3D scene renderer for Three.js & WebGL.
    Renders 3D debug visualizations, mesh deformations, physics collision volumes,
    and frustum projections into high-quality MP4 video or PNG diagrams.
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

    def _build_html_wrapper(self, scene_js: str, transparent: bool = False) -> str:
        bg_color = "transparent" if transparent else "#0a0f1d"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace, sans-serif; }}
    body {{
        width: {self.width}px;
        height: {self.height}px;
        background: {bg_color};
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    #canvas-container {{
        width: {self.width}px;
        height: {self.height}px;
        position: relative;
    }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
<div id="canvas-container"></div>
<script>
const WIDTH = {self.width};
const HEIGHT = {self.height};
const FPS = {self.fps};

// Setup Base Scene, Camera, Renderer
const scene = new THREE.Scene();
{'scene.background = null;' if transparent else 'scene.background = new THREE.Color(0x0a0f1d);'}

const camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({{
    antialias: true,
    alpha: {'true' if transparent else 'false'},
    preserveDrawingBuffer: true
}});
renderer.setSize(WIDTH, HEIGHT);
renderer.setPixelRatio(1);
document.getElementById('canvas-container').appendChild(renderer.domElement);

// Global Hook for time-based rendering
let updateSceneAtTime = function(t, frameIdx) {{}};

{scene_js}

// Deterministic Time Render Trigger
window.renderFrameAtTime = function(t, frameIdx) {{
    updateSceneAtTime(t, frameIdx);
    renderer.render(scene, camera);
}};
</script>
</body>
</html>"""

    def render_static_frame(self, scene_js: str, output_image: Path, t: float = 0.0) -> Path:
        """
        Renders a single high-resolution 3D frame at time t.
        """
        output_image = Path(output_image).resolve()
        output_image.parent.mkdir(parents=True, exist_ok=True)

        full_html = self._build_html_wrapper(scene_js)
        # Append instant render call
        full_html = full_html.replace(
            "</body>",
            f"<script>window.renderFrameAtTime({t}, 0);</script></body>"
        )

        temp_dir = tempfile.mkdtemp()
        temp_html = Path(temp_dir) / "index.html"
        temp_html.write_text(full_html, encoding="utf-8")

        try:
            cmd = [
                self.browser_path,
                "--headless=new",
                f"--user-data-dir={temp_dir}",
                "--enable-webgl",
                "--use-gl=angle",
                "--hide-scrollbars",
                f"--window-size={self.width},{self.height}",
                f"--screenshot={str(output_image)}",
                f"file:///{temp_html.resolve().as_posix()}"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 and res.stderr:
                print("Three.js Chrome stderr:", res.stderr)
        finally:
            pass

        return output_image

    def render_video_clip(
        self,
        scene_js: str,
        output_mp4: Path,
        duration: float = 4.0,
        transparent: bool = False
    ) -> Path:
        """
        Renders a deterministic 30/60 FPS 3D animation clip into MP4 using NVIDIA NVENC GPU.
        """
        output_mp4 = Path(output_mp4).resolve()
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(duration * self.fps)
        temp_dir = Path(tempfile.mkdtemp())
        frames_dir = temp_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        # Write HTML template
        full_html = self._build_html_wrapper(scene_js, transparent=transparent)
        temp_html = temp_dir / "index.html"
        temp_html.write_text(full_html, encoding="utf-8")

        print(f"🎬 Рендеринг 3D WebGL сцены ({duration:.1f} сек, {total_frames} кадров)...")

        # Extract frames in batch via Headless Chrome with virtual time
        # We generate a self-contained multi-frame exporter or dump frames
        batch_exporter_html = full_html.replace(
            "</body>",
            f"""<script>
            async function exportAllFrames() {{
                const total = {total_frames};
                for (let f = 0; f < total; f++) {{
                    const t = f / {self.fps};
                    window.renderFrameAtTime(t, f);
                    // Frame ready for capture
                }}
            }}
            </script></body>"""
        )
        temp_html.write_text(batch_exporter_html, encoding="utf-8")

        # For highest reliability and cross-version compatibility on Windows,
        # we capture frames deterministically
        for f in range(total_frames):
            t = f / self.fps
            frame_file = frames_dir / f"frame_{f:04d}.png"
            
            frame_html_content = full_html.replace(
                "</body>",
                f"<script>window.renderFrameAtTime({t}, {f});</script></body>"
            )
            frame_html_path = temp_dir / f"render_{f}.html"
            frame_html_path.write_text(frame_html_content, encoding="utf-8")

            cmd = [
                self.browser_path,
                "--headless=new",
                f"--user-data-dir={temp_dir / f'prof_{f}'}",
                "--enable-webgl",
                "--use-gl=angle",
                "--hide-scrollbars",
                f"--window-size={self.width},{self.height}",
                f"--screenshot={str(frame_file)}",
                f"file:///{frame_html_path.resolve().as_posix()}"
            ]
            subprocess.run(cmd, capture_output=True)
            if frame_html_path.exists():
                try: os.remove(frame_html_path)
                except Exception: pass

            if f % 15 == 0 or f == total_frames - 1:
                pct = int(((f + 1) / total_frames) * 100)
                print(f"   ✓ 3D Кадры: {pct}% ({f + 1}/{total_frames})...")

        # Encode with FFmpeg NVENC
        ffmpeg_cmd = [
            FFMPEG_PATH, "-y",
            "-framerate", str(self.fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-c:v", VIDEO_CODEC,
            "-preset", VIDEO_PRESET,
            "-cq", VIDEO_CQ,
            "-pix_fmt", "yuv420p",
            str(output_mp4)
        ]
        res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("FFmpeg error:", res.stderr)
            raise RuntimeError("Failed to encode 3D video with FFmpeg")

        print(f"✨ [УСПЕХ] 3D видеоролик успешно отрендерен: {output_mp4}")
        return output_mp4


# Built-in Procedural 3D Scene Presets for Game Bugs
PRESET_CAMERA_FRUSTUM_PROJECTION = """
// Preset: 3D Camera Frustum & Projection NaN Bug
camera.fov = 55;
camera.position.set(0, 2, 22);
camera.lookAt(0, 0, 0);
camera.updateProjectionMatrix();

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.5);
dirLight.position.set(10, 20, 15);
scene.add(dirLight);

// 3D Grid Floor
const grid = new THREE.GridHelper(30, 30, 0x0284c7, 0x1e293b);
grid.position.y = -3.5;
scene.add(grid);

// 3D Camera Model (Mesh representation)
const camGroup = new THREE.Group();
const camBody = new THREE.Mesh(
    new THREE.BoxGeometry(2.2, 1.5, 2.5),
    new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.2, metalness: 0.8 })
);
const camLens = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.7, 1.2, 32),
    new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.1, metalness: 0.9 })
);
camLens.rotation.x = Math.PI / 2;
camLens.position.z = 1.4;
camGroup.add(camBody);
camGroup.add(camLens);
camGroup.position.set(-4.5, 0.5, 0);
scene.add(camGroup);

// 3D Frustum Wireframe Pyramid
const frustumGeo = new THREE.ConeGeometry(4.5, 8, 4, 1, true);
const frustumMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.85 });
const frustumMesh = new THREE.Mesh(frustumGeo, frustumMat);
frustumMesh.rotation.x = -Math.PI / 2;
frustumMesh.rotation.y = Math.PI / 4;
frustumMesh.position.set(-4.5, 0.5, 4.5);
scene.add(frustumMesh);

// 3D Target Bug Object
const targetGeo = new THREE.SphereGeometry(1.3, 32, 32);
const targetMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3, emissive: 0x7f1d1d });
const targetMesh = new THREE.Mesh(targetGeo, targetMat);
targetMesh.position.set(4.5, 0.5, 0);
scene.add(targetMesh);

// Broken Projection Vector Ray
const rayMat = new THREE.LineDashedMaterial({ color: 0xef4444, dashSize: 0.5, gapSize: 0.3, linewidth: 4 });
const points = [new THREE.Vector3(-4.5, 0.5, 0), new THREE.Vector3(4.5, 0.5, 0)];
const rayGeo = new THREE.BufferGeometry().setFromPoints(points);
const rayLine = new THREE.Line(rayGeo, rayMat);
rayLine.computeLineDistances();
scene.add(rayLine);


updateSceneAtTime = function(t, frameIdx) {
    camGroup.rotation.y = Math.sin(t * 1.5) * 0.2;
    targetMesh.position.y = 0.5 + Math.sin(t * 3.0) * 0.8;
    frustumMesh.rotation.z = Math.sin(t * 1.5) * 0.2;
};

"""

PRESET_COLLISION_PENETRATION = """
// Preset: 3D Capsule Pinned Against Static Wall
camera.position.set(6, 4, 8);
camera.lookAt(0, 0, 0);

const ambient = new THREE.AmbientLight(0xffffff, 0.7);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.4);
dirLight.position.set(8, 15, 10);
scene.add(dirLight);

// Floor
const grid = new THREE.GridHelper(20, 20, 0x38bdf8, 0x1e293b);
grid.position.y = -2;
scene.add(grid);

// Static Wall (Hazard Stripped)
const wall = new THREE.Mesh(
    new THREE.BoxGeometry(1, 6, 8),
    new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.6 })
);
wall.position.set(3, 1, 0);
scene.add(wall);

// NPC Capsule Collider
const capGeo = new THREE.CylinderGeometry(0.8, 0.8, 2.5, 24);
const capMat = new THREE.MeshStandardMaterial({ color: 0x22c55e, roughness: 0.3, transparent: true, opacity: 0.85 });
const capMesh = new THREE.Mesh(capGeo, capMat);
capMesh.position.set(1.5, 0.25, 0);
scene.add(capMesh);

// Kinematic Door
const doorGeo = new THREE.BoxGeometry(0.4, 5, 4);
const doorMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.2 });
const door = new THREE.Mesh(doorGeo, doorMat);
door.position.set(-1.5, 0.5, 0);
scene.add(door);

// Overlap Warning Ring
const ringGeo = new THREE.RingGeometry(0.4, 0.8, 32);
const ringMat = new THREE.MeshBasicMaterial({ color: 0xef4444, side: THREE.DoubleSide });
const ring = new THREE.Mesh(ringGeo, ringMat);
ring.position.set(2.4, 0.5, 0);
ring.rotation.y = Math.PI / 2;
scene.add(ring);

updateSceneAtTime = function(t, frameIdx) {
    const push = Math.min(1.2, t * 0.8);
    door.position.x = -1.5 + push;
    ring.scale.set(1 + Math.sin(t * 8) * 0.2, 1 + Math.sin(t * 8) * 0.2, 1);
};
"""
