import io
import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT, FPS


def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3)


def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    x = max(0.0, min(1.0, x))
    return 1.0 + c3 * math.pow(x - 1.0, 3) + c1 * math.pow(x - 1.0, 2)


class Episode6VisualsGenerator:
    def __init__(self, lang: str = "ru", width: int = 1000, height: int = 540, fps: int = FPS):
        self.lang = lang.lower()
        self.width = width
        self.height = height
        self.fps = fps

        # Fonts setup
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
            self.font_subtitle = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
            self.font_counter = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 62)
            self.font_mono = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 28)
            self.font_mono_small = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 22)
            self.font_regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
            self.font_bold = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_badge = ImageFont.load_default()
            self.font_counter = ImageFont.load_default()
            self.font_mono = ImageFont.load_default()
            self.font_mono_small = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()
            self.font_bold = ImageFont.load_default()

    def draw_grid_background(self, draw: ImageDraw.ImageDraw, x1, y1, x2, y2, step=40):
        for x in range(x1, x2, step):
            draw.line([(x, y1), (x, y2)], fill="#111c35", width=1)
        for y in range(y1, y2, step):
            draw.line([(x1, y), (x2, y)], fill="#111c35", width=1)

    def draw_rounded_card(self, draw: ImageDraw.ImageDraw, x1, y1, x2, y2, radius=26, fill="#0b1329ee", outline="#38bdf855", width=2):
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

    def draw_badge(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color: str = "#0f172a", text_color: str = "#38bdf8", border_color: str = "#0ea5e9"):
        bbox = draw.textbbox((x + 14, y + 6), text, font=self.font_badge)
        draw.rounded_rectangle([x, y, bbox[2] + 14, bbox[3] + 6], radius=8, fill=bg_color, outline=border_color, width=2)
        draw.text((x + 14, y + 6), text, fill=text_color, font=self.font_badge)

    def generate_scheme1_axis_swap(self, output_path: Path) -> Path:
        """
        Scheme 1: Coordinate Axis Swap (Pitch Roll vs Vertical Yaw)
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background card with CAD grid
        self.draw_rounded_card(draw, 10, 10, self.width - 10, self.height - 10, radius=26, fill="#070c1dee", outline="#38bdf866", width=2)
        self.draw_grid_background(draw, 20, 20, self.width - 20, self.height - 20, step=35)

        badge_txt = "СХЕМА 1: СБОЙ МАТРИЦЫ ПОВОРОТА" if self.lang == "ru" else "SCHEME 1: ROTATION MATRIX BUG"
        title_txt = "Смена осей: Pitch (качение) на Yaw (рыскание)" if self.lang == "ru" else "Axis Swap: Pitch (Roll) to Yaw (Spin)"
        self.draw_badge(draw, 40, 30, badge_txt, bg_color="#0f172a", text_color="#38bdf8", border_color="#0284c7")
        draw.text((40, 75), title_txt, fill="#ffffff", font=self.font_title)

        # Left area: Normal Wheel with Pitch axis (Green)
        # Right area: Bugged Wheel spinning on Yaw axis (Red / Orange)
        cx_norm = 250
        cy_norm = 255

        cx_bug = 750
        cy_bug = 255

        # Separator line
        draw.line([(self.width // 2, 130), (self.width // 2, 440)], fill="#1e293b", width=2)

        # --- LEFT: NORMAL WHEEL (PITCH) ---
        draw.text((cx_norm, 135), "НОРМА (Ось X: Pitch)" if self.lang == "ru" else "NORMAL (X-Axis: Pitch)", fill="#4ade80", font=self.font_badge, anchor="mm")
        
        # Vertical tyre silhouette
        draw.rounded_rectangle([cx_norm - 40, cy_norm - 85, cx_norm + 40, cy_norm + 85], radius=16, fill="#1e293b", outline="#22c55e", width=3)
        # Hub center
        draw.ellipse([cx_norm - 14, cy_norm - 14, cx_norm + 14, cy_norm + 14], fill="#22c55e")
        # Horizontal Rotation axis (Pitch)
        draw.line([(cx_norm - 95, cy_norm), (cx_norm + 95, cy_norm)], fill="#86efac", width=4)
        draw.polygon([(cx_norm + 105, cy_norm), (cx_norm + 90, cy_norm - 8), (cx_norm + 90, cy_norm + 8)], fill="#86efac")
        draw.text((cx_norm, cy_norm + 105), "Вращение качения" if self.lang == "ru" else "Forward Rolling", fill="#94a3b8", font=self.font_mono_small, anchor="mm")

        # --- RIGHT: BUGGED WHEEL (YAW / PROPELLER) ---
        draw.text((cx_bug, 135), "БАГ (Ось Y: Yaw)" if self.lang == "ru" else "GLITCH (Y-Axis: Yaw)", fill="#f87171", font=self.font_badge, anchor="mm")
        
        # Horizontal tyre silhouette (spinning flat)
        draw.rounded_rectangle([cx_bug - 85, cy_bug - 30, cx_bug + 85, cy_bug + 30], radius=12, fill="#27141e", outline="#ef4444", width=3)
        
        # Hub center
        draw.ellipse([cx_bug - 14, cy_bug - 14, cx_bug + 14, cy_bug + 14], fill="#ef4444")
        # Vertical Rotation axis (Yaw)
        draw.line([(cx_bug, cy_bug - 85), (cx_bug, cy_bug + 85)], fill="#f87171", width=4)
        draw.polygon([(cx_bug, cy_bug - 95), (cx_bug - 8, cy_bug - 80), (cx_bug + 8, cy_bug - 80)], fill="#f87171")

        # Spinning blades arc
        draw.arc([cx_bug - 110, cy_bug - 45, cx_bug + 110, cy_bug + 45], start=0, end=360, fill="#f59e0b", width=2)
        draw.text((cx_bug, cy_bug + 105), "РЕЖИМ ВЕРТОЛЕТА" if self.lang == "ru" else "HELICOPTER MODE", fill="#fca5a5", font=self.font_mono_small, anchor="mm")

        # Bottom summary rule
        foot_txt = "ПРИНЦИП: Угловая скорость колеса применилась к вертикальной оси" if self.lang == "ru" else "RULE: Wheel angular velocity applied to vertical axis instead"
        draw.rounded_rectangle([40, 460, self.width - 40, 510], radius=8, fill="#0f172a", outline="#0284c7")
        draw.text((self.width // 2, 485), foot_txt, fill="#38bdf8", font=self.font_regular, anchor="mm")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path

    def generate_scheme2_physics_vs_visual(self, output_path: Path) -> Path:
        """
        Scheme 2: Physics Raycast (100% Grip) vs Visual Render (3500 RPM)
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background card with CAD grid
        self.draw_rounded_card(draw, 10, 10, self.width - 10, self.height - 10, radius=26, fill="#070c1dee", outline="#a855f766", width=2)
        self.draw_grid_background(draw, 20, 20, self.width - 20, self.height - 20, step=35)

        badge_txt = "СХЕМА 2: ФИЗИКА VS ВИЗУАЛ" if self.lang == "ru" else "SCHEME 2: PHYSICS VS VISUAL"
        title_txt = "Двойные стандарты игрового движка" if self.lang == "ru" else "Game Engine Dual Standards"
        self.draw_badge(draw, 40, 30, badge_txt, bg_color="#0f172a", text_color="#c084fc", border_color="#9333ea")
        draw.text((40, 75), title_txt, fill="#ffffff", font=self.font_title)

        # Box 1: Physics Engine State (Green Box)
        box1_x1, box1_y1 = 40, 130
        box1_x2, box1_y2 = self.width // 2 - 15, 440
        draw.rounded_rectangle([box1_x1, box1_y1, box1_x2, box1_y2], radius=16, fill="#052e16cc", outline="#22c55e", width=2)
        draw.text(((box1_x1 + box1_x2) // 2, box1_y1 + 30), "ФИЗИКА (Raycast Collider)" if self.lang == "ru" else "PHYSICS (Raycast Collider)", fill="#86efac", font=self.font_badge, anchor="mm")
        
        # Grip status
        draw.text(((box1_x1 + box1_x2) // 2, box1_y1 + 95), "GRIP: 100%", fill="#4ade80", font=self.font_counter, anchor="mm")
        draw.text(((box1_x1 + box1_x2) // 2, box1_y1 + 160), "Сцепление: ИДЕАЛЬНОЕ" if self.lang == "ru" else "Traction: PERFECT", fill="#bbf7d0", font=self.font_mono_small, anchor="mm")
        draw.text(((box1_x1 + box1_x2) // 2, box1_y1 + 205), "Управляемость: 100%" if self.lang == "ru" else "Steering: 100% OK", fill="#86efac", font=self.font_mono_small, anchor="mm")
        draw.text(((box1_x1 + box1_x2) // 2, box1_y1 + 245), "Raycast.Hit: TrackSurface" if self.lang == "ru" else "Raycast.Hit: TrackSurface", fill="#6ee7b7", font=self.font_mono_small, anchor="mm")

        # Box 2: Visual Mesh State (Red Box)
        box2_x1, box2_y1 = self.width // 2 + 15, 130
        box2_x2, box2_y2 = self.width - 40, 440
        draw.rounded_rectangle([box2_x1, box2_y1, box2_x2, box2_y2], radius=16, fill="#3b0712cc", outline="#ef4444", width=2)
        draw.text(((box2_x1 + box2_x2) // 2, box2_y1 + 30), "ВИЗУАЛ (Mesh Render)" if self.lang == "ru" else "VISUAL (Mesh Render)", fill="#fca5a5", font=self.font_badge, anchor="mm")

        # RPM counter
        draw.text(((box2_x1 + box2_x2) // 2, box2_y1 + 95), "3 500 RPM", fill="#f87171", font=self.font_counter, anchor="mm")
        draw.text(((box2_x1 + box2_x2) // 2, box2_y1 + 160), "Положение: ПЛАШМЯ" if self.lang == "ru" else "Orientation: FLAT", fill="#fecaca", font=self.font_mono_small, anchor="mm")
        draw.text(((box2_x1 + box2_x2) // 2, box2_y1 + 205), "Режим: ВЕРТОЛЕТ" if self.lang == "ru" else "Mode: PROPELLER", fill="#f87171", font=self.font_mono_small, anchor="mm")
        draw.text(((box2_x1 + box2_x2) // 2, box2_y1 + 245), "Mesh.Euler: (90°, Yaw, 0°)", fill="#fda4af", font=self.font_mono_small, anchor="mm")

        # Bottom summary rule
        foot_txt = "ИТОГ: Физика едет вперед, пока графика нарезает воздух" if self.lang == "ru" else "SUMMARY: Physics drives straight while mesh cuts the air"
        draw.rounded_rectangle([40, 460, self.width - 40, 510], radius=8, fill="#0f172a", outline="#9333ea")
        draw.text((self.width // 2, 485), foot_txt, fill="#c084fc", font=self.font_regular, anchor="mm")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path

    def generate_fix_card(self, output_path: Path) -> Path:
        """
        Scheme 3: Code Fix Terminal
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background card
        self.draw_rounded_card(draw, 10, 10, self.width - 10, self.height - 10, radius=26, fill="#090d16ee", outline="#22c55e66", width=2)
        self.draw_grid_background(draw, 20, 20, self.width - 20, self.height - 20, step=35)

        badge_txt = "ФИКС В КОДЕ" if self.lang == "ru" else "CODE FIX"
        title_txt = "Разделение осей в матрице трансформации" if self.lang == "ru" else "Decoupling Transformation Matrix Axes"
        self.draw_badge(draw, 40, 30, badge_txt, bg_color="#0f172a", text_color="#4ade80", border_color="#16a34a")
        draw.text((40, 75), title_txt, fill="#ffffff", font=self.font_title)

        # Terminal Box
        term_x1 = 40
        term_x2 = self.width - 40
        term_y1 = 130
        term_y2 = 440
        draw.rounded_rectangle([term_x1, term_y1, term_x2, term_y2], radius=16, fill="#040711", outline="#1e293b", width=2)

        # Window Dots
        draw.ellipse([term_x1 + 20, term_y1 + 18, term_x1 + 34, term_y1 + 32], fill="#ef4444")
        draw.ellipse([term_x1 + 44, term_y1 + 18, term_x1 + 58, term_y1 + 32], fill="#f59e0b")
        draw.ellipse([term_x1 + 68, term_y1 + 18, term_x1 + 82, term_y1 + 32], fill="#22c55e")
        draw.text((term_x1 + 105, term_y1 + 25), "WheelController.cpp", fill="#64748b", font=self.font_mono_small, anchor="lm")

        # Wrong Code Block
        draw.rounded_rectangle([term_x1 + 20, term_y1 + 50, term_x2 - 20, term_y1 + 130], radius=10, fill="#7f1d1d33", outline="#ef444466", width=1)
        draw.text((term_x1 + 35, term_y1 + 75), "[-] wheelMesh.localRotation =", fill="#f87171", font=self.font_mono, anchor="lm")
        draw.text((term_x1 + 65, term_y1 + 105), "Euler(0.0f, roll_omega * dt, 0.0f); // BUG: Yaw!", fill="#fca5a5", font=self.font_mono_small, anchor="lm")

        # Fixed Code Block (Glows green)
        draw.rounded_rectangle([term_x1 + 20, term_y1 + 150, term_x2 - 20, term_y1 + 230], radius=10, fill="#14532d44", outline="#22c55e", width=2)
        draw.text((term_x1 + 35, term_y1 + 175), "[+] wheelMesh.localRotation =", fill="#4ade80", font=self.font_mono, anchor="lm")
        draw.text((term_x1 + 65, term_y1 + 205), "Euler(roll_omega * dt, steerAngle, 0.0f); // OK: Pitch", fill="#86efac", font=self.font_mono_small, anchor="lm")

        # Bottom summary rule
        foot_txt = "РЕЗУЛЬТАТ: Колесо снова катится ровно по асфальту" if self.lang == "ru" else "RESULT: Wheel stays on tarmac and rolls forward"
        draw.rounded_rectangle([40, 460, self.width - 40, 510], radius=8, fill="#0f172a", outline="#22c55e")
        draw.text((self.width // 2, 485), foot_txt, fill="#4ade80", font=self.font_regular, anchor="mm")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")
        return output_path
