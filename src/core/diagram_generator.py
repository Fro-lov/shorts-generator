from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config.settings import ASSETS_DIR


class DiagramGenerator:
    def __init__(self, width: int = 980, height: int = 580):
        self.width = width
        self.height = height
        self.bg_color = "#0f172a"
        self.border_color = "#38bdf8"

        try:
            self.title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.label_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 20)
            self.code_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.label_font = ImageFont.load_default()
            self.code_font = ImageFont.load_default()

    def generate_cyberpunk_physics_diagram(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Card container with rounded corners and cyan glow
        draw.rounded_rectangle(
            [0, 0, self.width, self.height],
            radius=18,
            fill=self.bg_color,
            outline=self.border_color,
            width=2
        )

        # Title bar
        draw.rounded_rectangle(
            [0, 0, self.width, 50],
            radius=18,
            fill="#1e293b"
        )
        draw.rectangle([0, 30, self.width, 50], fill="#1e293b")
        draw.text((30, 12), "📐 СХЕМА ОШИБКИ: REDengine & PhysX Deformation", fill="#38bdf8", font=self.title_font)

        # Step 1: 3D Mesh Penetration (Left box)
        box1 = [30, 75, 470, 540]
        draw.rounded_rectangle(box1, radius=12, fill="#182032", outline="#334155", width=1)
        draw.text((50, 90), "1. Высокая скорость + Коллизия", fill="#f8fafc", font=self.label_font)

        # Draw Static Barrier
        draw.rectangle([340, 140, 440, 380], fill="#475569", outline="#94a3b8", width=2)
        draw.text((355, 250), "БЛОК\n(Barrier)", fill="#f1f5f9", font=self.label_font)

        # Draw 3D Car box entering barrier
        draw.rounded_rectangle([100, 180, 370, 340], radius=10, fill="#1e3a8a", outline="#60a5fa", width=3)
        draw.text((150, 250), "3D Автомобиль", fill="#93c5fd", font=self.label_font)

        # Draw Penetration Area (Overlap)
        draw.rectangle([340, 180, 370, 340], fill="#ef4444")
        draw.text((100, 410), "• Высокая скорость (Tunneling)", fill="#fca5a5", font=self.code_font)
        draw.text((100, 440), "• Проникновение внутрь барьера", fill="#fca5a5", font=self.code_font)
        draw.text((100, 470), "• Физический тик пропустил удар", fill="#94a3b8", font=self.code_font)

        # Step 2: Deformation Collapse to Z=0 (Right box)
        box2 = [500, 75, 950, 540]
        draw.rounded_rectangle(box2, radius=12, fill="#182032", outline="#334155", width=1)
        draw.text((520, 90), "2. Ошибка выталкивания (Z = 0)", fill="#f8fafc", font=self.label_font)

        # Draw Static Barrier
        draw.rectangle([810, 140, 910, 380], fill="#475569", outline="#94a3b8", width=2)
        draw.text((825, 250), "БЛОК", fill="#f1f5f9", font=self.label_font)

        # Squashed flat car line
        draw.rounded_rectangle([550, 255, 830, 265], radius=3, fill="#f43f5e", outline="#fda4af", width=2)
        draw.text((560, 205), "⚠️ Схлопывание вершин (Z -> 0)", fill="#fb7185", font=self.label_font)

        # Force arrows compressing car
        draw.text((670, 150), "⬇ Сила деформации ⬇", fill="#f43f5e", font=self.code_font)
        draw.text((670, 285), "⬆ Выталкивание меша ⬆", fill="#f43f5e", font=self.code_font)

        draw.text((530, 410), "• Solver умножил Z на коэфф. сжатия", fill="#fca5a5", font=self.code_font)
        draw.text((530, 440), "• Без Clamp(min_height) геометрия", fill="#fca5a5", font=self.code_font)
        draw.text((530, 470), "• Превратилась в плоскую 2D текстуру", fill="#fbbf24", font=self.code_font)

        img.save(output_path, "PNG")
        return output_path
