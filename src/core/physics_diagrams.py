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
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 24)
            self.font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
            self.font_regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 17)
            self.font_mono_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 20)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
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
        for x in range(0, self.width, step):
            color = "#141e33" if x % (step * 3) != 0 else "#1c2b48"
            draw.line([(x, 0), (x, self.height)], fill=color, width=1)
        for y in range(0, self.height, step):
            color = "#141e33" if y % (step * 3) != 0 else "#1c2b48"
            draw.line([(0, y), (self.width, y)], fill=color, width=1)
        draw.rectangle([0, 0, self.width - 1, self.height - 1], outline="#38bdf8", width=3)

    def draw_badge(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color: str = "#1e293b", text_color: str = "#38bdf8", border_color: str = "#0ea5e9"):
        bbox = draw.textbbox((x + 14, y + 6), text, font=self.font_badge)
        draw.rounded_rectangle([x, y, bbox[2] + 14, bbox[3] + 6], radius=6, fill=bg_color, outline=border_color, width=2)
        draw.text((x + 14, y + 6), text, fill=text_color, font=self.font_badge)

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
            
            if abs(dx) < 1e-4 or abs(math.cos(angle)) < 0.2:
                if label_side == "right":
                    draw.text((mx + 16, my), label, fill=color, font=self.font_bold, anchor="lm")
                else:
                    draw.text((mx - 16, my), label, fill=color, font=self.font_bold, anchor="rm")
            else:
                dist = 24
                nx = -math.sin(angle) * dist
                ny = math.cos(angle) * dist
                if label_side == "left":
                    nx, ny = -nx, -ny
                draw.text((mx + nx, my + ny), label, fill=color, font=self.font_bold, anchor="mm")

    def draw_contact_point(self, draw: ImageDraw.ImageDraw, x: float, y: float, label: str = "P", color: str = "#ef4444", label_side: str = "top"):
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], outline=color, width=2)
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=color)
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill="#ffffff")
        
        if label_side == "top":
            draw.text((x, y - 20), label, fill=color, font=self.font_bold, anchor="mm")
        elif label_side == "bottom":
            draw.text((x, y + 20), label, fill=color, font=self.font_bold, anchor="mm")
        elif label_side == "right":
            draw.text((x + 18, y), label, fill=color, font=self.font_bold, anchor="lm")
        else:
            draw.text((x - 18, y), label, fill=color, font=self.font_bold, anchor="rm")

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
        draw.ellipse([x - 14*scale, y - 55*scale, x + 14*scale, y - 27*scale], fill=color)
        draw.line([(x, y - 27*scale), (x, y + 15*scale)], fill=color, width=int(5*scale))
        draw.line([(x - 22*scale, y - 12*scale), (x + 22*scale, y - 12*scale)], fill=color, width=int(4*scale))
        draw.line([(x, y + 15*scale), (x - 18*scale, y + 55*scale)], fill=color, width=int(4*scale))
        draw.line([(x, y + 15*scale), (x + 18*scale, y + 55*scale)], fill=color, width=int(4*scale))

    def draw_2d_car(self, draw: ImageDraw.ImageDraw, cx: float, cy: float, scale: float = 1.0, color: str = "#3b82f6", outline: str = "#93c5fd", angle_deg: float = 0):
        w = 140 * scale
        h = 45 * scale
        wheel_r = 16 * scale

        draw.rounded_rectangle([cx - w/2, cy - h/2 + 10*scale, cx + w/2, cy + h/2], radius=int(8*scale), fill=color, outline=outline, width=2)
        roof_pts = [
            (cx - w/4, cy - h/2 + 10*scale),
            (cx - w/6, cy - h/2 - 18*scale),
            (cx + w/6, cy - h/2 - 18*scale),
            (cx + w/3, cy - h/2 + 10*scale)
        ]
        draw.polygon(roof_pts, fill=color, outline=outline)

        wheel_y = cy + h/2 + 2*scale
        for wx in [cx - w/3, cx + w/3]:
            draw.ellipse([wx - wheel_r, wheel_y - wheel_r, wx + wheel_r, wheel_y + wheel_r], fill="#18181b", outline="#e2e8f0", width=2)
            draw.ellipse([wx - wheel_r/3, wheel_y - wheel_r/3, wx + wheel_r/3, wheel_y + wheel_r/3], fill="#94a3b8")

    def draw_barrel_prop(self, draw: ImageDraw.ImageDraw, cx: float, cy: float, w: float = 60, h: float = 80, color: str = "#0284c7"):
        draw.rounded_rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], radius=8, fill=color, outline="#7dd3fc", width=2)
        draw.line([(cx - w/2, cy - h/6), (cx + w/2, cy - h/6)], fill="#0369a1", width=3)
        draw.line([(cx - w/2, cy + h/6), (cx + w/2, cy + h/6)], fill="#0369a1", width=3)


# ==============================================================================
# SCHEMES WITH MULTI-LANGUAGE (RU / EN) SUPPORT
# ==============================================================================

def generate_scheme_1_door_pinch(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Схема 1: Far Cry 6 (Смертоносная дверь)."""
    img, draw = renderer.create_canvas()

    title_badge = "FAR CRY 6: LETHAL DOOR IMPULSE" if lang == "en" else "FAR CRY 6: СМЕРТОНОСНАЯ ДВЕРЬ"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    pivot_x, pivot_y = 120, 420
    draw.ellipse([pivot_x - 12, pivot_y - 12, pivot_x + 12, pivot_y + 12], fill="#f59e0b", outline="#fef08a", width=3)
    draw.text((pivot_x, pivot_y + 24), "Hinge (0,0)" if lang == "en" else "Петля", fill="#f59e0b", font=renderer.font_bold, anchor="mm")

    door_pts = [(120, 420), (490, 180), (510, 205), (140, 445)]
    draw.polygon(door_pts, fill="#1e293b", outline="#38bdf8", width=3)
    door_lbl = "DOOR\n(Mass = ∞)" if lang == "en" else "ДВЕРЬ\n(Масса = ∞)"
    draw.text((270, 270), door_lbl, fill="#38bdf8", font=renderer.font_bold, anchor="mm", align="center")

    move_lbl = "Rotation" if lang == "en" else "Движение"
    renderer.draw_vector(draw, (360, 170), (490, 170), color="#38bdf8", width=5, label=move_lbl, label_side="left")

    npc_x, npc_y = 620, 290
    renderer.draw_capsule_collider(draw, npc_x, npc_y, radius=48, height=170, color="#22c55e", fill="#14532d44")
    renderer.draw_humanoid_stickman(draw, npc_x, npc_y - 5, scale=0.85, color="#86efac")
    npc_lbl = "Player / NPC" if lang == "en" else "Игрок / NPC"
    draw.text((npc_x, npc_y + 115), npc_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    wall_x1, wall_y1, wall_x2, wall_y2 = 740, 140, 880, 450
    renderer.draw_hazard_stripes(draw, wall_x1, wall_y1, wall_x2, wall_y2, stripe_w=18)
    wall_lbl = "STATIC WALL" if lang == "en" else "СТЕНА (Препятствие)"
    draw.text(((wall_x1 + wall_x2)/2, wall_y1 - 25), wall_lbl, fill="#eab308", font=renderer.font_bold, anchor="mm")

    hit_lbl = "Door Hit" if lang == "en" else "Удар"
    pinch_lbl = "Crush Pinch" if lang == "en" else "Зажатие"
    renderer.draw_contact_point(draw, 520, 240, label=hit_lbl, color="#ef4444", label_side="top")
    renderer.draw_contact_point(draw, 720, 290, label=pinch_lbl, color="#ef4444", label_side="top")

    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#ef4444", width=2)
    formula_lbl = "DAMAGE = Door Velocity × Door Mass (∞) = 9999 HP" if lang == "en" else "УРОН = Скорость двери × Масса двери (∞) = 9999 ХП"
    draw.text((540, 535), formula_lbl, fill="#fca5a5", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 1 ({lang}) сгенерирована: {out_path}")


def generate_scheme_2_skyrim_giant_space(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Схема 2: Skyrim (Полет от великана)."""
    img, draw = renderer.create_canvas()
    title_badge = "SKYRIM: WHY GIANTS LAUNCH YOU TO SPACE" if lang == "en" else "SKYRIM: ПОЧЕМУ ВЕЛИКАН ЗАПУСКАЕТ В КОСМОС"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 360

    # ЛЕВАЯ КОЛОНКА
    col1_title = "1. CLUB PUSHES UNDERGROUND" if lang == "en" else "1. УДАР ЗАБИВАЕТ ПОД ЗЕМЛЮ"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((140, ground_y - 18), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    strike_lbl = "Club Strike" if lang == "en" else "Удар дубиной"
    renderer.draw_vector(draw, (270, 140), (270, 270), color="#ef4444", width=5, label=strike_lbl, label_side="right")

    cap_x, cap_y = 270, 410
    renderer.draw_capsule_collider(draw, cap_x, cap_y, radius=36, height=95, color="#ef4444", fill="#7f1d1d88")
    under_lbl = "Capsule Underground (Δx)" if lang == "en" else "Капсула под землей"
    draw.text((cap_x, cap_y + 65), under_lbl, fill="#f87171", font=renderer.font_bold, anchor="mm")

    # ПРАВАЯ КОЛОНКА
    col2_title = "2. SOLVER LAUNCHES SKYWARD" if lang == "en" else "2. ДВИЖОК КАТАПУЛЬТИРУЕТ ВВЕРХ"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y - 18), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    push_lbl = "Repulsion Force" if lang == "en" else "Сила выталкивания"
    renderer.draw_vector(draw, (810, ground_y), (810, 250), color="#22c55e", width=6, label=push_lbl, label_side="right")

    fly_x, fly_y = 810, 195
    renderer.draw_capsule_collider(draw, fly_x, fly_y, radius=22, height=60, color="#4ade80", fill="#14532d55")
    renderer.draw_humanoid_stickman(draw, fly_x, fly_y, scale=0.65, color="#bbf7d0")
    flight_lbl = "Orbit Flight\n(850 m/s)" if lang == "en" else "Полет в стратосферу\n(850 м/с)"
    draw.text((fly_x + 40, fly_y), flight_lbl, fill="#4ade80", font=renderer.font_bold, anchor="lm")

    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#8b5cf6", width=2)
    bottom_lbl = "PHYSICS: The deeper an object is buried, the harder the physics engine repels it upward" if lang == "en" else "ФИЗИКА: Чем глубже забит объект под землю, тем сильнее движок выталкивает его вверх"
    draw.text((540, 535), bottom_lbl, fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 2 ({lang}) сгенерирована: {out_path}")


def generate_scheme_3_roach_roof_raycast(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Схема 3: Ведьмак 3 (Плотва на крыше)."""
    img, draw = renderer.create_canvas()
    title_badge = "WITCHER 3: WHY ROACH SPAWNS ON ROOFS" if lang == "en" else "ВЕДЬМАК 3: ПОЧЕМУ ПЛОТВА СПАВНИТСЯ НА КРЫШЕ"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#f59e0b", border_color="#f59e0b")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 420

    # ЛЕВАЯ КОЛОНКА
    col1_title = "NORMAL: GROUND SPAWN" if lang == "en" else "НОРМА: СПАВН НА ЗЕМЛЕ"
    draw.text((270, 85), col1_title, fill="#38bdf8", font=renderer.font_bold, anchor="mm")
    ray1_x = 270
    draw.ellipse([ray1_x - 8, 140 - 8, ray1_x + 8, 140 + 8], fill="#38bdf8")
    origin_lbl = "Raycast Origin" if lang == "en" else "Точка проверки"
    draw.text((ray1_x, 120), origin_lbl, fill="#38bdf8", font=renderer.font_regular, anchor="mm")

    ray_lbl = "Raycast Down" if lang == "en" else "Луч вниз"
    renderer.draw_vector(draw, (ray1_x, 150), (ray1_x, ground_y - 5), color="#38bdf8", width=4, label=ray_lbl, label_side="left")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((120, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    draw.rounded_rectangle([ray1_x - 65, ground_y - 45, ray1_x + 65, ground_y - 5], radius=8, fill="#166534", outline="#4ade80", width=2)
    horse1_lbl = "ROACH (Ground)" if lang == "en" else "ПЛОТВА (Земля)"
    draw.text((ray1_x, ground_y - 25), horse1_lbl, fill="#ffffff", font=renderer.font_bold, anchor="mm")

    # ПРАВАЯ КОЛОНКА
    col2_title = "BUG: RAY HITS ROOF MESH" if lang == "en" else "БАГ: ЛУЧ УПЕРСЯ В КРЫШУ"
    draw.text((810, 85), col2_title, fill="#f59e0b", font=renderer.font_bold, anchor="mm")
    hx = 810
    house_w = 120
    roof_ridge_y = 260
    eaves_y = 340

    draw.polygon([(hx - house_w, eaves_y), (hx, roof_ridge_y), (hx + house_w, eaves_y)], fill="#334155", outline="#f8fafc", width=2)
    draw.rectangle([hx - house_w + 15, eaves_y, hx + house_w - 15, ground_y], fill="#1e293b", outline="#64748b", width=2)
    draw.text((hx, (eaves_y + ground_y)/2), "HOUSE" if lang == "en" else "ДОМ", fill="#64748b", font=renderer.font_bold, anchor="mm")

    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)

    ray2_x = hx
    draw.ellipse([ray2_x - 8, 140 - 8, ray2_x + 8, 140 + 8], fill="#f43f5e")
    draw.text((ray2_x, 120), origin_lbl, fill="#f43f5e", font=renderer.font_regular, anchor="mm")

    renderer.draw_vector(draw, (ray2_x, 150), (ray2_x, roof_ridge_y - 5), color="#f43f5e", width=4, label=ray_lbl, label_side="left")
    hit_lbl = "1st Hit: Roof" if lang == "en" else "1-е препятствие"
    renderer.draw_contact_point(draw, ray2_x, roof_ridge_y, label=hit_lbl, color="#ef4444", label_side="right")

    draw.rounded_rectangle([hx - 65, roof_ridge_y - 50, hx + 65, roof_ridge_y - 12], radius=8, fill="#7c2d12", outline="#f97316", width=2)
    horse2_lbl = "ROACH (Roof)" if lang == "en" else "ПЛОТВА (Крыша)"
    draw.text((hx, roof_ridge_y - 31), horse2_lbl, fill="#ffffff", font=renderer.font_bold, anchor="mm")

    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#f59e0b", width=2)
    bottom_lbl = "BUG: Engine spawns mount on the FIRST collider hit without LayerMask filtering" if lang == "en" else "ОШИБКА: Игра спавнит лошадь на первой попавшейся поверхности без фильтрации слоев"
    draw.text((540, 535), bottom_lbl, fill="#fef08a", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 3 ({lang}) сгенерирована: {out_path}")


def generate_scheme_4_gta_swingset(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Схема 4: GTA IV (Качели-убийцы)."""
    img, draw = renderer.create_canvas()
    title_badge = "GTA IV: SWINGSET CATAPULT GLITCH" if lang == "en" else "GTA IV: КАЧЕЛИ-УБИЙЦЫ (SWINGSET GLITCH)"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 380

    col1_title = "1. JOINT SPRING TENSION" if lang == "en" else "1. ЗАЖАТИЕ ШАРНИРА В ЗЕМЛЮ"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((120, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    swing_top_x, swing_top_y = 380, 150
    draw.line([(swing_top_x - 30, swing_top_y), (swing_top_x + 30, swing_top_y)], fill="#eab308", width=5)
    draw.ellipse([swing_top_x - 6, swing_top_y - 6, swing_top_x + 6, swing_top_y + 6], fill="#f59e0b")
    draw.text((swing_top_x, swing_top_y - 20), "Hinge Joint" if lang == "en" else "Шарнир (Joint)", fill="#f59e0b", font=renderer.font_bold, anchor="mm")

    seat_x, seat_y = 350, ground_y - 10
    draw.line([(swing_top_x, swing_top_y), (seat_x, seat_y)], fill="#ef4444", width=3)
    draw.rounded_rectangle([seat_x - 18, seat_y - 6, seat_x + 18, seat_y + 6], radius=3, fill="#ef4444")
    
    car1_x = 220
    renderer.draw_2d_car(draw, car1_x, ground_y - 30, scale=0.9, color="#1e40af", outline="#60a5fa")
    ram_lbl = "Ramming" if lang == "en" else "Таран"
    renderer.draw_vector(draw, (car1_x + 65, ground_y - 30), (seat_x - 10, ground_y - 10), color="#ef4444", width=4, label=ram_lbl, label_side="left")

    tension_lbl = "Tension: MAX" if lang == "en" else "Натяжение MAX"
    renderer.draw_contact_point(draw, seat_x, seat_y, label=tension_lbl, color="#ef4444", label_side="right")

    col2_title = "2. SUPERSONIC CATAPULT" if lang == "en" else "2. ВЫСТРЕЛ ЧЕРЕЗ ВЕСЬ ГОРОД"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    launch_start = (740, ground_y - 10)
    launch_end = (860, 180)
    impulse_lbl = "Impulse 1000 km/h" if lang == "en" else "Импульс 1000 км/ч"
    renderer.draw_vector(draw, launch_start, launch_end, color="#22c55e", width=7, label=impulse_lbl, label_side="left")

    flying_car_x, flying_car_y = 880, 180
    renderer.draw_2d_car(draw, flying_car_x, flying_car_y, scale=0.8, color="#1e40af", outline="#60a5fa")
    catapult_lbl = "Orbital Launch" if lang == "en" else "Катапультирование"
    draw.text((flying_car_x, flying_car_y - 45), catapult_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#0ea5e9", width=2)
    bottom_lbl = "PHYSICS: The hinge joint stores massive elastic potential energy and unleashes it instantly" if lang == "en" else "ФИЗИКА: Шарнир качелей накопил чудовищное натяжение и мгновенно разрядил его в машину"
    draw.text((540, 535), bottom_lbl, fill="#bae6fd", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 4 ({lang}) сгенерирована: {out_path}")


def generate_scheme_5_hl2_prop_flying(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Схема 5: Half-Life 2 (Проп-серфинг)."""
    img, draw = renderer.create_canvas()
    title_badge = "HALF-LIFE 2: PROP FLYING GLITCH" if lang == "en" else "HALF-LIFE 2: ПОЛЕТ НА БОЧКЕ (PROP FLYING)"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 400

    col1_title = "NORMAL: LIFTING PROP" if lang == "en" else "НОРМА: ПОДЪЕМ ПРЕДМЕТА"
    draw.text((270, 85), col1_title, fill="#38bdf8", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((120, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    p1_x, p1_y = 180, ground_y - 50
    renderer.draw_humanoid_stickman(draw, p1_x, p1_y, scale=0.8, color="#38bdf8")
    p1_lbl = "Player on Ground" if lang == "en" else "Игрок на земле"
    draw.text((p1_x, ground_y + 20), p1_lbl, fill="#38bdf8", font=renderer.font_regular, anchor="mm")

    barrel1_x, barrel1_y = 350, ground_y - 70
    renderer.draw_barrel_prop(draw, barrel1_x, barrel1_y, w=55, h=70, color="#0284c7")
    draw.text((barrel1_x, barrel1_y + 55), "Prop Barrel" if lang == "en" else "Бочка", fill="#7dd3fc", font=renderer.font_bold, anchor="mm")

    pull_lbl = "Pull Beam" if lang == "en" else "Тяга к себе"
    renderer.draw_vector(draw, (p1_x + 25, p1_y - 20), (barrel1_x - 30, barrel1_y - 10), color="#38bdf8", width=4, label=pull_lbl, label_side="left")

    col2_title = "BUG: CLOSED FORCE LOOP" if lang == "en" else "БАГ: ЗАМКНУТЫЙ ЦИКЛ СИЛ"
    draw.text((810, 85), col2_title, fill="#f59e0b", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 20), "Ground Below" if lang == "en" else "Земля осталась внизу", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    air_x = 760
    barrel_air_y = 280
    player_air_y = barrel_air_y - 85

    renderer.draw_barrel_prop(draw, air_x, barrel_air_y, w=65, h=75, color="#0284c7")
    renderer.draw_humanoid_stickman(draw, air_x, player_air_y, scale=0.8, color="#38bdf8")

    f1_lbl = "1. Hands pull barrel UP" if lang == "en" else "1. Руки тянут бочку"
    renderer.draw_vector(draw, (air_x - 45, barrel_air_y), (air_x - 45, player_air_y + 10), color="#f43f5e", width=4, label=f1_lbl, label_side="left")

    f2_lbl = "2. Barrel pushes feet UP" if lang == "en" else "2. Бочка толкает ноги"
    renderer.draw_vector(draw, (air_x + 45, barrel_air_y - 30), (air_x + 45, player_air_y - 40), color="#22c55e", width=4, label=f2_lbl, label_side="right")

    fly_hl_lbl = "Infinite Sky Ascent!" if lang == "en" else "Бесконечный взлет в небо!"
    draw.text((air_x, player_air_y - 60), fly_hl_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#f59e0b", width=2)
    bottom_lbl = "BUG: Physics engine fails to cancel the upward pull when player stands on the carried object" if lang == "en" else "БАГ: Физика Havok не проверяет, что игрок стоит на том же предмете, который тянет вверх"
    draw.text((540, 535), bottom_lbl, fill="#fef08a", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 5 ({lang}) сгенерирована: {out_path}")


if __name__ == "__main__":
    renderer = PhysicsDiagramRenderer(width=1080, height=600)
    out_dir_ru = Path("output/diagram_demos/ru")
    out_dir_en = Path("output/diagram_demos/en")
    
    print("\n🎨 Генерация схем на РУССКОМ языке...")
    generate_scheme_1_door_pinch(renderer, out_dir_ru / "scheme_1_door_crush.png", lang="ru")
    generate_scheme_2_skyrim_giant_space(renderer, out_dir_ru / "scheme_2_skyrim_giant.png", lang="ru")
    generate_scheme_3_roach_roof_raycast(renderer, out_dir_ru / "scheme_3_roach_roof.png", lang="ru")
    generate_scheme_4_gta_swingset(renderer, out_dir_ru / "scheme_4_gta_swingset.png", lang="ru")
    generate_scheme_5_hl2_prop_flying(renderer, out_dir_ru / "scheme_5_hl2_prop_flying.png", lang="ru")

    print("\n🎨 Generating schemes in ENGLISH...")
    generate_scheme_1_door_pinch(renderer, out_dir_en / "scheme_1_door_crush.png", lang="en")
    generate_scheme_2_skyrim_giant_space(renderer, out_dir_en / "scheme_2_skyrim_giant.png", lang="en")
    generate_scheme_3_roach_roof_raycast(renderer, out_dir_en / "scheme_3_roach_roof.png", lang="en")
    generate_scheme_4_gta_swingset(renderer, out_dir_en / "scheme_4_gta_swingset.png", lang="en")
    generate_scheme_5_hl2_prop_flying(renderer, out_dir_en / "scheme_5_hl2_prop_flying.png", lang="en")

    print("\n✨ Все схемы успешно созданы на RU и EN!")
def generate_scheme_farcry5_overlap(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Episode 5 Scheme 1: Far Cry 5 Double Overlap."""
    img, draw = renderer.create_canvas()
    title_badge = "FAR CRY 5: DOUBLE COLLISION OVERLAP" if lang == "en" else "FAR CRY 5: ДВОЙНОЕ ЗАЩЕМЛЕНИЕ ТРУПА"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 420

    # ЛЕВАЯ КОЛОНКА (540px)
    col1_title = "1. CORPSE CLAMPED IN VICE" if lang == "en" else "1. ЗАЩЕМЛЕНИЕ ТРУПА ВПРИТИРКУ"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")

    # Truck bed representation
    truck_box_y1, truck_box_y2 = 140, 240
    draw.rounded_rectangle([90, truck_box_y1, 450, truck_box_y2], radius=10, fill="#1e3a8a", outline="#60a5fa", width=2)
    truck_lbl = "TRUCK COLLIDER (5 TONS)" if lang == "en" else "КУЗОВ ПИКАПА (5 ТОНН)"
    draw.text((270, 190), truck_lbl, fill="#ffffff", font=renderer.font_bold, anchor="mm")

    # Ground
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((120, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Ragdoll capsule caught between
    rag_cx, rag_cy = 270, 330
    renderer.draw_capsule_collider(draw, rag_cx, rag_cy, radius=32, height=140, color="#ef4444", fill="#7f1d1d66")
    corpse_lbl = "Ragdoll (Δx overlap)" if lang == "en" else "Рэгдолл (Пересечение Δx)"
    draw.text((rag_cx, rag_cy), corpse_lbl, fill="#fca5a5", font=renderer.font_bold, anchor="mm")

    renderer.draw_contact_point(draw, rag_cx, truck_box_y2, label="P1: Truck" if lang == "en" else "P1: Кузов", color="#ef4444", label_side="left")
    renderer.draw_contact_point(draw, rag_cx, ground_y, label="P2: Ground" if lang == "en" else "P2: Земля", color="#ef4444", label_side="right")

    # ПРАВАЯ КОЛОНКА (540px)
    col2_title = "2. DUAL REPULSION SPIKE" if lang == "en" else "2. ДВОЙНОЙ ВЫТАЛКИВАЮЩИЙ ИМПУЛЬС"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Upward forces
    f1_lbl = "F1: Ground Push" if lang == "en" else "F1: От земли"
    renderer.draw_vector(draw, (750, ground_y - 10), (750, 260), color="#4ade80", width=5, label=f1_lbl, label_side="left")

    f2_lbl = "F2: Truck Reaction" if lang == "en" else "F2: Реакция опоры"
    renderer.draw_vector(draw, (870, ground_y - 10), (870, 260), color="#f59e0b", width=5, label=f2_lbl, label_side="right")

    # Net launch force
    f_net_lbl = "F_NET = F1 + F2 = MAX!" if lang == "en" else "F_ИТОГ = F1 + F2 (В КОСМОС!)"
    renderer.draw_vector(draw, (810, 250), (810, 130), color="#38bdf8", width=7, label=f_net_lbl, label_side="right")

    # Bottom banner
    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#38bdf8", width=2)
    bottom_lbl = "PHYSICS: Body wedged between two solids -> Solver sums upward repulsion forces" if lang == "en" else "ФИЗИКА: Труп зажат между двумя телами -> Движок суммирует силы выталкивания вверх"
    draw.text((540, 535), bottom_lbl, fill="#bae6fd", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 1 Far Cry 5 ({lang}) сгенерирована: {out_path}")


def generate_scheme_farcry5_launch(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Episode 5 Scheme 2: Far Cry 5 Launch to Orbit."""
    img, draw = renderer.create_canvas()
    title_badge = "FAR CRY 5: SPACE PROGRAM CATAPULT" if lang == "en" else "FAR CRY 5: КОСМИЧЕСКАЯ ПРОГРАММА СЕКТАНТОВ"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 400

    # ЛЕВАЯ КОЛОНКА (540px)
    col1_title = "1. MASSIVE IMPULSE TO TRUCK" if lang == "en" else "1. ИМПУЛЬС ВЫБИВАЕТ ПИКАП"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)

    t1_x = 270
    renderer.draw_2d_car(draw, t1_x, ground_y - 40, scale=1.1, color="#1e3a8a", outline="#60a5fa")
    
    imp_lbl = "Impulse J = F × dt" if lang == "en" else "Импульс J = F × dt"
    renderer.draw_vector(draw, (t1_x, ground_y - 10), (t1_x, ground_y - 130), color="#ef4444", width=6, label=imp_lbl, label_side="right")
    draw.text((t1_x, ground_y + 25), "Flatbed Truck (5,000 kg)" if lang == "en" else "Эвакуатор (5,000 кг)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # ПРАВАЯ КОЛОНКА (540px)
    col2_title = "2. STRATOSPHERE ORBIT FLIGHT" if lang == "en" else "2. ПОЛЕТ В СТРАТОСФЕРУ"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 25), "Ground Terrain" if lang == "en" else "Земля округа Хоуп", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Flying truck
    fly_x, fly_y = 820, 200
    renderer.draw_2d_car(draw, fly_x, fly_y, scale=0.9, color="#1e3a8a", outline="#60a5fa")

    v_lbl = "Velocity 450 km/h" if lang == "en" else "Скорость 450 км/ч"
    renderer.draw_vector(draw, (730, ground_y - 20), (fly_x - 30, fly_y + 20), color="#22c55e", width=6, label=v_lbl, label_side="left")

    space_lbl = "Hope County Spaceflight!" if lang == "en" else "Выход на околоземную орбиту!"
    draw.text((fly_x, fly_y - 45), space_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    # Bottom banner
    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#8b5cf6", width=2)
    bottom_lbl = "RESULT: Unresolved collision overlap accelerates the 5-ton truck into orbit" if lang == "en" else "ИТОГ: Неустранимое пересечение коллизий запускает 5-тонный пикап на орбиту"
    draw.text((540, 535), bottom_lbl, fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 2 Far Cry 5 ({lang}) сгенерирована: {out_path}")
def generate_scheme_farcry5_overlap(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Episode 5 Scheme 1: Far Cry 5 Double Overlap with Zero-Overlap standard."""
    img, draw = renderer.create_canvas()
    title_badge = "FAR CRY 5: DOUBLE COLLISION OVERLAP" if lang == "en" else "FAR CRY 5: ДВОЙНОЕ ЗАЩЕМЛЕНИЕ ТРУПА"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#38bdf8", border_color="#38bdf8")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 420

    # ЛЕВАЯ КОЛОНКА (540px)
    col1_title = "1. CORPSE CLAMPED IN VICE" if lang == "en" else "1. ЗАЩЕМЛЕНИЕ ТРУПА ВПРИТИРКУ"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")

    # Truck bed representation
    truck_box_y1, truck_box_y2 = 135, 230
    draw.rounded_rectangle([70, truck_box_y1, 470, truck_box_y2], radius=10, fill="#1e3a8a", outline="#60a5fa", width=2)
    truck_lbl = "TRUCK COLLIDER (5 TONS)" if lang == "en" else "КУЗОВ ПИКАПА (5 ТОНН)"
    draw.text((270, 180), truck_lbl, fill="#ffffff", font=renderer.font_bold, anchor="mm")

    # Ground
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)
    draw.text((120, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Ragdoll capsule caught between
    rag_cx, rag_cy = 270, 325
    renderer.draw_capsule_collider(draw, rag_cx, rag_cy, radius=32, height=140, color="#ef4444", fill="#7f1d1d66")
    corpse_lbl = "Ragdoll (Δx)" if lang == "en" else "Рэгдолл (Δx)"
    draw.text((rag_cx, rag_cy), corpse_lbl, fill="#fca5a5", font=renderer.font_bold, anchor="mm")

    renderer.draw_contact_point(draw, rag_cx, truck_box_y2, label="P1: Truck" if lang == "en" else "P1: Кузов", color="#ef4444", label_side="left")
    renderer.draw_contact_point(draw, rag_cx, ground_y, label="P2: Ground" if lang == "en" else "P2: Земля", color="#ef4444", label_side="right")

    # ПРАВАЯ КОЛОНКА (540px)
    col2_title = "2. DUAL REPULSION SPIKE" if lang == "en" else "2. ДВОЙНОЙ ВЫТАЛКИВАЮЩИЙ ИМПУЛЬС"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 20), "Terrain Ground" if lang == "en" else "Земля (Террейн)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Upward forces
    f1_lbl = "F1: Ground Push" if lang == "en" else "F1: От земли"
    renderer.draw_vector(draw, (730, ground_y - 10), (730, 260), color="#4ade80", width=5, label=f1_lbl, label_side="left")

    f2_lbl = "F2: Truck Reaction" if lang == "en" else "F2: Реакция опоры"
    renderer.draw_vector(draw, (890, ground_y - 10), (890, 260), color="#f59e0b", width=5, label=f2_lbl, label_side="right")

    # Net launch force
    f_net_lbl = "F_NET = F1 + F2 = MAX!" if lang == "en" else "F_ИТОГ = F1 + F2 (В КОСМОС!)"
    renderer.draw_vector(draw, (810, 250), (810, 130), color="#38bdf8", width=7, label=f_net_lbl, label_side="right")

    # Bottom banner
    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#38bdf8", width=2)
    bottom_lbl = "PHYSICS: Body wedged between two solids -> Solver sums upward repulsion forces" if lang == "en" else "ФИЗИКА: Труп зажат между двумя телами -> Движок суммирует силы выталкивания вверх"
    draw.text((540, 535), bottom_lbl, fill="#bae6fd", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 1 Far Cry 5 ({lang}) сгенерирована: {out_path}")


def generate_scheme_farcry5_launch(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Episode 5 Scheme 2: Far Cry 5 Launch to Orbit with Zero-Overlap standard."""
    img, draw = renderer.create_canvas()
    title_badge = "FAR CRY 5: SPACE PROGRAM CATAPULT" if lang == "en" else "FAR CRY 5: КОСМИЧЕСКАЯ ПРОГРАММА СЕКТАНТОВ"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 400

    # ЛЕВАЯ КОЛОНКА (540px)
    col1_title = "1. MASSIVE IMPULSE TO TRUCK" if lang == "en" else "1. ИМПУЛЬС ВЫБИВАЕТ ПИКАП"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)

    t1_x = 270
    renderer.draw_2d_car(draw, t1_x, ground_y - 40, scale=1.1, color="#1e3a8a", outline="#60a5fa")
    
    imp_lbl = "Impulse J = F × dt" if lang == "en" else "Импульс J = F × dt"
    renderer.draw_vector(draw, (t1_x, ground_y - 10), (t1_x, ground_y - 135), color="#ef4444", width=6, label=imp_lbl, label_side="right")
    draw.text((t1_x, ground_y + 25), "Flatbed Truck (5,000 kg)" if lang == "en" else "Эвакуатор (5,000 кг)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # ПРАВАЯ КОЛОНКА (540px)
    col2_title = "2. STRATOSPHERE ORBIT FLIGHT" if lang == "en" else "2. ПОЛЕТ В СТРАТОСФЕРУ"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 25), "Ground Terrain" if lang == "en" else "Земля округа Хоуп", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Flying truck
    fly_x, fly_y = 860, 180
    renderer.draw_2d_car(draw, fly_x, fly_y, scale=0.9, color="#1e3a8a", outline="#60a5fa")

    v_lbl = "Velocity 450 km/h" if lang == "en" else "Скорость 450 км/ч"
    renderer.draw_vector(draw, (690, ground_y - 15), (fly_x - 45, fly_y + 35), color="#22c55e", width=6, label=v_lbl, label_side="left")

    space_lbl = "Hope County Spaceflight!" if lang == "en" else "Выход на околоземную орбиту!"
    draw.text((fly_x, fly_y - 45), space_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    # Bottom banner
    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#8b5cf6", width=2)
    bottom_lbl = "RESULT: Unresolved collision overlap accelerates the 5-ton truck into orbit" if lang == "en" else "ИТОГ: Неустранимое пересечение коллизий запускает 5-тонный пикап на орбиту"
    draw.text((540, 535), bottom_lbl, fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 2 Far Cry 5 ({lang}) сгенерирована: {out_path}")
def generate_scheme_farcry5_launch(renderer: PhysicsDiagramRenderer, out_path: Path, lang: str = "ru"):
    """Episode 5 Scheme 2: Far Cry 5 Launch to Orbit with Zero-Overlap standard."""
    img, draw = renderer.create_canvas()
    title_badge = "FAR CRY 5: SPACE PROGRAM CATAPULT" if lang == "en" else "FAR CRY 5: КОСМИЧЕСКАЯ ПРОГРАММА СЕКТАНТОВ"
    renderer.draw_badge(draw, 40, 25, title_badge, bg_color="#0f172a", text_color="#a855f7", border_color="#c084fc")

    draw.line([(540, 80), (540, 470)], fill="#1e293b", width=2)
    ground_y = 400

    # ЛЕВАЯ КОЛОНКА (540px)
    col1_title = "1. MASSIVE IMPULSE TO TRUCK" if lang == "en" else "1. ИМПУЛЬС ВЫБИВАЕТ ПИКАП"
    draw.text((270, 85), col1_title, fill="#fb7185", font=renderer.font_bold, anchor="mm")
    draw.line([(60, ground_y), (480, ground_y)], fill="#64748b", width=3)

    t1_x = 270
    renderer.draw_2d_car(draw, t1_x, ground_y - 40, scale=1.1, color="#1e3a8a", outline="#60a5fa")
    
    imp_lbl = "Impulse J = F × dt" if lang == "en" else "Импульс J = F × dt"
    renderer.draw_vector(draw, (t1_x, ground_y - 10), (t1_x, ground_y - 135), color="#ef4444", width=6, label=imp_lbl, label_side="right")
    draw.text((t1_x, ground_y + 25), "Flatbed Truck (5,000 kg)" if lang == "en" else "Эвакуатор (5,000 кг)", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # ПРАВАЯ КОЛОНКА (540px)
    col2_title = "2. STRATOSPHERE ORBIT FLIGHT" if lang == "en" else "2. ПОЛЕТ В СТРАТОСФЕРУ"
    draw.text((810, 85), col2_title, fill="#4ade80", font=renderer.font_bold, anchor="mm")
    draw.line([(600, ground_y), (1020, ground_y)], fill="#64748b", width=3)
    draw.text((680, ground_y + 25), "Ground Terrain" if lang == "en" else "Земля округа Хоуп", fill="#94a3b8", font=renderer.font_regular, anchor="mm")

    # Flying truck
    fly_x, fly_y = 880, 175
    renderer.draw_2d_car(draw, fly_x, fly_y, scale=0.9, color="#1e3a8a", outline="#60a5fa")

    # Velocity vector with manual label on the side
    renderer.draw_vector(draw, (730, ground_y - 15), (fly_x - 45, fly_y + 35), color="#22c55e", width=6)
    v_lbl = "Velocity\n450 km/h" if lang == "en" else "Скорость\n450 км/ч"
    draw.text((680, 260), v_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm", align="center")

    space_lbl = "Hope County Spaceflight!" if lang == "en" else "Выход на околоземную орбиту!"
    draw.text((fly_x, fly_y - 45), space_lbl, fill="#4ade80", font=renderer.font_bold, anchor="mm")

    # Bottom banner
    draw.rounded_rectangle([40, 505, 1040, 565], radius=12, fill="#111827", outline="#8b5cf6", width=2)
    bottom_lbl = "RESULT: Unresolved collision overlap accelerates the 5-ton truck into orbit" if lang == "en" else "ИТОГ: Неустранимое пересечение коллизий запускает 5-тонный пикап на орбиту"
    draw.text((540, 535), bottom_lbl, fill="#ddd6fe", font=renderer.font_mono_bold, anchor="mm")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    img.save(str(out_path), "PNG")
    print(f"   ✓ Схема 2 Far Cry 5 ({lang}) сгенерирована: {out_path}")
