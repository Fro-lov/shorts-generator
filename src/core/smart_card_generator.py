import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


def sanitize_text(text: str) -> str:
    """Strips all emoji characters and non-standard symbols to prevent square box glyph artifacts."""
    if not text:
        return ""
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27bf]', '', text)
    text = re.sub(r'[\u2300-\u23ff]', '', text)
    text = text.replace("⚠️", "[!]").replace("💡", "[INFO]").replace("✔", "[v]").replace("🛠️", "[FIX]")
    return text.strip()


class SmartCardGenerator:
    """
    Ultra-Tight Compact Card Generator.
    - Zero Wasted Space: Card height dynamically wraps content OR distributes text evenly.
    - Dynamic Font & Vertical Spacing: 3 items spread across available height so no empty voids exist.
    - OS Window IDE styling for Code Cards.
    - 100% Ban on emojis.
    """
    def __init__(self, width: int = 1000):
        self.width = width
        self.bg_color = "#14161a"
        self.border_color = "#2d3342"
        self.header_bg = "#1c212b"
        self.cyan_accent = "#38bdf8"
        self.orange_accent = "#fb923c"
        self.green_accent = "#4ade80"
        self.red_accent = "#f87171"

        self.font_dir = "C:/Windows/Fonts/"
        self._init_fonts()

    def _init_fonts(self):
        try:
            self.font_bold_huge = ImageFont.truetype(os.path.join(self.font_dir, "arialbd.ttf"), 36)
            self.font_bold_large = ImageFont.truetype(os.path.join(self.font_dir, "arialbd.ttf"), 30)
            self.font_bold_mid = ImageFont.truetype(os.path.join(self.font_dir, "arialbd.ttf"), 26)
            self.font_bold_small = ImageFont.truetype(os.path.join(self.font_dir, "arialbd.ttf"), 20)
            self.font_code = ImageFont.truetype(os.path.join(self.font_dir, "consola.ttf"), 24)
            self.font_code_bold = ImageFont.truetype(os.path.join(self.font_dir, "consolab.ttf"), 26)
        except Exception:
            default = ImageFont.load_default()
            self.font_bold_huge = default
            self.font_bold_large = default
            self.font_bold_mid = default
            self.font_bold_small = default
            self.font_code = default
            self.font_code_bold = default

    def generate_diagram_card(
        self,
        output_path: Path,
        title: str,
        badge: str,
        step_title: str,
        items: List[str],
        accent_color: str = "#38bdf8",
        footer_note: str = ""
    ) -> Path:
        """
        Generates a dynamically sized card that wraps content snuggly with ZERO empty voids.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        title = sanitize_text(title)
        badge = sanitize_text(badge)
        step_title = sanitize_text(step_title)
        footer_note = sanitize_text(footer_note)

        import textwrap

        # 1. Calculate dynamic height based on wrapped item lines
        item_font = self.font_bold_large if len(items) <= 3 else self.font_bold_mid
        single_line_h = 44 if len(items) <= 3 else 36
        max_chars = 38 if len(items) <= 3 else 44

        wrapped_items = []
        total_item_lines = 0
        for item in items:
            clean = sanitize_text(item)
            lines = textwrap.wrap(clean, width=max_chars) or [clean]
            wrapped_items.append((clean, lines))
            total_item_lines += len(lines)

        items_h = total_item_lines * single_line_h + (len(items) * 12)
        box_h = 60 + items_h + 20 # Subtitle header (60) + items + bottom pad (20)
        footer_h = 70 if footer_note else 0

        # Total Card Height dynamically computed
        card_height = 95 + box_h + (footer_h + 20 if footer_h else 20)

        img = Image.new("RGBA", (self.width, card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Container
        draw.rounded_rectangle(
            [0, 0, self.width, card_height],
            radius=20,
            fill=self.bg_color,
            outline=self.border_color,
            width=3
        )

        # Top Header Bar (Height 75px)
        draw.rounded_rectangle([0, 0, self.width, 75], radius=20, fill=self.header_bg)
        draw.rectangle([0, 40, self.width, 75], fill=self.header_bg)
        draw.line([0, 75, self.width, 75], fill="#2d3342", width=2)

        # Badge
        title_x = 24
        if badge:
            badge_text = badge.upper()
            bbox = draw.textbbox((0, 0), badge_text, font=self.font_bold_small)
            bw = (bbox[2] - bbox[0]) + 20
            badge_box = [20, 18, 20 + bw, 56]
            draw.rounded_rectangle(badge_box, radius=6, fill="#0f172a", outline=self.cyan_accent, width=2)
            draw.text((30, 26), badge_text, fill=self.cyan_accent, font=self.font_bold_small)
            title_x = badge_box[2] + 16

        # Title
        draw.text((title_x, 22), title, fill="#ffffff", font=self.font_bold_large)

        # Main Content Block (Tight auto-fitted height)
        box = [20, 95, self.width - 20, 95 + box_h]
        draw.rounded_rectangle(box, radius=14, fill="#191d24", outline="#2b313d", width=2)
        
        # Subtitle header bar inside box
        draw.rounded_rectangle([box[0], box[1], box[2], box[1] + 55], radius=14, fill="#212631")
        draw.rectangle([box[0], box[1] + 30, box[2], box[1] + 55], fill="#212631")
        draw.rounded_rectangle([box[0], box[1], box[0] + 8, box[3]], radius=4, fill=accent_color)
        draw.text((box[0] + 24, box[1] + 12), step_title, fill="#ffffff", font=self.font_bold_large)

        # Content Items with multiline support
        y_c = box[1] + 75
        for orig_item, lines in wrapped_items:
            color = self.orange_accent if "[!]" in orig_item or "ОШИБКА" in orig_item or "БАГ" in orig_item else "#e2e8f0"
            for idx, line in enumerate(lines):
                prefix = "* " if idx == 0 else "  "
                draw.text((box[0] + 24, y_c), f"{prefix}{line}", fill=color, font=item_font)
                y_c += single_line_h
            y_c += 10 # extra padding between bullet items

        # Footer Note
        if footer_note:
            fy = box[3] + 16
            draw.rounded_rectangle([20, fy, self.width - 20, fy + footer_h], radius=10, fill="#1e2430", outline=self.cyan_accent, width=2)
            draw.text((32, fy + 18), f"[INFO] {footer_note}", fill="#38bdf8", font=self.font_bold_mid)

        img.save(output_path, "PNG")
        return output_path

    def generate_os_code_card(
        self,
        output_path: Path,
        title: str,
        file_tab: str,
        wrong_code: List[str],
        fixed_code: List[str],
        takeaway: str = ""
    ) -> Path:
        """
        Generates an OS IDE Window style code card wrapping content snuggly with ZERO empty voids.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        title = sanitize_text(title)
        file_tab = sanitize_text(file_tab) or "physics_solver.cpp"
        takeaway = sanitize_text(takeaway)

        code_font = self.font_code_bold
        line_h = 36

        w_box_h = 45 + (len(wrong_code) * line_h) + 15
        f_box_h = 45 + (len(fixed_code) * line_h) + 15
        t_h = 60 if takeaway else 0

        card_height = 65 + 20 + w_box_h + 15 + f_box_h + (20 + t_h if t_h else 20)

        img = Image.new("RGBA", (self.width, card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # OS Window Container
        draw.rounded_rectangle(
            [0, 0, self.width, card_height],
            radius=18,
            fill="#181a1f",
            outline="#2d313b",
            width=3
        )

        # OS Window Titlebar (y: 0 to 60)
        draw.rounded_rectangle([0, 0, self.width, 60], radius=18, fill="#21252b")
        draw.rectangle([0, 30, self.width, 60], fill="#21252b")
        draw.line([0, 60, self.width, 60], fill="#2c313a", width=2)

        # OS Window Control Buttons
        draw.ellipse([20, 22, 34, 36], fill="#ff5f56") # Red
        draw.ellipse([42, 22, 56, 36], fill="#ffbd2e") # Yellow
        draw.ellipse([64, 22, 78, 36], fill="#27c93f") # Green

        # IDE File Tab
        draw.rounded_rectangle([100, 15, 320, 60], radius=8, fill="#181a1f")
        draw.text((120, 24), file_tab, fill="#abb2bf", font=self.font_code_bold)

        # Title
        draw.text((self.width - 340, 22), title, fill="#61afef", font=self.font_bold_small)

        # Block 1: [-] WRONG CODE
        box1 = [16, 75, self.width - 16, 75 + w_box_h]
        draw.rounded_rectangle(box1, radius=10, fill="#21191d", outline="#4a1e24", width=2)
        draw.text((box1[0] + 16, box1[1] + 8), "[-] WRONG / НЕПРАВИЛЬНО", fill="#e06c75", font=self.font_bold_small)

        y_c = box1[1] + 40
        for line in wrong_code:
            line_clean = sanitize_text(line)
            draw.text((box1[0] + 20, y_c), line_clean, fill="#fca5a5", font=code_font)
            y_c += line_h

        # Block 2: [+] FIXED CODE
        fy = box1[3] + 15
        box2 = [16, fy, self.width - 16, fy + f_box_h]
        draw.rounded_rectangle(box2, radius=10, fill="#18261e", outline="#1e4d2b", width=2)
        draw.text((box2[0] + 16, box2[1] + 8), "[+] FIXED / ПРАВИЛЬНЫЙ КОД", fill="#98c379", font=self.font_bold_small)

        y_c = box2[1] + 40
        for line in fixed_code:
            line_clean = sanitize_text(line)
            draw.text((box2[0] + 20, y_c), line_clean, fill="#98c379", font=code_font)
            y_c += line_h

        # Footer takeaway
        if takeaway:
            ty = box2[3] + 15
            draw.rounded_rectangle([16, ty, self.width - 16, ty + t_h], radius=8, fill="#1c2430", outline="#61afef", width=1)
            draw.text((28, ty + 16), f"[FIX] {takeaway}", fill="#61afef", font=self.font_bold_mid)

        img.save(output_path, "PNG")
        return output_path
