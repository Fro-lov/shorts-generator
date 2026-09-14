from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class Episode2VisualsGenerator:
    def __init__(self, width: int = 1000, height: int = 560):
        self.width = width
        self.height = height
        self.bg_color = "#0f172a"
        self.border_color = "#38bdf8"

        try:
            self.title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
            self.header_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
            self.body_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.code_bold = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 30)
            self.code_bold_large = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 34)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.code_bold = ImageFont.load_default()
            self.code_bold_large = ImageFont.load_default()

    def generate_step1_door(self, output_path: Path) -> Path:
        """Step 1: Door with infinite mass rotating."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline=self.border_color, width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "ШАГ 1: КИНЕМАТИЧЕСКАЯ ДВЕРЬ (МАССА = ∞)", fill="#38bdf8", font=self.title_font, anchor="mm")

        # Door (Left)
        draw.rounded_rectangle([100, 140, 240, 390], radius=12, fill="#475569", outline="#94a3b8", width=3)
        draw.text((170, 265), "ДВЕРЬ\n(Анимация)", fill="#f8fafc", font=self.header_font, anchor="mm", align="center")

        # Arrow rotation
        draw.polygon([(280, 265), (380, 215), (380, 315)], fill="#38bdf8")
        draw.text((450, 160), "ОТКРЫТИЕ СКРИПТОМ", fill="#38bdf8", font=self.header_font, anchor="mm")

        # NPC (Right)
        draw.rounded_rectangle([620, 160, 880, 370], radius=16, fill="#ea580c", outline="#fdba74", width=3)
        draw.text((750, 265), "БЕГУЩИЙ NPC\n(100 HP)", fill="#ffffff", font=self.title_font, anchor="mm", align="center")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 430, self.width - 40, 520], radius=14, fill="#1e1e2e", outline="#38bdf8", width=2)
        draw.text((self.width // 2, 475), "Дверь двигалась скриптом, игнорируя физику и препятствия!", fill="#bae6fd", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_step2_impact(self, output_path: Path) -> Path:
        """Step 2: Massive physics impulse kills NPC instantly."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline="#f43f5e", width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "ШАГ 2: СМЕРТЕЛЬНЫЙ ИМПУЛЬС (УРОН: 9999)", fill="#fb7185", font=self.title_font, anchor="mm")

        # Visual impact
        draw.rounded_rectangle([100, 160, 480, 370], radius=16, fill="#e11d48", outline="#fecdd3", width=3)
        draw.text((290, 265), "УДАР СТВОРКОЙ\n(ИМПУЛЬС x1000)", fill="#ffffff", font=self.header_font, anchor="mm", align="center")

        # Arrow
        draw.polygon([(520, 265), (620, 215), (620, 315)], fill="#ef4444")

        # Dead NPC box
        draw.rounded_rectangle([660, 200, 920, 330], radius=16, fill="#311b24", outline="#f38ba8", width=3)
        draw.text((790, 265), "NPC ПОГИБ\n(0 HP / РАГДОЛЛ)", fill="#f38ba8", font=self.header_font, anchor="mm", align="center")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 430, self.width - 40, 520], radius=14, fill="#1e1e2e", outline="#f43f5e", width=2)
        draw.text((self.width // 2, 475), "Движок посчитал касание двери как таран грузовиком!", fill="#fecdd3", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_door_fix_card(self, output_path: Path) -> Path:
        """Step 3: Clear and funny pseudo-code fix card."""
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

        draw.text((120, 18), "ЛОГИКА ФИКСА КОЛЛИЗИИ ДВЕРЕЙ", fill="#cdd6f4", font=self.header_font)

        # 1. Bug Box (Red)
        bug_y1, bug_y2 = 85, 305
        draw.rounded_rectangle([30, bug_y1, self.width - 30, bug_y2], radius=16, fill="#311b24", outline="#f38ba8", width=2)
        draw.rounded_rectangle([50, bug_y1 + 15, 290, bug_y1 + 55], radius=8, fill="#f38ba8")
        draw.text((170, bug_y1 + 35), "[-] НЕПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, bug_y1 + 75), "урон_от_двери = скорость * масса;", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, bug_y1 + 140), "// Упс: масса двери бесконечна -> 99999 урона!", fill="#fca5a5", font=self.body_font)

        # 2. Fix Box (Green)
        fix_y1, fix_y2 = 330, 550
        draw.rounded_rectangle([30, fix_y1, self.width - 30, fix_y2], radius=16, fill="#162d22", outline="#a6e3a1", width=2)
        draw.rounded_rectangle([50, fix_y1 + 15, 260, fix_y1 + 55], radius=8, fill="#a6e3a1")
        draw.text((155, fix_y1 + 35), "[+] ПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, fix_y1 + 75), "урон_от_двери = 0;", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, fix_y1 + 130), "дверь.просто_толкает(персонаж);", fill="#a6e3a1", font=self.code_bold_large)

        img.save(output_path, "PNG")
        return output_path
