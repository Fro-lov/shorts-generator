import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

from src.core.smart_card_generator import SmartCardGenerator
from src.core.three_renderer import ThreeSceneRenderer


class Episode23VisualsGenerator:
    """
    Visuals Generator for Episode #23 (Watch Dogs NPC Interaction Target Collision Bug).
    Generates exact 3D schematic animated scene with solid dark graphite background #14161a and cards:
    - Target Ring (зеленый круг цели)
    - Vector Arrow pointing to ring center
    - Small Red Obstacle Square resting on part of ring edge (не перекрывает вид)
    - Orange Cylinder (персонаж) moving in multi-directional steps (в разные стороны)
    - Distance Indicator HUD (DIST: 1.82m [REQ: <0.10m])
    - Visual Legend (Легенда)
    """
    def __init__(self, width: int = 1000):
        self.width = width
        self.smart_cards = SmartCardGenerator(width=width)
        self.three_renderer = ThreeSceneRenderer(width=1000, height=600, fps=30)

    def generate_3d_cutscene_card(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        three_gif = output_path.parent / "three_navmesh_bug.gif"
        
        # 3D Scene Three.js script matching exact user specs with solid dark background
        three_js = """
camera.position.set(7, 6, 8);
camera.lookAt(0, 0.4, -0.5);

// Dark Grid
const grid = new THREE.GridHelper(14, 14, 0x38bdf8, 0x1e293b);
grid.position.y = 0;
scene.add(grid);

const ambient = new THREE.AmbientLight(0xffffff, 0.95);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.5);
dirLight.position.set(6, 12, 6);
scene.add(dirLight);

// 1. Зеленый круг назначения (Target Ring)
const targetRingGeo = new THREE.RingGeometry(0.7, 0.95, 32);
const targetRingMat = new THREE.MeshBasicMaterial({ color: 0x22c55e, side: THREE.DoubleSide });
const targetRing = new THREE.Mesh(targetRingGeo, targetRingMat);
targetRing.rotation.x = Math.PI / 2;
targetRing.position.set(0, 0.03, -2.0);
scene.add(targetRing);

// Точка в центре круга
const centerDot = new THREE.Mesh(
    new THREE.CylinderGeometry(0.12, 0.12, 0.05, 16),
    new THREE.MeshBasicMaterial({ color: 0x4ade80 })
);
centerDot.position.set(0, 0.04, -2.0);
scene.add(centerDot);

// 2. Стрелка направления (Arrow pointing to target ring center)
const arrowDir = new THREE.Vector3(0, 0, -1);
const arrowOrigin = new THREE.Vector3(0, 0.4, 1.2);
const arrowHelper = new THREE.ArrowHelper(arrowDir, arrowOrigin, 2.6, 0xfba919, 0.5, 0.35);
scene.add(arrowHelper);

// 3. Небольшой красный квадрат на части края круга (Small red obstacle square resting on part of ring edge)
const obstacle = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, 0.4, 1.2),
    new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.2 })
);
obstacle.position.set(0, 0.2, -1.3);
scene.add(obstacle);

// 4. Персонаж (Оранжевый цилиндр / Orange Cylinder)
const player = new THREE.Mesh(
    new THREE.CylinderGeometry(0.4, 0.4, 1.6, 32),
    new THREE.MeshStandardMaterial({ color: 0xfba919, metalness: 0.2, roughness: 0.4 })
);
player.position.set(0, 0.8, 1.2);
scene.add(player);

// Линия дистанции
const lineMat = new THREE.LineDashedMaterial({ color: 0x38bdf8, dashSize: 0.15, gapSize: 0.1 });
const lineGeo = new THREE.BufferGeometry().setFromPoints([player.position, centerDot.position]);
const distLine = new THREE.Line(lineGeo, lineMat);
scene.add(distLine);

// Анимация: персонаж двигается В РАЗНЫЕ СТОРОНЫ (multi-directional search)
updateSceneAtTime = function(t, progress) {
    const stepX = Math.sin(progress * Math.PI * 8) * 0.35;
    const stepZ = Math.cos(progress * Math.PI * 6) * 0.25;
    
    player.position.x = stepX;
    player.position.z = 1.0 + stepZ;
    
    const pts = [player.position.clone(), centerDot.position.clone()];
    distLine.geometry.setFromPoints(pts);

    const currDist = player.position.distanceTo(centerDot.position);
    window._hudPos = "DIST: " + currDist.toFixed(2) + "m [REQ: <0.10m]";
    window._hudForce = "STATUS: PATHSEARCHING (BLOCKED)";
};
"""
        try:
            self.three_renderer.render_transparent_gif(
                scene_js=three_js,
                output_gif=three_gif,
                duration=3.0,
                hud_title="NAVMESH TARGET DEBUGGER",
                hud_pos="DIST: 1.82m [REQ: <0.10m]",
                hud_force="OBSTACLE COLLISION DETECTED",
                bg_color="#14161a"  # Solid dark graphite background returned
            )
            print(f"[+] Rendered 3D GIF with dark graphite background: {three_gif}")
        except Exception as e:
            print(f"[*] Note: ThreeRenderer GIF error: {e}")

        items = [
            "1. ТРИГГЕР: Клик на кассу задает зеленый круг-цель",
            "2. ВЕКТОР: Стрелка указывает в центр круга цели",
            "3. ПРЕПЯТСТВИЕ: Красный квадрат лежит на крае круга",
            "4. РЕЗУЛЬТАТ: Цилиндр ищет путь в разные стороны (dist > 0.1m)"
        ]
        return self.smart_cards.generate_diagram_card(
            output_path=output_path,
            title="3D СХЕМА: ЗАСТРЕВАНИЕ В КАТСЦЕНЕ",
            badge="3D DEBUGGER",
            step_title="Легенда: Зеленый круг = Цель | Красный квадрат = Блок",
            items=items,
            accent_color="#ef4444",
            footer_note="ЛЕГЕНДА: 🟢 Зеленый = Цель | 🔴 Красный = Блок | 🟠 Цилиндр = Персонаж"
        )

    def generate_diagram_2(self, output_path: Path) -> Path:
        """Diagram 2: State Machine Logic Error Diagram."""
        items = [
            "1. Вход в состояние CutsceneState без таймаута",
            "2. Движок ожидает события OnTargetReached()",
            "3. Коллизия авто блокирует вектор перемещения",
            "4. UI магазина заблокирован в открытом виде"
        ]
        return self.smart_cards.generate_diagram_card(
            output_path=output_path,
            title="СХЕМА 2: СБОЙ СТЕЙТ-МАШИНЫ",
            badge="ENGINE LOGIC",
            step_title="Зацикливание состояния CutsceneWalkState",
            items=items,
            accent_color="#fb923c",
            footer_note="Фикс: Добавление таймаута 3 сек и Raycast пути"
        )

    def generate_code_card(self, output_path: Path) -> Path:
        """Code Card: CutsceneTargetController.cpp Bug & Fix."""
        wrong = [
            "// BUG: Infinite loop if target position is blocked",
            "void UpdateCutsceneWalk(float dt) {",
            "    Vector3 dir = (targetPos - playerPos).Normalized();",
            "    playerController.Move(dir * speed * dt);",
            "}"
        ]
        fixed = [
            "// FIX: Path verification & safety timeout limit",
            "void UpdateCutsceneWalk(float dt) {",
            "    if (IsPathBlocked(targetPos) || walkTimer > 3.0f) {",
            "        CancelInteraction(); return;",
            "    }",
            "    playerController.MoveTo(targetPos, dt);",
            "}"
        ]
        return self.smart_cards.generate_os_code_card(
            output_path=output_path,
            title="КОД ФИКСА (CutsceneController.cpp)",
            file_tab="CutsceneTargetController.cpp",
            wrong_code=wrong,
            fixed_code=fixed,
            takeaway="Таймаут 3.0с + проверка коллизии в Raycast"
        )


def generate_episode23_visuals():
    out_dir = BASE_DIR / "output" / "23" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    gen = Episode23VisualsGenerator()
    c1 = gen.generate_3d_cutscene_card(out_dir / "card1_3d_navmesh.png")
    c2 = gen.generate_diagram_2(out_dir / "card2_state_machine.png")
    c3 = gen.generate_code_card(out_dir / "card3_code_fix.png")

    print(f"✅ Episode 23 visual cards updated in: {out_dir}")
    return [c1, c2, c3]


if __name__ == "__main__":
    generate_episode23_visuals()
