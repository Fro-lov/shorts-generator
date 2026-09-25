import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

from src.core.code_card import CodeCardGenerator


class Episode17VisualsGenerator:
    """
    Visuals Generator for Episode #17 (Fallout: New Vegas Malcolm Holmes World Freeze Bug).
    Creates 1000x1280 px vertical Top-to-Bottom Mobile-First diagram cards.
    """

    def __init__(self, width: int = 1000, height: int = 1280):
        self.width = width
        self.height = height

        # Dark graphit theme
        self.bg_color = "#14161a"
        self.card_bg = "#1c1f26"
        self.accent_red = "#ef4444"
        self.accent_cyan = "#38bdf8"
        self.accent_green = "#22c55e"
        self.accent_yellow = "#eab308"
        self.text_main = "#f8fafc"
        self.text_muted = "#94a3b8"

        # Fonts
        font_dir = "C:/Windows/Fonts"
        try:
            self.title_font = ImageFont.truetype(f"{font_dir}/segoeuib.ttf", 44)
            self.header_font = ImageFont.truetype(f"{font_dir}/segoeuib.ttf", 36)
            self.body_font = ImageFont.truetype(f"{font_dir}/segoeui.ttf", 32)
            self.bold_font = ImageFont.truetype(f"{font_dir}/segoeuib.ttf", 32)
            self.mono_font = ImageFont.truetype(f"{font_dir}/consola.ttf", 30)
            self.footer_font = ImageFont.truetype(f"{font_dir}/segoeui.ttf", 26)
        except Exception:
            self.title_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.body_font = ImageFont.load_default()
            self.bold_font = ImageFont.load_default()
            self.mono_font = ImageFont.load_default()
            self.footer_font = ImageFont.load_default()

    def generate_diagram_1(self, output_path: Path) -> Path:
        """Diagram 1: Gamebryo World Freeze & ForceDialogue Logic."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.new("RGBA", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Outer border
        draw.rectangle([0, 0, self.width - 1, self.height - 1], outline="#262a33", width=6)

        # Header Bar
        draw.rectangle([0, 0, self.width, 130], fill="#1e232d")
        draw.rectangle([0, 0, 16, 130], fill=self.accent_cyan)
        draw.text((40, 30), "ЭТАП 1: ЗАМОРОЗКА ВРЕМЕНИ ДВИЖКА", fill=self.accent_cyan, font=self.title_font)
        draw.text((40, 84), "Fallout: New Vegas // Gamebryo World Pause State", fill=self.text_muted, font=self.footer_font)

        # STEP 1 CONTAINER (Top Block, Full Width)
        draw.rounded_rectangle([30, 150, self.width - 30, 580], radius=16, fill=self.card_bg, outline="#2e3440", width=3)
        draw.rectangle([30, 150, 42, 580], fill=self.accent_cyan)

        draw.text((60, 175), "1. Старт диалога (ForceDialogue)", fill=self.text_main, font=self.header_font)
        draw.text((60, 235), "• Маркольм Холмс выбегает и вызывает диалог", fill=self.text_main, font=self.body_font)
        draw.text((60, 285), "• Движок блокирует ввод управления игрока", fill=self.text_main, font=self.body_font)
        draw.text((60, 335), "• Скорость времени мира сбрасывается в нуль", fill=self.text_main, font=self.body_font)

        # Tech Parameter Box
        draw.rounded_rectangle([60, 400, self.width - 60, 550], radius=12, fill="#12151c", outline="#38bdf8", width=2)
        draw.text((80, 420), "WORLD TIME MULTIPLIER:", fill=self.accent_cyan, font=self.bold_font)
        draw.text((80, 475), "Gamebryo.TimeScale = 0.0f; // Global Freeze", fill="#34d399", font=self.mono_font)

        # CONNECTOR ARROW DOWN
        draw.text((self.width // 2, 605), "||", fill=self.accent_red, font=self.title_font, anchor="mm")
        draw.text((self.width // 2, 635), "\\/", fill=self.accent_red, font=self.title_font, anchor="mm")

        # STEP 2 CONTAINER (Bottom Block, Full Width)
        draw.rounded_rectangle([30, 670, self.width - 30, 1120], radius=16, fill=self.card_bg, outline="#3b1d1d", width=3)
        draw.rectangle([30, 670, 42, 1120], fill=self.accent_red)

        draw.text((60, 695), "2. Остановка AI моба vs Речь NPC", fill=self.accent_red, font=self.header_font)
        draw.text((60, 755), "• Муравей замирает в воздухе посреди атаки", fill=self.text_main, font=self.body_font)
        draw.text((60, 805), "• Физический тик и апдейт AI поставлены на паузу", fill=self.text_main, font=self.body_font)
        draw.text((60, 855), "• Говорящий NPC продолжает анимацию LipSync", fill=self.text_main, font=self.body_font)

        # Result Box
        draw.rounded_rectangle([60, 920, self.width - 60, 1080], radius=12, fill="#2a1215", outline="#ef4444", width=2)
        draw.text((80, 945), "РЕЗУЛЬТАТ:", fill="#fca5a5", font=self.bold_font)
        draw.text((80, 1000), "Монстр застыл в 5 см от лица, пока NPC болтает", fill=self.text_main, font=self.body_font)

        # FOOTER BORDER & TEXT
        draw.rectangle([0, 1150, self.width, 1280], fill="#181b22")
        draw.text((self.width // 2, 1205), "ИТОГ: Время мира остановлено ради защиты игрока", fill=self.accent_cyan, font=self.bold_font, anchor="mm")

        img.save(output_path, "PNG")
        return output_path

    def generate_code_card(self, output_path: Path) -> Path:
        """Code Card: Missing Combat Check Bug vs Fixed Script."""
        code_gen = CodeCardGenerator(width=980)
        lines = [
            {"text": "// BUG: Malcolm triggers dialogue without checking combat", "type": "bug", "line_no": "42"},
            {"text": "if (player.HasItem(StarCap) && !met_player)", "type": "bug", "line_no": "43"},
            {"text": "    malcolm.ForceDialogue(player); // BUG: Freezes world in combat!", "type": "bug", "line_no": "44"},
            {"text": "", "type": "normal", "line_no": "45"},
            {"text": "// FIX: Ensure player is not currently engaged in combat", "type": "fix", "line_no": "46"},
            {"text": "if (player.HasItem(StarCap) && !met_player && !player.IsInCombat())", "type": "fix", "line_no": "47"},
            {"text": "    malcolm.ForceDialogue(player); // FIX: Wait for combat to end", "type": "fix", "line_no": "48"}
        ]
        code_gen.generate_card("MalcolmHolmesScript.geck (Fallout: NV)", lines, output_path)
        return output_path


def generate_episode17_visuals():
    out_dir = BASE_DIR / "output" / "17" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    gen = Episode17VisualsGenerator()
    diagram1_path = out_dir / "diagram_pause_world.png"
    code_card_path = out_dir / "code_card_holmes.png"

    gen.generate_diagram_1(diagram1_path)
    gen.generate_code_card(code_card_path)

    print(f"[+] Diagram 1 generated: {diagram1_path}")
    print(f"[+] Code card generated: {code_card_path}")
    return diagram1_path, code_card_path


if __name__ == "__main__":
    generate_episode17_visuals()
