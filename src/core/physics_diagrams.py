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
        
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
            self.font_regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 19)
            self.font_mono_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 22)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_mono_bold = ImageFont.load_default()
            self.font_badge = ImageFont.load_default()

    def create_canvas(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGBA", (self.width, self.height), "#0a0f1d")
        draw = ImageDraw.Draw(img)
        self._draw_grid(draw)
        return img, draw

    def _draw_grid(self, draw: ImageDraw.ImageDraw, step: int = 45):
        # Subtle technical grid
        for x in range(0, self.width, step):
            color = "#141e33" if x % (step * 3) != 0 else "#1c2b48"
            draw.line([(x, 0), (x, self.height)], fill=color, width=1)
        for y in range(0, self.height, step):
            color = "#141e33" if y % (step * 3) != 0 else "#1c2b48"
            draw.line([(0, y), (self.width, y)], fill=color, width=1)
        draw.rectangle([0, 0, self.width - 1, self.height - 1], outline="#38bdf8", width=3)

    def draw_badge(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color: str = "#1e293b", text_color: str = "#38bdf8", border_color: str = "#0ea5e9"):
        bbox = draw.textbbox((x + 16, y + 8), text, font=self.font_badge)
        draw.rounded_rectangle([x, y, bbox[2] + 16, bbox[3] + 8], radius=8, fill=bg_color, outline=border_color, width=2)
        draw.text((x + 16, y + 8), text, fill=text_color, font=self.font_badge)

    def draw_hazard_stripes(self, draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, stripe_w: int = 18):
        w = x2 - x1
        h = y2 - y1
        draw.rectangle([x1, y1, x2, y2], fill="#18181b", outline="#eab308", width=2)
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
            dist = 22
            nx = -math.sin(angle) * dist
            ny = math.cos(angle) * dist
            if label_side == "left":
                nx, ny = -nx, -ny
            draw.text((mx + nx, my + ny), label, fill=color, font=self.font_bold, anchor="mm")

    def draw_contact_point(self, draw: ImageDraw.ImageDraw, x: float, y: float, label: str = "P", color: str = "#ef4444", label_side: str = "top"):
        draw.ellipse([x - 12, y - 12, x + 12, y + 12], outline=color, width=2)
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=color)
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill="#ffffff")
        
        ly = y - 24 if label_side == "top" else y + 24
        draw.text((x, ly), label, fill=color, font=self.font_bold, anchor="mm")

    def draw_capsule_collider(
        self, draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, height: float,
        color: str = "#22c55e", fill: str = None
    ):
        top_y = cy - height / 2 + radius
        bot_y = cy + height / 2 - radius

        if fill:
            draw.rectangle([cx - radius, top_y, cx + radius, bot_y], fill=fill)
            draw.ellipse([cx - radius, top_y - radius, cx + radius, top_y + radius], fill=fill)
            draw.ellipse([cx - radius, bot_y - radius, cx + radius, bot_y + radius], fill=fill)

        draw.line([(cx - radius, top_y), (cx - radius, bot_y)], fill=color, width=3)
        draw.line([(cx + radius, top_y), (cx + radius, bot_y)], fill=color, width=3)
        draw.arc([cx - radius, top_y - radius, cx + radius, top_y + radius], 180, 0, fill=color, width=3)
        draw.arc([cx - radius, bot_y - radius, cx + radius, bot_y + radius], 0, 180, fill=color, width=3)
        draw.line([(cx, top_y), (cx, bot_y)], fill=color, width=1)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=color)

    def draw_humanoid_stickman(self, draw: ImageDraw.ImageDraw, x: float, y: float, scale: float = 1.0, color: str = "#38bdf8"):
        # Head
        draw.ellipse([x - 14*scale, y - 55*scale, x + 14*scale, y - 27*scale], fill=color)
        # Spine
        draw.line([(x, y - 27*scale), (x, y + 15*scale)], fill=color, width=int(5*scale))
        # Arms
        draw.line([(x - 22*scale, y - 12*scale), (x + 22*scale, y - 12*scale)], fill=color, width=int(4*scale))
        # Legs
        draw.line([(x, y + 15*scale), (x - 18*scale, y + 55*scale)], fill=color, width=int(4*scale))
        draw.line([(x, y + 15*scale), (x + 18*scale, y + 55*scale)], fill=color, width=int(4*scale))


# ==============================================================================
# CLEAN & SIMPLIFIED SCHEMES (NO OVERLAP, MINIMAL CLEAR TEXT)
# ==============================================================================

def generate_scheme_1_door_pinch(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 1: Дверь с бесконечной массой зажимает NPC у стены."""
    img, draw = renderer.create_canvas()

    # Badge Header
    renderer.draw_badge(draw, 40, 25, "FAR CRY 6: СМЕРТОНОСНАЯ ДВЕРЬ", bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    # 1. Door (Left / Angular)
    pivot_x, pivot_y = 120, 420
    draw.ellipse([pivot_x - 12, pivot_y - 12, pivot_x + 12, pivot_y + 12], fill="#f59e0b", outline="#fef08a", width=3)
    draw.text((pivot_x, pivot_y + 24), "Петля", fill="#f59e0b", font=renderer.font_bold, anchor="mm")

    # Rotating Door Polygon
    door_pts = [(120, 420), (490, 180), (510, 205), (140, 445)]
    draw.polygon(door_pts, fill="#1e293b", outline="#38bdf8", width=3)
    draw.text((280, 260), "ДВЕРЬ\n(Масса = ∞)", fill="#38bdf8", font=renderer.font_bold, anchor="mm", align="center")

    # Movement Vector
    renderer.draw_vector(draw, (360, 190), (480, 190), color="#38bdf8", width=5, label="Движение", label_side="left")

    # 2. NPC Capsule (Center)
    npc_x, npc_y = 610, 290
    renderer.draw_capsule_collider(draw, npc_x, npc_y, radius=48, height=170, color="#22c55e", fill="#14532d44")
    renderer.draw_humanoid_stickman(draw, npc_x, npc_y - 5, scale=0.85, color="#86efac")
    draw.text((npc_x, npc_y + 115), "Игрок / NPC", fill="#4ade80", font=renderer.font_bold, anchor="mm")

    # 3. Static Wall (Right)
    wall_x1, wall_y1, wall_x2, wall_y2 = 720, 140, 860, 450
    renderer.draw_hazard_stripes(draw, wall_x1, wall_y1, wall_x2, wall_y2, stripe_w=18)
    draw.text(((wall_x1 + wall_x2)/2, wall_y1 - 25), "СТЕНА (Препятствие)", fill="#eab308", font=renderer.font_bold, anchor="mm")

    # 4. Impact Points (Clear & Non-overlapping)
    renderer.draw_contact_point(draw, 520, 240, label="Удар дверью", color="#ef4444", label_side="top")
    renderer.draw_contact_point(draw, 700, 290, label="Зажатие", color="#ef4444", label_side="top")

    # 5. Bottom Simple Formula Banner
    draw.rounded_rectangle([40, 500, 1040, 565], radius=12, fill="#111827", outline="#ef4444", width=2)
    draw.text((540, 532), "УРОН = Скорость двери × Масса двери (∞) = 9999 ХП", fill="#fca5a5", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 1 сгенерирована: {out_path}")


def generate_scheme_2_skyrim_giant_space(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 2: Удар великана в Skyrim и полет в космос."""
    img, draw = renderer.create_canvas()

    # Badge Header
    renderer.draw_badge(draw, 40, 25, "SKYRIM: ПОЛЕТ В КОСМОС ОТ ВЕЛИКАНА", bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")

    # 1. Ground
    draw.line([(40, 460), (1040, 460)], fill="#64748b", width=4)
    draw.text((100, 485), "Земля (Коллайдер)", fill="#94a3b8", font=renderer.font_bold, anchor="mm")

    # 2. Giant with Club (Left)
    gx, gy = 200, 310
    draw.rounded_rectangle([gx - 50, gy - 120, gx + 50, gy + 140], radius=14, fill="#312e81", outline="#818cf8", width=3)
    draw.text((gx, gy), "ВЕЛИКАН", fill="#c7d2fe", font=renderer.font_bold, anchor="mm")

    # Club Strike Downward
    draw.line([(gx + 30, gy - 70), (370, 420)], fill="#78350f", width=18)
    draw.ellipse([345, 390, 405, 450], fill="#92400e", outline="#fde68a", width=3)
    
    # Downward Strike Vector
    renderer.draw_vector(draw, (375, 270), (375, 410), color="#ef4444", width=6, label="Удар дубиной", label_side="left")
    renderer.draw_contact_point(draw, 375, 455, label="Урон: -5000 HP", color="#f43f5e", label_side="top")

    # 3. Space Launch Vector (Right)
    player_ground_x = 450
    renderer.draw_capsule_collider(draw, player_ground_x, 435, radius=18, height=45, color="#ef4444", fill="#7f1d1d")

    # Massive Arc Arrow to Sky
    renderer.draw_vector(draw, (470, 410), (840, 160), color="#22c55e", width=7, label="Скорость взлета: 850 м/с", label_side="right")

    # Flying Character in Stratosphere
    sky_x, sky_y = 880, 130
    renderer.draw_capsule_collider(draw, sky_x, sky_y, radius=22, height=60, color="#4ade80", fill="#14532d")
    renderer.draw_humanoid_stickman(draw, sky_x, sky_y, scale=0.7, color="#bbf7d0")
    draw.text((sky_x, sky_y + 55), "Стратосфера (3000м)", fill="#4ade80", font=renderer.font_bold, anchor="mm")

    # 4. Bottom Simple Explanation Banner
    draw.rounded_rectangle([40, 500, 1040, 565], radius=12, fill="#111827", outline="#8b5cf6", width=2)
    draw.text((540, 532), "ФИЗИКА: Избыточный урон движок перевел в импульс отскока вверх", fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 2 сгенерирована: {out_path}")


def generate_scheme_3_roach_roof_raycast(renderer: PhysicsDiagramRenderer, out_path: Path):
    """Схема 3: Спавн Плотвы на крыше в Witcher 3."""
    img, draw = renderer.create_canvas()

    # Badge Header
    renderer.draw_badge(draw, 40, 25, "ВЕДЬМАК 3: ПЛОТВА НА КРЫШЕ ДОМА", bg_color="#0f172a", text_color="#f59e0b", border_color="#f59e0b")

    # 1. Ground Surface
    draw.line([(40, 460), (1040, 460)], fill="#64748b", width=4)
    draw.text((120, 485), "Земля (Игнорируется)", fill="#94a3b8", font=renderer.font_bold, anchor="mm")

    # 2. House (Center-Right)
    hx, hy = 580, 460
    # House Body
    draw.rectangle([hx - 150, hy - 140, hx + 150, hy], fill="#1e293b", outline="#64748b", width=3)
    draw.text((hx, hy - 60), "ДОМ", fill="#94a3b8", font=renderer.font_bold, anchor="mm")

    # Triangular Roof
    roof_pts = [(hx - 180, hy - 140), (hx, hy - 240), (hx + 180, hy - 140)]
    draw.polygon(roof_pts, fill="#334155", outline="#f8fafc", width=3)

    # 3. Raycast from Camera (Top)
    cam_x, cam_y = 580, 100
    draw.ellipse([cam_x - 10, cam_y - 10, cam_x + 10, cam_y + 10], fill="#38bdf8")
    draw.text((cam_x, cam_y - 20), "Камера игрока", fill="#38bdf8", font=renderer.font_bold, anchor="mm")

    # Raycast Beam
    renderer.draw_vector(draw, (cam_x, cam_y + 15), (cam_x, hy - 245), color="#f43f5e", width=4, label="Луч поиска земли (Raycast)", label_side="left")

    # Hit Point on Roof
    renderer.draw_contact_point(draw, hx, hy - 240, label="Точка спавна", color="#ef4444", label_side="top")

    # 4. Roach Silhouette on Roof
    horse_x, horse_y = hx + 10, hy - 290
    draw.rounded_rectangle([horse_x - 70, horse_y - 30, horse_x + 70, horse_y + 30], radius=10, fill="#7c2d12cc", outline="#f97316", width=3)
    draw.text((horse_x, horse_y), "ПЛОТВА (Спавн)", fill="#ffedd5", font=renderer.font_bold, anchor="mm")

    # 5. Bottom Simple Fix Banner
    draw.rounded_rectangle([40, 500, 1040, 565], radius=12, fill="#111827", outline="#f59e0b", width=2)
    draw.text((540, 532), "ОШИБКА: Игра ставит лошадь на ПЕРВОЕ препятствие на пути луча (крышу)", fill="#fef08a", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"   ✓ Схема 3 сгенерирована: {out_path}")


if __name__ == "__main__":
    renderer = PhysicsDiagramRenderer(width=1080, height=600)
    out_dir = Path("output/diagram_demos")
    print("\n🎨 Генерация упрощенных, просторных схем без наслоений...")
    generate_scheme_1_door_pinch(renderer, out_dir / "scheme_1_door_crush.png")
    generate_scheme_2_skyrim_giant_space(renderer, out_dir / "scheme_2_skyrim_giant.png")
    generate_scheme_3_roach_roof_raycast(renderer, out_dir / "scheme_3_roach_roof.png")
    print("\n✨ Все 3 схемы успешно обновлены!")
