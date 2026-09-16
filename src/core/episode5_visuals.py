from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class Episode5VisualsGenerator:
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
            self.code_bold_large = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 31)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.sub_font = ImageFont.load_default()
            self.code_bold = ImageFont.load_default()
            self.code_bold_large = ImageFont.load_default()

    def frame_meme(self, meme_input_path: Path, output_path: Path, title_text: str = "") -> Path:
        """Puts a meme into a nice high-contrast card frame suitable for 9:16 layout."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        card_h = 600
        img = Image.new("RGBA", (self.width, card_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, card_h], radius=24, fill=self.bg_color, outline=self.border_color, width=3)

        top_offset = 12
        if title_text:
            draw.rounded_rectangle([0, 0, self.width, 60], radius=24, fill="#1e293b")
            draw.rectangle([0, 36, self.width, 60], fill="#1e293b")
            draw.text((self.width // 2, 30), title_text, fill="#38bdf8", font=self.header_font, anchor="mm")
            top_offset = 68

        # Load meme image
        raw_meme = Image.open(meme_input_path).convert("RGBA")
        avail_w = self.width - 32
        avail_h = card_h - top_offset - 16

        # Scale keeping aspect ratio
        raw_w, raw_h = raw_meme.size
        scale = min(avail_w / raw_w, avail_h / raw_h)
        new_w = int(raw_w * scale)
        new_h = int(raw_h * scale)
        resized_meme = raw_meme.resize((new_w, new_h), Image.Resampling.LANCZOS)

        pos_x = (self.width - new_w) // 2
        pos_y = top_offset + (avail_h - new_h) // 2
        img.paste(resized_meme, (pos_x, pos_y), resized_meme if resized_meme.mode == "RGBA" else None)

        img.save(output_path, "PNG")
        return output_path

    def generate_overlap_diagram(self, output_path: Path) -> Path:
        """Card 1: Double Overlap (Corpse clamped between Truck and Ground)."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline=self.border_color, width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "СХЕМА #1: ДВОЙНОЕ ЗАЩЕМЛЕНИЕ ТРУПА", fill="#38bdf8", font=self.title_font, anchor="mm")

        # Top Object: Truck Collider
        truck_y1, truck_y2 = 95, 195
        draw.rounded_rectangle([60, truck_y1, self.width - 60, truck_y2], radius=16, fill="#1e3a8a", outline="#60a5fa", width=3)
        draw.text((self.width // 2, 130), "[ ОБЪЕКТ #1: КОЛЛИЗИЯ ГРУЗОВИКА (5 ТОНН) ]", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 168), "Массивное твердое тело с активной подвеской", fill="#93c5fd", font=self.sub_font, anchor="mm")

        # Middle Intersected Object: Corpse Ragdoll
        corpse_y1, corpse_y2 = 215, 315
        draw.rounded_rectangle([100, corpse_y1, self.width - 100, corpse_y2], radius=16, fill="#7f1d1d", outline="#ef4444", width=3)
        draw.text((self.width // 2, 248), "--> ТРУП КУЛЬТИСТА (ВКЛЮЧИЛСЯ РЭГДОЛЛ) <--", fill="#fca5a5", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 285), "! Заспавнился ВНУТРИ геометрии кузова и земли одновременно !", fill="#ffffff", font=self.sub_font, anchor="mm")

        # Bottom Object: Ground Collider
        ground_y1, ground_y2 = 335, 435
        draw.rounded_rectangle([60, ground_y1, self.width - 60, ground_y2], radius=16, fill="#14532d", outline="#4ade80", width=3)
        draw.text((self.width // 2, 370), "[ ОБЪЕКТ #2: МОНОЛИТНАЯ ЗЕМЛЯ (СТАТИКА) ]", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 408), "Неподвижный меш террейна с бесконечной массой", fill="#86efac", font=self.sub_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 455, self.width - 40, 535], radius=14, fill="#1e1e2e", outline="#38bdf8", width=2)
        draw.text((self.width // 2, 495), "Труп зажат как в прессе: два коллайдера сжимают его с двух сторон!", fill="#bae6fd", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_impulse_diagram(self, output_path: Path) -> Path:
        """Card 2: Penetration Resolution Impulse Spike Launch."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Base Card
        draw.rounded_rectangle([0, 0, self.width, self.height], radius=24, fill=self.bg_color, outline="#f43f5e", width=3)

        # Header Bar
        draw.rounded_rectangle([0, 0, self.width, 70], radius=24, fill="#1e293b")
        draw.rectangle([0, 40, self.width, 70], fill="#1e293b")
        draw.text((self.width // 2, 35), "СХЕМА #2: КОСМИЧЕСКИЙ ВЫТАЛКИВАЮЩИЙ ИМПУЛЬС", fill="#fb7185", font=self.title_font, anchor="mm")

        # Left Column: Ground push up
        draw.rounded_rectangle([40, 95, 470, 290], radius=16, fill="#162d22", outline="#4ade80", width=2)
        draw.text((255, 125), "СИЛА #1: ОТ ЗЕМЛИ", fill="#4ade80", font=self.header_font, anchor="mm")
        draw.text((255, 168), "Земля толкает труп ВВЕРХ", fill="#ffffff", font=self.body_font, anchor="mm")
        draw.text((255, 205), "Землю сдвинуть нельзя,", fill="#86efac", font=self.sub_font, anchor="mm")
        draw.text((255, 245), "^^^ ВЕКТОР ВВЕРХ ^^^", fill="#4ade80", font=self.header_font, anchor="mm")

        # Plus in center
        draw.text((self.width // 2, 192), "+", fill="#fbbf24", font=self.title_font, anchor="mm")

        # Right Column: Truck push down
        draw.rounded_rectangle([530, 95, 960, 290], radius=16, fill="#311b24", outline="#f43f5e", width=2)
        draw.text((745, 125), "СИЛА #2: ОТ КУЗОВА", fill="#f87171", font=self.header_font, anchor="mm")
        draw.text((745, 168), "Кузов отталкивает труп", fill="#ffffff", font=self.body_font, anchor="mm")
        draw.text((745, 205), "Но труп упёрся в землю!", fill="#fca5a5", font=self.sub_font, anchor="mm")
        draw.text((745, 245), "!!! РЕАКЦИЯ ОПОРЫ !!!", fill="#f43f5e", font=self.header_font, anchor="mm")

        # Result Big Launch Bar
        draw.rounded_rectangle([40, 310, self.width - 40, 420], radius=14, fill="#450a0a", outline="#ef4444", width=3)
        draw.text((self.width // 2, 345), "ИТОГ: ИМПУЛЬС УХОДИТ В ГРУЗОВИК", fill="#ffffff", font=self.header_font, anchor="mm")
        draw.text((self.width // 2, 385), "Вся сила выталкивания подбрасывает 5-тонный пикап в стратосферу!", fill="#fca5a5", font=self.body_font, anchor="mm")

        # Bottom Explanatory Banner
        draw.rounded_rectangle([40, 440, self.width - 40, 525], radius=14, fill="#1e1e2e", outline="#f43f5e", width=2)
        draw.text((self.width // 2, 482), "Движок Havok суммирует силу отталкивания -> Грузовик улетает в космос!", fill="#fecdd3", font=self.body_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_fix_card(self, output_path: Path) -> Path:
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

        draw.text((120, 18), "ЛОГИКА РАБОТЫ ФИКСА В КОДЕ (HAVOK SOLVER)", fill="#cdd6f4", font=self.header_font)

        # 1. Bug Box (Red)
        bug_y1, bug_y2 = 85, 305
        draw.rounded_rectangle([30, bug_y1, self.width - 30, bug_y2], radius=16, fill="#311b24", outline="#f38ba8", width=2)
        # Bug badge
        draw.rounded_rectangle([50, bug_y1 + 15, 290, bug_y1 + 55], radius=8, fill="#f38ba8")
        draw.text((170, bug_y1 + 35), "[-] НЕПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, bug_y1 + 75), "сила_выталкивания = глубина_проникновения * 9999;", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, bug_y1 + 135), "// Труп застрял в земле -> импульс запускает пикап в космос", fill="#fca5a5", font=self.body_font)

        # 2. Fix Box (Green)
        fix_y1, fix_y2 = 330, 550
        draw.rounded_rectangle([30, fix_y1, self.width - 30, fix_y2], radius=16, fill="#162d22", outline="#a6e3a1", width=2)
        # Fix badge
        draw.rounded_rectangle([50, fix_y1 + 15, 260, fix_y1 + 55], radius=8, fill="#a6e3a1")
        draw.text((155, fix_y1 + 35), "[+] ПРАВИЛЬНО:", fill="#11111b", font=self.body_font, anchor="mm")

        draw.text((60, fix_y1 + 75), "сила_выталкивания = ограничить(сила, 0.0, 500.0);", fill="#ffffff", font=self.code_bold_large)
        draw.text((60, fix_y1 + 135), "// Ограничиваем импульс: труп аккуратно выскальзывает, машина стоит", fill="#a6e3a1", font=self.body_font)

        img.save(output_path, "PNG")
        return output_path
