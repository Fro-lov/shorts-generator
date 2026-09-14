from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class SimplifiedVisualsGenerator:
    def __init__(self, width: int = 1000, height: int = 560):
        self.width = width
        self.height = height
        self.bg_color = "#0f172a"
        self.border_color = "#38bdf8"

        try:
            self.title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
            self.header_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
            self.body_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.sub_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
            self.code_bold = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 30)
            self.code_bold_large = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 34)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.sub_font = ImageFont.load_default()
            self.code_bold = ImageFont.load_default()
            self.code_bold_large = ImageFont.load_default()

    def generate_step1_penetration(self, output_path: Path) -> Path:
        """Card 1: High speed collision and wall penetration."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline=self.border_color, width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "ШАГ 1: ПРОНИКНОВЕНИЕ СКВОЗЬ СТЕНУ", fill="#38bdf8", font=self.title_font, anchor="mm")

        # Visual: Car (Blue) crashing into Wall (Grey)
        # Wall (Right side)
        wall_x1, wall_y1, wall_x2, wall_y2 = 680, 110, 940, 400
        draw.rounded_rectangle([wall_x1, wall_y1, wall_x2, wall_y2], radius=16, fill="#334155", outline="#64748b", width=3)
        draw.text((845, (wall_y1 + wall_y2) // 2), "СТЕНА\n(Коллизия)", fill="#f8fafc", font=self.header_font, anchor="mm", align="center")

        # Car (Left side into wall)
        car_x1, car_y1, car_x2, car_y2 = 60, 160, 750, 350
        draw.rounded_rectangle([car_x1, car_y1, car_x2, car_y2], radius=16, fill="#1d4ed8", outline="#60a5fa", width=3)
        draw.text(((car_x1 + 680) // 2, (car_y1 + car_y2) // 2), "3D МАШИНА", fill="#ffffff", font=self.title_font, anchor="mm")

        # Penetration Zone (Overlap between Car and Wall: 680 to 750)
        draw.rounded_rectangle([680, 160, 750, 350], radius=6, fill="#ef4444", outline="#f87171", width=2)
        draw.text((715, 255), "УДАР", fill="#ffffff", font=self.body_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 430, self.width - 40, 520], radius=14, fill="#1e1e2e", outline="#ef4444", width=2)
        draw.text((self.width // 2, 475), "Из-за высокой скорости меш влетел прямо внутрь стены!", fill="#fca5a5", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_step2_collapse(self, output_path: Path) -> Path:
        """Card 2: Z-axis squash to zero."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline="#f43f5e", width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "ШАГ 2: СХЛОПЫВАНИЕ В БЛИН (Z = 0)", fill="#fb7185", font=self.title_font, anchor="mm")

        # Top Force text & Arrows
        draw.text((self.width // 2, 120), "СИЛА ДЕФОРМАЦИИ СЖИМАЕТ КУЗОВ", fill="#f43f5e", font=self.header_font, anchor="mm")
        # Draw clean down-arrows
        for ax in [250, 500, 750]:
            draw.polygon([(ax - 16, 150), (ax + 16, 150), (ax, 180)], fill="#f43f5e")

        # Flattened flat line car
        flat_x1, flat_y1, flat_x2, flat_y2 = 80, 220, self.width - 80, 280
        draw.rounded_rectangle([flat_x1, flat_y1, flat_x2, flat_y2], radius=10, fill="#e11d48", outline="#fecdd3", width=3)
        draw.text((self.width // 2, 250), "ВЫСОТА Z = 0 (МАШИНА СТАЛА ПЛОСКИМ КОВРИКОМ)", fill="#ffffff", font=self.header_font, anchor="mm")

        # Draw clean up-arrows
        for ax in [250, 500, 750]:
            draw.polygon([(ax - 16, 350), (ax + 16, 350), (ax, 320)], fill="#f43f5e")
        draw.text((self.width // 2, 380), "ОШИБКА ВЫТАЛКИВАНИЯ ВЕРШИН", fill="#f43f5e", font=self.header_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 430, self.width - 40, 520], radius=14, fill="#1e1e2e", outline="#f43f5e", width=2)
        draw.text((self.width // 2, 475), "Формула деформации умножила толщину на ноль!", fill="#fecdd3", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_simple_fix_card(self, output_path: Path) -> Path:
        """Card 3: Fun, clear, simple pseudo-code bug/fix comparison."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        card_height = 580
        img = Image.new("RGBA", (self.width, card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, card_height], radius=24, fill="#181825", outline="#45475a", width=3)

        # Header Bar with mac dots
        draw.rounded_rectangle([0, 0, self.width, 64], radius=24, fill="#11111b")
        draw.rectangle([0, 36, self.width, 64], fill="#11111b")

        dots = [(30, 32, "#f38ba8"), (58, 32, "#f9e2af"), (86, 32, "#a6e3a1")]
        for dx, dy, col in dots:
            draw.ellipse([dx - 8, dy - 8, dx + 8, dy + 8], fill=col)

        draw.text((120, 18), "ЛОГИКА РАБОТЫ ФИКСА В КОДЕ", fill="#cdd6f4", font=self.header_font)

        # 1. Bug Box (Red)
        bug_y1, bug_y2 = 85, 305
        draw.rounded_rectangle([30, bug_y1, self.width - 30, bug_y2], radius=16, fill="#311b24", outline="#f38ba8", width=2)
        # Bug badge
        draw.rounded_rectangle([50, bug_y1 + 15, 290, bug_y1 + 55], radius=8, fill="#f38ba8")
        draw.text((170, bug_y1 + 35), "[-] НЕПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, bug_y1 + 75), "высота = (1.0 - сила_удара)", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, bug_y1 + 140), "// При сильном ударе высота стала = 0!", fill="#fca5a5", font=self.body_font)

        # 2. Fix Box (Green)
        fix_y1, fix_y2 = 330, 550
        draw.rounded_rectangle([30, fix_y1, self.width - 30, fix_y2], radius=16, fill="#162d22", outline="#a6e3a1", width=2)
        # Fix badge
        draw.rounded_rectangle([50, fix_y1 + 15, 260, fix_y1 + 55], radius=8, fill="#a6e3a1")
        draw.text((155, fix_y1 + 35), "[+] ПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, fix_y1 + 75), "высота = (1.0 - сила_удара),", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, fix_y1 + 130), "НО НЕ МЕНЬШЕ 0.5 (ОГРАНИЧИТЕЛЬ!)", fill="#a6e3a1", font=self.code_bold_large)

        img.save(output_path, "PNG")
        return output_path
