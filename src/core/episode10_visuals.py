import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT
from src.core.three_renderer import ThreeSceneRenderer

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


SKELETON_RETARGET_3D_SCENE_JS = """
// 3D Scene setup
camera.position.set(9, 3, 11);
camera.lookAt(0, 0.5, 0);

// Custom HUD setup
window._hudBoxWidth = 520;
window._hudLine1Label = 'TARGET RIG:  ';
window._hudLine2Label = 'SPINE PITCH: ';
window._hudLine3Label = 'STATUS:      ';

// Neon Grid Floor
const grid = new THREE.GridHelper(26, 26, 0x0284c7, 0x1e293b);
grid.position.y = -2.5;
scene.add(grid);

// Lights
const ambient = new THREE.AmbientLight(0xffffff, 0.85);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.8);
dirLight.position.set(12, 20, 15);
scene.add(dirLight);

const redLight = new THREE.PointLight(0xef4444, 0, 30);
redLight.position.set(0, 1.5, 0);
scene.add(redLight);

// Helper to create bone cylinder between 2 points
function createBone(p1, p2, radius, colorHex) {
    const dir = new THREE.Vector3().subVectors(p2, p1);
    const len = dir.length();
    const geo = new THREE.CylinderGeometry(radius, radius * 0.85, len, 16);
    geo.translate(0, len / 2, 0);
    geo.rotateX(Math.PI / 2);
    const mat = new THREE.MeshStandardMaterial({
        color: colorHex,
        roughness: 0.25,
        metalness: 0.3,
        emissive: colorHex,
        emissiveIntensity: 0.25
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(p1);
    mesh.lookAt(p2);
    return mesh;
}

// Helper to create joint sphere
function createJoint(pos, radius, colorHex) {
    const geo = new THREE.SphereGeometry(radius, 16, 16);
    const mat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: colorHex,
        emissiveIntensity: 0.7
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    return mesh;
}

// Master Skeleton Container
const skeletonGroup = new THREE.Group();
scene.add(skeletonGroup);

// Materials references
const nominalColor = 0x22c55e; // Green
const errorColor = 0xef4444;   // Red

// Error Shockwave
const shockGeo = new THREE.RingGeometry(0.5, 1.2, 32);
const shockMat = new THREE.MeshBasicMaterial({ color: errorColor, side: THREE.DoubleSide, transparent: true, opacity: 0 });
const shockwave = new THREE.Mesh(shockGeo, shockMat);
shockwave.rotation.x = Math.PI / 2;
shockwave.position.y = -2.48;
scene.add(shockwave);

// Dynamic Point Generator for Skeleton
function getSkeletonPoints(pQuadToHuman) {
    const pelvis = new THREE.Vector3(0, -0.2 - pQuadToHuman * 0.3, -1.2 * (1 - pQuadToHuman));
    
    const spine1 = new THREE.Vector3(
        0,
        pelvis.y + 0.3 * (1 - pQuadToHuman) + 0.9 * pQuadToHuman,
        pelvis.z + 0.8 * (1 - pQuadToHuman)
    );
    const spine2 = new THREE.Vector3(
        0,
        pelvis.y + 0.6 * (1 - pQuadToHuman) + 1.8 * pQuadToHuman,
        pelvis.z + 1.6 * (1 - pQuadToHuman)
    );
    const chest = new THREE.Vector3(
        0,
        pelvis.y + 0.8 * (1 - pQuadToHuman) + 2.6 * pQuadToHuman,
        pelvis.z + 2.3 * (1 - pQuadToHuman)
    );
    const neck = new THREE.Vector3(
        0,
        chest.y + 0.3 * (1 - pQuadToHuman) + 0.6 * pQuadToHuman,
        chest.z + 0.7 * (1 - pQuadToHuman)
    );
    const head = new THREE.Vector3(
        0,
        neck.y + 0.4 * (1 - pQuadToHuman) + 0.7 * pQuadToHuman,
        neck.z + 0.7 * (1 - pQuadToHuman)
    );

    // Hind Legs:
    const lHip = new THREE.Vector3(-0.65, pelvis.y, pelvis.z);
    const rHip = new THREE.Vector3(0.65, pelvis.y, pelvis.z);

    const lKnee = new THREE.Vector3(
        -0.7,
        pelvis.y - 1.2,
        pelvis.z - 0.5 * (1 - pQuadToHuman)
    );
    const rKnee = new THREE.Vector3(
        0.7,
        pelvis.y - 1.2,
        pelvis.z - 0.5 * (1 - pQuadToHuman)
    );

    const lFoot = new THREE.Vector3(-0.65, -2.5, pelvis.z - 0.2 * (1 - pQuadToHuman));
    const rFoot = new THREE.Vector3(0.65, -2.5, pelvis.z - 0.2 * (1 - pQuadToHuman));

    // Front Legs / Arms:
    const lShoulder = new THREE.Vector3(-0.85, chest.y - 0.1, chest.z);
    const rShoulder = new THREE.Vector3(0.85, chest.y - 0.1, chest.z);

    const lElbow = new THREE.Vector3(
        -0.95,
        (chest.y - 1.3) * (1 - pQuadToHuman) + (chest.y - 1.2) * pQuadToHuman,
        (chest.z + 0.2) * (1 - pQuadToHuman) + (chest.z) * pQuadToHuman
    );
    const rElbow = new THREE.Vector3(
        0.95,
        (chest.y - 1.3) * (1 - pQuadToHuman) + (chest.y - 1.2) * pQuadToHuman,
        (chest.z + 0.2) * (1 - pQuadToHuman) + (chest.z) * pQuadToHuman
    );

    const lHand = new THREE.Vector3(
        -0.95,
        (-2.5) * (1 - pQuadToHuman) + (chest.y - 2.4) * pQuadToHuman,
        (chest.z + 0.2) * (1 - pQuadToHuman) + (chest.z) * pQuadToHuman
    );
    const rHand = new THREE.Vector3(
        0.95,
        (-2.5) * (1 - pQuadToHuman) + (chest.y - 2.4) * pQuadToHuman,
        (chest.z + 0.2) * (1 - pQuadToHuman) + (chest.z) * pQuadToHuman
    );

    return {
        pelvis, spine1, spine2, chest, neck, head,
        lHip, rHip, lKnee, rKnee, lFoot, rFoot,
        lShoulder, rShoulder, lElbow, rElbow, lHand, rHand
    };
}

function rebuildSkeleton(pts, colorHex) {
    while (skeletonGroup.children.length > 0) {
        const obj = skeletonGroup.children[0];
        skeletonGroup.remove(obj);
    }

    const radBone = 0.12;
    const radJoint = 0.22;

    const bonePairs = [
        [pts.pelvis, pts.spine1],
        [pts.spine1, pts.spine2],
        [pts.spine2, pts.chest],
        [pts.chest, pts.neck],
        [pts.neck, pts.head],
        [pts.pelvis, pts.lHip],
        [pts.lHip, pts.lKnee],
        [pts.lKnee, pts.lFoot],
        [pts.pelvis, pts.rHip],
        [pts.rHip, pts.rKnee],
        [pts.rKnee, pts.rFoot],
        [pts.chest, pts.lShoulder],
        [pts.lShoulder, pts.lElbow],
        [pts.lElbow, pts.lHand],
        [pts.chest, pts.rShoulder],
        [pts.rShoulder, pts.rElbow],
        [pts.rElbow, pts.rHand]
    ];

    bonePairs.forEach(pair => {
        skeletonGroup.add(createBone(pair[0], pair[1], radBone, colorHex));
    });

    Object.values(pts).forEach(pt => {
        skeletonGroup.add(createJoint(pt, radJoint, colorHex));
    });

    const headGeo = new THREE.BoxGeometry(0.8, 0.7, 1.0);
    const headMat = new THREE.MeshStandardMaterial({
        color: colorHex,
        roughness: 0.3,
        metalness: 0.2,
        emissive: colorHex,
        emissiveIntensity: 0.35
    });
    const headMesh = new THREE.Mesh(headGeo, headMat);
    headMesh.position.copy(pts.head);
    skeletonGroup.add(headMesh);
}

rebuildSkeleton(getSkeletonPoints(0), nominalColor);

updateSceneAtTime = function(t, progress) {
    let pMorph = 0.0;
    let curColor = nominalColor;

    if (progress < 0.35) {
        pMorph = 0.0;
        curColor = nominalColor;
        shockMat.opacity = 0;
        redLight.intensity = 0;

        window._hudVelText = 'QUADRUPED_ANIMAL';
        window._hudVelColor = '#4ade80';
        window._hudLine2Text = '0.0° (ГОРИЗОНТАЛЬ)';
        window._hudLine2Color = '#38bdf8';
        window._hudStatusText = 'OK: 4 ЛАПЫ НА ЗЕМЛЕ';
        window._hudStatusColor = '#4ade80';
    } else if (progress < 0.55) {
        const pSub = (progress - 0.35) / 0.20;
        pMorph = Math.min(1.0, pSub * 1.3);
        curColor = errorColor;

        shockMat.opacity = Math.max(0, 0.9 - pSub * 0.9);
        shockwave.scale.set(1 + pSub * 14, 1 + pSub * 14, 1);
        redLight.intensity = 3.5 * (1 - pSub * 0.5);

        window._hudVelText = 'BIPED_HUMAN_GUARD';
        window._hudVelColor = '#ef4444';
        window._hudLine2Text = '+90.0° (ВЕРТИКАЛЬНО)';
        window._hudLine2Color = '#f87171';
        window._hudStatusText = 'ERROR: РЕТАРГЕТИНГ СБОЙ';
        window._hudStatusColor = '#ef4444';
    } else {
        pMorph = 1.0;
        curColor = errorColor;
        shockMat.opacity = 0;
        redLight.intensity = 0.8;

        window._hudVelText = 'HUMANOID_IDLE';
        window._hudVelColor = '#ef4444';
        window._hudLine2Text = '+90.0° (СТОЙКА СМИРНО)';
        window._hudLine2Color = '#ef4444';
        window._hudStatusText = 'СТОЙКА ОХРАННИКА';
        window._hudStatusColor = '#ef4444';
    }

    const pts = getSkeletonPoints(pMorph);
    rebuildSkeleton(pts, curColor);

    const camAngle = 0.8 + progress * Math.PI * 0.45;
    const camDist = 12.0;
    camera.position.x = camDist * Math.cos(camAngle);
    camera.position.y = 2.2 + Math.sin(progress * Math.PI) * 1.5;
    camera.position.z = camDist * Math.sin(camAngle);
    camera.lookAt(0, 0.5, 0);
};
"""


class Episode10VisualsGenerator:
    """
    Visual assets generator for Episode 10:
    - 3D WebGL Skeleton Retargeting simulation (Three.js)
    - 2D Animation Graph & Blend Tree architecture card (1000x1280)
    - 2D Code fix diff card (1000x1280)
    """
    def __init__(self, width: int = 1000, height: int = 1280, browser_path: str = CHROME_PATH):
        self.width = width
        self.height = height
        self.browser_path = browser_path
        self.three_renderer = ThreeSceneRenderer(width=width, height=height, fps=30, browser_path=browser_path)

    def render_3d_skeleton_video(self, output_mp4: Path, duration: float = 5.0, output_gif: Path = None) -> Path:
        return self.three_renderer.render_3d_video(
            scene_js=SKELETON_RETARGET_3D_SCENE_JS,
            output_mp4=output_mp4,
            duration=duration,
            output_gif=output_gif,
            header_title="3D СИМУЛЯЦИЯ: СБОЙ РЕТАРГЕТИНГА",
            header_badge="HAVOK SKELETON RIG",
            footer_left="Анимация гуманоида на риге животного",
            footer_right="Retarget Glitch"
        )

    def render_html_to_image(self, html_content: str, output_image_path: Path) -> Path:
        output_image_path = Path(output_image_path).resolve()
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    body {{
        width: {self.width}px;
        height: {self.height}px;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""

        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as f_temp:
            temp_html_path = f_temp.name
            f_temp.write(full_html)

        try:
            cmd = [
                self.browser_path,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--default-background-color=00000000",
                f"--window-size={self.width},{self.height}",
                f"--screenshot={str(output_image_path)}",
                f"file:///{Path(temp_html_path).resolve().as_posix()}"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print("Browser stderr:", res.stderr)
        finally:
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)

        return output_image_path

    def render_card2_tree(self, output_path: Path) -> Path:
        """
        Card 2: Animation Blend Tree & Retargeting Conflict
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 42px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #232730; padding-bottom: 24px;">
                <div>
                    <h2 style="font-size: 34px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">АНИМАЦИОННОЕ ДЕРЕВО (BLEND TREE)</h2>
                    <p style="font-size: 22px; color: #94a3b8; margin-top: 6px;">Как движок путает скелеты персонажей</p>
                </div>
                <div style="background: #0f172a; border: 2px solid #0284c7; padding: 10px 20px; border-radius: 12px; font-size: 20px; font-weight: 700; color: #38bdf8; font-family: monospace;">
                    ANIM CONTROLLER
                </div>
            </div>

            <!-- Step 1: Normal Quadruped State -->
            <div style="background: #1c1f26; border-left: 8px solid #22c55e; border-radius: 20px; padding: 26px 30px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 26px; font-weight: 800; color: #4ade80;">1. Исходный меш: Четвероногое (Quadruped)</span>
                    <span style="font-size: 20px; background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 4px 14px; border-radius: 8px; font-family: monospace;">NORMAL</span>
                </div>
                <div style="font-size: 23px; color: #cbd5e1; line-height: 1.4;">
                    • <b>Скелет:</b> 4 опорные точки, горизонтальный хребет (Spine)<br>
                    • <b>Ожидание:</b> Патрулирование на четырех лапах (Walk/Run)
                </div>
            </div>

            <!-- Down Arrow Connector with Retarget Glitch -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 24px; margin: 4px 0;">
                <div style="height: 3px; background: #334155; flex: 1;"></div>
                <div style="background: #450a0a; border: 2px solid #ef4444; padding: 14px 28px; border-radius: 16px; text-align: center;">
                    <div style="font-size: 28px; font-weight: 900; color: #f87171;">⇓ СБОЙ РЕТАРГЕТИНГА ⇓</div>
                    <div style="font-size: 21px; color: #fca5a5; font-family: monospace; margin-top: 4px;">ApplyState(HUMAN_GUARD_IDLE) ➔ Spine +90°</div>
                </div>
                <div style="height: 3px; background: #334155; flex: 1;"></div>
            </div>

            <!-- Step 2: Humanoid Pose Forced on Animal -->
            <div style="background: #1c1f26; border-left: 8px solid #ef4444; border-radius: 20px; padding: 26px 30px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 26px; font-weight: 800; color: #f87171;">2. Реакция движка: Стойка человека</span>
                    <span style="font-size: 20px; background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 4px 14px; border-radius: 8px; font-family: monospace;">COLLAPSE</span>
                </div>
                <div style="font-size: 23px; color: #cbd5e1; line-height: 1.4;">
                    • <b>Хребет:</b> Развернут вертикально вверх (поза человека)<br>
                    • <b>Передние лапы:</b> Прижаты вдоль тела, как руки охранника<br>
                    • <b>Итог:</b> Животное стоит на двух ногах и неподвижно смотрит в туман
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #0d0e11; border: 2px solid #232730; border-radius: 20px; padding: 20px 28px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 23px; color: #94a3b8;">
                    Итог: <b style=\"color: #ffffff;\">Движок назначил риг человека вместо зверя</b>
                </div>
                <div style="background: rgba(239, 68, 68, 0.2); border: 1.5px solid #ef4444; color: #f87171; padding: 8px 18px; border-radius: 10px; font-size: 20px; font-family: monospace; font-weight: 700;">
                    Rig Mismatch
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card3_fix(self, output_path: Path) -> Path:
        """
        Card 3: Code Fix Diff Card
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 42px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #232730; padding-bottom: 24px;">
                <div>
                    <h2 style="font-size: 34px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">ИСПРАВЛЕНИЕ В ДВИЖКЕ (FIX)</h2>
                    <p style="font-size: 22px; color: #94a3b8; margin-top: 6px;">Строгая проверка типа скелета при спавне</p>
                </div>
                <div style="background: #0f172a; border: 2px solid #22c55e; padding: 10px 20px; border-radius: 12px; font-size: 20px; font-weight: 700; color: #4ade80; font-family: monospace;">
                    PATCH APPLIED
                </div>
            </div>

            <!-- Code Diff Box -->
            <div style="background: #0a0c10; border: 2.5px solid #1e293b; border-radius: 20px; padding: 28px 32px; font-family: Consolas, Monaco, monospace; font-size: 23px; line-height: 1.7;">
                <div style="color: #64748b; margin-bottom: 16px; font-size: 20px;">// AnimStateMachine.cpp: BindSkeletonState()</div>

                <!-- Wrong Line -->
                <div style="background: rgba(239, 68, 68, 0.15); border-left: 6px solid #ef4444; padding: 12px 16px; margin-bottom: 16px; border-radius: 0 10px 10px 0; color: #fca5a5;">
                    <span style="color: #ef4444; font-weight: 900; margin-right: 12px;">[-]</span>anim-&gt;ApplyPose(DEFAULT_HUMAN_GUARD);<br>
                    <span style="color: #94a3b8; font-size: 20px; margin-left: 32px;">// 🦝 Меш встает на 2 лапы по стойке смирно!</span>
                </div>

                <!-- Fixed Lines -->
                <div style="background: rgba(34, 197, 94, 0.15); border-left: 6px solid #22c55e; padding: 12px 16px; border-radius: 0 10px 10px 0; color: #86efac;">
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>if (entity.IsQuadruped()) {{<br>
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>&nbsp;&nbsp;&nbsp;&nbsp;anim-&gt;ApplyPose(QUADRUPED_IDLE);<br>
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>}} // 🐾 Хребет горизонтален, все 4 лапы на земле!
                </div>
            </div>

            <!-- Explanation Callout -->
            <div style="background: #1c1f26; border-left: 8px solid #38bdf8; border-radius: 18px; padding: 22px 28px;">
                <div style="font-size: 24px; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">💡 Почему это лечит баг?</div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.4;">
                    Движок больше не назначает позу человека сущностям без гуманоидного скелета. Животные остаются на четырех лапах и не пугают игроков в тумане.
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #0d0e11; border: 2px solid #232730; border-radius: 20px; padding: 20px 28px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 23px; color: #94a3b8;">
                    Результат: <b style="color: #ffffff;">Никаких прямоходящих зверей-охранников</b>
                </div>
                <div style="background: rgba(34, 197, 94, 0.2); border: 1.5px solid #22c55e; color: #4ade80; padding: 8px 18px; border-radius: 10px; font-size: 20px; font-family: monospace; font-weight: 700;">
                    100% Fixed
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)
