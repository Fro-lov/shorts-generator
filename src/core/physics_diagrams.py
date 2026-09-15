import io
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


class PhysicsDiagramRenderer:
    def __init__(self, width: int = 1080, height: int = 600):
        self.width = width
        self.height = height
        
        # Load fonts
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
            self.font_regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
            self.font_mono = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
            self.font_mono_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 22)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_mono = ImageFont.load_default()
            self.font_mono_bold = ImageFont.load_default()

    def create_canvas(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (self.width, self.height), "#0a0f1d")
        draw = ImageDraw.Draw(img)
        self._draw_grid(draw)
        return img, draw

    def _draw_grid(self, draw: ImageDraw.ImageDraw, step: int = 40):
        # Draw CAD blueprint coordinate grid
        for x in range(0, self.width, step):
            color = "#17233f" if x % (step * 4) != 0 else "#1e3258"
            draw.line([(x, 0), (x, self.height)], fill=color, width=1)
        for y in range(0, self.height, step):
            color = "#17233f" if y % (step * 4) != 0 else "#1e3258"
            draw.line([(0, y), (self.width, y)], fill=color, width=1)

        # Outer border
        draw.rectangle([0, 0, self.width - 1, self.height - 1], outline="#38bdf8", width=3)

    def draw_badge(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color: str = "#1e293b", text_color: str = "#38bdf8", border_color: str = "#0ea5e9"):
        bbox = draw.textbbox((x + 12, y + 6), text, font=self.font_mono_bold)
        draw.rounded_rectangle([x, y, bbox[2] + 12, bbox[3] + 6], radius=6, fill=bg_color, outline=border_color, width=2)
        draw.text((x + 12, y + 6), text, fill=text_color, font=self.font_mono_bold)

    def draw_hazard_stripes(self, draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, stripe_w: int = 16):
        w = x2 - x1
        h = y2 - y1
        draw.rectangle([x1, y1, x2, y2], fill="#18181b", outline="#eab308", width=2)
        
        # Clip diagonal yellow stripes
        for sx in range(-h, w + h, stripe_w * 2):
            pts = [
                (max(x1, min(x2, x1 + sx)), y1),
                (max(x1, min(x2, x1 + sx + stripe_w)), y1),
                (max(x1, min(x2, x1 + sx + stripe_w - h)), y2),
                (max(x1, min(x2, x1 + sx - h)), y2)
            ]
            if pts[0][0] < x2 and pts[2][0] > x1:
                draw.polygon([(max(x1, min(x2, px)), max(y1, min(y2, py))) for px, py in pts], fill="#eab308")

    def draw_vector(
        self, draw: ImageDraw.ImageDraw, start: tuple[float, float], end: tuple[float, float],
        color: str = "#38bdf8", width: int = 4, label: str = None, label_side: str = "right"
    ):
        x1, y1 = start
        x2, y2 = end
        draw.line([start, end], fill=color, width=width)

        # Arrow head
        dx = x2 - x1
        dy = y2 - y1
        angle = math.atan2(dy, dx)
        head_len = 16
        head_angle = math.pi / 6

        left_x = x2 - head_len * math.cos(angle - head_angle)
        left_y = y2 - head_len * math.sin(angle - head_angle)
        right_x = x2 - head_len * math.cos(angle + head_angle)
        right_y = y2 - head_len * math.sin(angle + head_angle)

        draw.polygon([(x2, y2), (left_x, left_y), (right_x, right_y)], fill=color)

        if label:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            nx = -math.sin(angle) * 18
            ny = math.cos(angle) * 18
            if label_side == "left":
                nx, ny = -nx, -ny
            draw.text((mx + nx, my + ny), label, fill=color, font=self.font_mono_bold, anchor="mm")

    def draw_contact_point(self, draw: ImageDraw.ImageDraw, x: float, y: float, label: str = "P", color: str = "#ef4444"):
        # Pulse circles
        draw.ellipse([x - 14, y - 14, x + 14, y + 14], outline=color, width=2)
        draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=color)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill="#ffffff")
        draw.text((x + 18, y - 10), label, fill=color, font=self.font_mono_bold)

    def draw_capsule_collider(
        self, draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, height: float,
        color: str = "#22c55e", fill: str = None, dashed: bool = False
    ):
        top_y = cy - height / 2 + radius
        bot_y = cy + height / 2 - radius

        if fill:
            draw.rectangle([cx - radius, top_y, cx + radius, bot_y], fill=fill)
            draw.ellipse([cx - radius, top_y - radius, cx + radius, top_y + radius], fill=fill)
            draw.ellipse([cx - radius, bot_y - radius, cx + radius, bot_y + radius], fill=fill)

        outline_pts = [
            (cx - radius, top_y), (cx - radius, bot_y),
            (cx + radius, bot_y), (cx + radius, top_y)
        ]
        
        # Caps and sides
        draw.line([(cx - radius, top_y), (cx - radius, bot_y)], fill=color, width=3)
        draw.line([(cx + radius, top_y), (cx + radius, bot_y)], fill=color, width=3)
        draw.arc([cx - radius, top_y - radius, cx + radius, top_y + radius], 180, 0, fill=color, width=3)
        draw.arc([cx - radius, bot_y - radius, cx + radius, bot_y + radius], 0, 180, fill=color, width=3)

        # Center axis & dot
        draw.line([(cx, top_y), (cx, bot_y)], fill=color, width=1)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)

    def draw_humanoid_stickman(self, draw: ImageDraw.ImageDraw, x: float, y: float, scale: float = 1.0, color: str = "#38bdf8", angle_deg: float = 0):
        # Head
        draw.ellipse([x - 14*scale, y - 60*scale, x + 14*scale, y - 32*scale], fill=color)
        # Spine
        draw.line([(x, y - 32*scale), (x, y + 10*scale)], fill=color, width=int(5*scale))
        # Arms
        draw.line([(x - 24*scale, y - 18*scale), (x + 24*scale, y - 18*scale)], fill=color, width=int(4*scale))
        # Legs
        draw.line([(x, y + 10*scale), (x - 20*scale, y + 55*scale)], fill=color, width=int(4*scale))
        draw.line([(x, y + 10*scale), (x + 20*scale, y + 55*scale)], fill=color, width=int(4*scale))


# ==============================================================================
# 3 TEST SCHEMES
# ==============================================================================

def generate_scheme_1_door_pinch(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 1: Дверь с бесконечной массой зажимает капсулу NPC у стены."""
    img, draw = renderer.create_canvas()

    # Title & Subtitle Badge
    renderer.draw_badge(draw, 30, 25, "CASE #01: KINEMATIC DOOR CRUSH", bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")
    draw.text((30, 68), "Движок не успевает вытолкнуть капсулу -> расчет урона сжатия delta_x -> inf", fill="#94a3b8", font=renderer.font_regular)

    # 1. Static Wall Collider (Right)
    wall_x1, wall_y1, wall_x2, wall_y2 = 780, 130, 980, 520
    renderer.draw_hazard_stripes(draw, wall_x1, wall_y1, wall_x2, wall_y2, stripe_w=18)
    draw.text(((wall_x1 + wall_x2)/2, 325), "STATIC WALL\n(Collider)", fill="#f8fafc", font=renderer.font_bold, anchor="mm", align="center")

    # 2. Door Pivot & Rotating Door (OBB)
    pivot_x, pivot_y = 200, 460
    # Hinge
    draw.ellipse([pivot_x - 16, pivot_y - 16, pivot_x + 16, pivot_y + 16], fill="#f59e0b", outline="#fef08a", width=3)
    draw.text((pivot_x - 30, pivot_y + 26), "HINGE (0,0)", fill="#f59e0b", font=renderer.font_mono_bold)

    # Rotation Arc
    draw.arc([pivot_x - 360, pivot_y - 360, pivot_x + 360, pivot_y + 360], 280, 350, fill="#38bdf8", width=2)
    renderer.draw_vector(draw, (360, 200), (450, 165), color="#38bdf8", width=4, label="omega (ROTATION)", label_side="left")

    # Door Geometry (Angle ~ 38 deg)
    door_pts = [(200, 460), (590, 190), (610, 215), (220, 485)]
    draw.polygon(door_pts, fill="#1e293b", outline="#0ea5e9")
    renderer.draw_hazard_stripes(draw, 340, 310, 580, 340, stripe_w=10)
    draw.text((350, 390), "DOOR (m = inf)", fill="#38bdf8", font=renderer.font_mono_bold)

    # 3. NPC Capsule (Pushed into Wall)
    npc_cx, npc_cy = 710, 310
    # Ghost past position
    renderer.draw_capsule_collider(draw, 640, 310, radius=55, height=180, color="#475569", dashed=True)
    draw.text((640, 200), "t = 0", fill="#64748b", font=renderer.font_mono)

    # Current pinched capsule
    renderer.draw_capsule_collider(draw, npc_cx, npc_cy, radius=55, height=180, color="#22c55e", fill="#14532d55")
    renderer.draw_humanoid_stickman(draw, npc_cx, npc_cy - 10, scale=0.85, color="#86efac")
    draw.text((npc_cx, npc_cy + 115), "NPC CAPSULE", fill="#4ade80", font=renderer.font_mono_bold, anchor="mm")

    # 4. Overlap & Contact Zone
    renderer.draw_contact_point(draw, 635, 255, label="P1 (DOOR HIT)", color="#ef4444")
    renderer.draw_contact_point(draw, 765, 310, label="P2 (WALL PINCH)", color="#ef4444")

    # Impulse & Normal Vectors
    renderer.draw_vector(draw, (635, 255), (730, 255), color="#ef4444", width=5, label="F_door = inf", label_side="right")
    renderer.draw_vector(draw, (765, 310), (710, 310), color="#eab308", width=4, label="N_wall", label_side="left")

    # Bottom Formula Card
    draw.rectangle([30, 520, 1050, 580], fill="#111827", outline="#ef4444", width=2)
    draw.text((540, 550), "IMPULSE: J = -(1 + e)*v_rel / (1/m1 + 1/m2)  =>  m1=inf -> J=inf -> HP=0 (INSTANT KILL)", fill="#fca5a5", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 1 сгенерирована: {out_path}")


def generate_scheme_2_skyrim_giant_space(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 2: Удар дубиной великана в Skyrim и запуск в космос (Overkill Ragdoll Velocity)."""
    img, draw = renderer.create_canvas()

    # Title & Badge
    renderer.draw_badge(draw, 30, 25, "CASE #02: SKYRIM GIANT SPACE PROGRAM", bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")
    draw.text((30, 68), "Отрицательное HP переводится физ. движком Havok в вектор вертикального отскока", fill="#94a3b8", font=renderer.font_regular)

    # 1. Ground Surface (Static Plane)
    draw.line([(50, 480), (1030, 480)], fill="#38bdf8", width=4)
    renderer.draw_hazard_stripes(draw, 50, 484, 1030, 520, stripe_w=16)
    draw.text((540, 502), "TERRAIN COLLIDER (Static)", fill="#ffffff", font=renderer.font_mono_bold, anchor="mm")

    # 2. Giant Character Silhouette & Giant Club
    giant_x, giant_y = 240, 320
    # Giant Body (Large box collider)
    draw.rounded_rectangle([giant_x - 60, giant_y - 140, giant_x + 60, giant_y + 150], radius=16, fill="#312e81", outline="#818cf8", width=3)
    draw.text((giant_x, giant_y), "GIANT\n(Mass: 2500kg)", fill="#c7d2fe", font=renderer.font_bold, anchor="mm", align="center")

    # Club Heavy Downward Strike
    club_start = (giant_x + 30, giant_y - 110)
    club_end = (460, 460)
    draw.line([club_start, club_end], fill="#78350f", width=22)
    draw.ellipse([club_end[0] - 30, club_end[1] - 40, club_end[0] + 30, club_end[1] + 20], fill="#92400e", outline="#fde68a", width=3)
    draw.text((460, 400), "CLUB\n(5000 Dmg)", fill="#fef08a", font=renderer.font_mono_bold, anchor="mm", align="center")

    # Downward Force Vector
    renderer.draw_vector(draw, (440, 320), (460, 450), color="#ef4444", width=6, label="F_impact (DOWN)", label_side="left")

    # 3. Impact Point & Ground Compression
    renderer.draw_contact_point(draw, 460, 475, label="OVERKILL CONTACT", color="#f43f5e")

    # 4. Player Ragdoll Launch (Massive Upward Vector)
    player_x, player_y = 520, 450
    # Player on ground
    renderer.draw_capsule_collider(draw, player_x, player_y - 20, radius=22, height=60, color="#f87171", fill="#7f1d1d")
    draw.text((player_x + 40, player_y - 20), "HP = -4500", fill="#f87171", font=renderer.font_mono_bold)

    # Giant Cosmic Velocity Vector (Arrow to the stratosphere!)
    renderer.draw_vector(draw, (player_x, player_y - 60), (780, 110), color="#22c55e", width=7, label="V_launch = 850 m/s (UPWARDS)", label_side="right")
    
    # Trajectory Arc
    draw.arc([300, 80, 950, 700], 180, 270, fill="#a855f7", width=2)

    # Flying Ragdoll Silhouette high in sky
    sky_x, sky_y = 780, 110
    renderer.draw_capsule_collider(draw, sky_x, sky_y, radius=18, height=45, color="#4ade80", fill="#14532d")
    renderer.draw_humanoid_stickman(draw, sky_x, sky_y, scale=0.6, color="#bbf7d0")
    draw.text((sky_x + 30, sky_y), "ALTITUDE: 3200m\n(Stratosphere)", fill="#4ade80", font=renderer.font_mono_bold)

    # Bottom Explanatory Card
    draw.rectangle([30, 530, 1050, 585], fill="#111827", outline="#8b5cf6", width=2)
    draw.text((540, 557), "OVERKILL BUG: Havok Physics рассчитывает отскок пропорционально избыточному урону!", fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 2 сгенерирована: {out_path}")


def generate_scheme_3_roach_roof_raycast(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 3: Плотва на крыше в Witcher 3 (Raycast Spawn / Surface Normal Error)."""
    img, draw = renderer.create_canvas()

    # Title & Badge
    renderer.draw_badge(draw, 30, 25, "CASE #03: WITCHER 3 - ROACH ROOF RAYCAST", bg_color="#0f172a", text_color="#f59e0b", border_color="#f59e0b")
    draw.text((30, 68), "Функция CallHorse() пускает Raycast сверху вниз и спавнит маунта на первом коллайдере", fill="#94a3b8", font=renderer.font_regular)

    # 1. Ground Surface
    draw.line([(50, 500), (1030, 500)], fill="#38bdf8", width=3)
    draw.text((120, 525), "TERRAIN (Target Ground)", fill="#38bdf8", font=renderer.font_mono_bold)

    # 2. House Structure & Roof Collider
    house_x, house_y = 520, 500
    # House Body
    draw.rectangle([house_x - 180, house_y - 180, house_x + 180, house_y], fill="#1e293b", outline="#64748b", width=3)
    draw.text((house_x, house_y - 80), "VILLAGE HOUSE\n(Mesh Collider)", fill="#94a3b8", font=renderer.font_bold, anchor="mm", align="center")

    # Triangular Roof
    roof_pts = [(house_x - 220, house_y - 180), (house_x, house_y - 300), (house_x + 220, house_y - 180)]
    draw.polygon(roof_pts, fill="#334155", outline="#e2e8f0")
    renderer.draw_hazard_stripes(draw, house_x - 100, house_y - 250, house_x + 100, house_y - 230, stripe_w=10)

    # 3. Raycast Origin (High in Sky / Camera offset)
    cam_x, cam_y = 520, 110
    draw.ellipse([cam_x - 12, cam_y - 12, cam_x + 12, cam_y + 12], fill="#38bdf8", outline="#e0f2fe", width=3)
    draw.text((cam_x + 20, cam_y - 6), "CAMERA RAY ORIGIN", fill="#38bdf8", font=renderer.font_mono_bold)

    # Raycast Line (Dashed laser beam down)
    renderer.draw_vector(draw, (cam_x, cam_y + 15), (cam_x, house_y - 295), color="#f43f5e", width=4, label="RaycastAll(DOWN)", label_side="left")

    # Hit Point on Roof Ridge
    renderer.draw_contact_point(draw, house_x, house_y - 300, label="HIT POINT #1 (ROOF)", color="#ef4444")
    renderer.draw_vector(draw, (house_x, house_y - 300), (house_x, house_y - 360), color="#38bdf8", width=4, label="n_surface", label_side="right")

    # 4. Roach (Horse Collider Box) Spawned on Top of Roof!
    horse_cx, horse_cy = house_x, house_y - 340
    # Horse Box Collider
    draw.rounded_rectangle([horse_cx - 90, horse_cy - 40, horse_cx + 90, horse_cy + 30], radius=12, fill="#7c2d1299", outline="#f97316", width=3)
    draw.text((horse_cx, horse_cy - 5), "ROACH (HORSE)\nSpawned Here!", fill="#ffedd5", font=renderer.font_bold, anchor="mm", align="center")

    # Missed Ground Marker
    draw.ellipse([house_x - 8, house_y - 8, house_x + 8, house_y + 8], outline="#64748b", width=2)
    draw.text((house_x + 20, house_y - 5), "EXPECTED GROUND (Ignored)", fill="#64748b", font=renderer.font_mono)

    # Bottom Formula Card
    draw.rectangle([30, 535, 1050, 588], fill="#111827", outline="#f59e0b", width=2)
    draw.text((540, 561), "FIX: Physics.Raycast(layerMask: TERRAIN_ONLY, ignoreMask: ROOF | PROPS)", fill="#fef08a", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 3 сгенерирована: {out_path}")


if __name__ == "__main__":
    renderer = PhysicsDiagramRenderer(width=1080, height=600)
    out_dir = Path("output/diagram_demos")
    print("\n🎨 Генерация 3 демонстрационных схем физики коллизий...")
    generate_scheme_1_door_pinch(renderer, out_dir / "scheme_1_door_crush.png")
    generate_scheme_2_skyrim_giant_space(renderer, out_dir / "scheme_2_skyrim_giant.png")
    generate_scheme_3_roach_roof_raycast(renderer, out_dir / "scheme_3_roach_roof.png")
    print("\n✨ Все 3 схемы успешно созданы в output/diagram_demos/")
