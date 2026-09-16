from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class Episode4VisualsGenerator:
    def __init__(self, width: int = 1000, height: int = 560):
        self.width = width
        self.height = height
        self.bg_color = "#0f172a"
        self.border_color = "#38bdf8"

        try:
            self.title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
            self.header_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.body_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 23)
            self.sub_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 21)
            self.code_bold = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 28)
            self.code_bold_large = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 32)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.sub_font = ImageFont.load_default()
            self.code_bold = ImageFont.load_default()
            self.code_bold_large = ImageFont.load_default()

    def generate_chair_anatomy(self, output_path: Path) -> Path:
        """Card 1: Anatomy of chair - 2 rigidbodies connected by a joint."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline=self.border_color, width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "АНАТОМИЯ СТУЛА: ДВА ФИЗИЧЕСКИХ ТЕЛА", fill="#38bdf8", font=self.title_font, anchor="mm")

        # Upper Body (Seat + Backrest)
        seat_x1, seat_y1, seat_x2, seat_y2 = 60, 95, self.width - 60, 205
        draw.rounded_rectangle([seat_x1, seat_y1, seat_x2, seat_y2], radius=16, fill="#1e3a8a", outline="#60a5fa", width=3)
        draw.text((self.width // 2, 130), "[ ТЕЛО #1: СИДЕНЬЕ И СПИНКА ]", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 170), "Отдельный Rigidbody с собственной массой и физикой", fill="#93c5fd", font=self.sub_font, anchor="mm")

        # Middle Joint Spring Link (Full width container)
        joint_y1, joint_y2 = 220, 290
        draw.rounded_rectangle([100, joint_y1, self.width - 100, joint_y2], radius=12, fill="#1e293b", outline="#fbbf24", width=2)
        draw.text((self.width // 2, (joint_y1 + joint_y2) // 2), "--- СВЯЗКА (ДЖОЙНТ / ФИЗИЧЕСКИЙ ШАРНИР) ---", fill="#fbbf24", font=self.header_font, anchor="mm")

        # Lower Body (Base + Wheels)
        base_x1, base_y1, base_x2, base_y2 = 60, 305, self.width - 60, 415
        draw.rounded_rectangle([base_x1, base_y1, base_x2, base_y2], radius=16, fill="#14532d", outline="#4ade80", width=3)
        draw.text((self.width // 2, 340), "[ ТЕЛО #2: КРЕСТОВИНА И КОЛЁСИКИ ]", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 380), "Отдельный Rigidbody для катания по полу", fill="#86efac", font=self.sub_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 440, self.width - 40, 525], radius=14, fill="#1e1e2e", outline="#38bdf8", width=2)
        draw.text((self.width // 2, 482), "В коде стул собран из двух независимых тел, связанных джойнтом!", fill="#bae6fd", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_chair_chaos(self, output_path: Path) -> Path:
        """Card 2: Endless conflict loop - repulsion vs spring snap."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline="#f43f5e", width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "ФИЗИЧЕСКИЙ ВЕЧНЫЙ ДВИГАТЕЛЬ (ХАОС)", fill="#fb7185", font=self.title_font, anchor="mm")

        # Step A: Push Out (Collision Repulsion)
        draw.rounded_rectangle([40, 95, 470, 285], radius=16, fill="#311b24", outline="#f43f5e", width=2)
        draw.text((255, 125), "1. СТОЛКНОВЕНИЕ", fill="#f87171", font=self.header_font, anchor="mm")
        draw.text((255, 168), "Коллайдеры врезались!", fill="#ffffff", font=self.body_font, anchor="mm")
        draw.text((255, 205), "Силы отталкивания", fill="#fca5a5", font=self.sub_font, anchor="mm")
        draw.text((255, 245), "<-- ТОЛКАЮТ НАРУЖУ -->", fill="#f43f5e", font=self.header_font, anchor="mm")

        # VS / Transition Arrow in center
        draw.text((self.width // 2, 190), "<==>", fill="#fbbf24", font=self.title_font, anchor="mm")

        # Step B: Snap Back (Joint Spring)
        draw.rounded_rectangle([530, 95, 960, 285], radius=16, fill="#1c1917", outline="#fbbf24", width=2)
        draw.text((745, 125), "2. РЫВОК ДЖОЙНТА", fill="#fbbf24", font=self.header_font, anchor="mm")
        draw.text((745, 168), "Связка натянулась!", fill="#ffffff", font=self.body_font, anchor="mm")
        draw.text((745, 205), "Пружина джойнта", fill="#fef08a", font=self.sub_font, anchor="mm")
        draw.text((745, 245), ">-- ТЯНЕТ ОБРАТНО --<", fill="#fbbf24", font=self.header_font, anchor="mm")

        # Result Big Bar (Overclocked Flight)
        draw.rounded_rectangle([40, 305, self.width - 40, 415], radius=14, fill="#450a0a", outline="#ef4444", width=3)
        draw.text((self.width // 2, 342), "ИТОГ: ЗАМКНУТЫЙ ЦИКЛ = БЕСКОНЕЧНАЯ ЭНЕРГИЯ", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 382), "Стул разрывает на куски и запускает в режим вертолета!", fill="#fca5a5", font=self.body_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 440, self.width - 40, 525], radius=14, fill="#1e1e2e", outline="#f43f5e", width=2)
        draw.text((self.width // 2, 482), "Удар -> Отталкивание -> Рывок связки -> Повтор 60 раз в секунду!", fill="#fecdd3", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_chair_fix_card(self, output_path: Path) -> Path:
        """Card 3: Clear, fun pseudo-code bug/fix comparison."""
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

        draw.text((60, bug_y1 + 75), "Тело1.драться_с(Тело2) = TRUE;", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, bug_y1 + 135), "// Стул атакует сам себя и улетает в космос", fill="#fca5a5", font=self.body_font)

        # 2. Fix Box (Green)
        fix_y1, fix_y2 = 330, 550
        draw.rounded_rectangle([30, fix_y1, self.width - 30, fix_y2], radius=16, fill="#162d22", outline="#a6e3a1", width=2)
        # Fix badge
        draw.rounded_rectangle([50, fix_y1 + 15, 260, fix_y1 + 55], radius=8, fill="#a6e3a1")
        draw.text((155, fix_y1 + 35), "[+] ПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, fix_y1 + 75), "физика.игнорировать_коллизию(Тело1, Тело2);", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, fix_y1 + 135), "// Отключаем взаимный урон: стул спокоен и стабилен", fill="#a6e3a1", font=self.body_font)

        img.save(output_path, "PNG")
        return output_path
