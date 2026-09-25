"""
Outro Call-To-Action (CTA) Card Generator for Onter's inn Shorts Engine.
Generates a universal subscribe banner for both YouTube Shorts and TikTok formats.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class OutroCTAGenerator:
    """
    Generates a universal 1000x340 subscribe banner overlay featuring:
    - YouTube Shorts + TikTok logos
    - Onter's inn branding
    - Vibrant 'ПОДПИСАТЬСЯ' button
    - Click hand cursor animation
    """

    def __init__(self, width: int = 1000, height: int = 340):
        self.width = width
        self.height = height

        # Load clean fonts
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
            self.font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 19)
            self.font_btn = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_sub = ImageFont.load_default()
            self.font_btn = ImageFont.load_default()
            self.font_badge = ImageFont.load_default()

    def _draw_yt_shorts_logo(self, draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 54):
        """Draws a crisp YouTube Shorts icon badge."""
        # Red rounded background badge
        draw.rounded_rectangle(
            [x, y, x + size, y + size],
            radius=14,
            fill="#ff0000"
        )
        # White play triangle
        tri_pts = [
            (x + size * 0.40, y + size * 0.28),
            (x + size * 0.72, y + size * 0.50),
            (x + size * 0.40, y + size * 0.72)
        ]
        draw.polygon(tri_pts, fill="#ffffff")

    def _draw_tiktok_logo(self, draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 54):
        """Draws a crisp TikTok icon badge with cyan/magenta accents."""
        # Dark badge
        draw.rounded_rectangle(
            [x, y, x + size, y + size],
            radius=14,
            fill="#111111",
            outline="#222222",
            width=1
        )

        cx, cy = x + size // 2, y + size // 2

        # Cyan shadow
        draw.arc([cx - 12, cy - 10, cx + 8, cy + 10], start=90, end=270, fill="#00f2fe", width=4)
        draw.line([(cx + 8, cy - 10), (cx + 8, cy + 6)], fill="#00f2fe", width=4)

        # Magenta main note
        draw.arc([cx - 14, cy - 8, cx + 6, cy + 12], start=90, end=270, fill="#ff0050", width=4)
        draw.line([(cx + 6, cy - 12), (cx + 6, cy + 8)], fill="#ff0050", width=4)

        # White core note
        draw.arc([cx - 13, cy - 9, cx + 7, cy + 11], start=90, end=270, fill="#ffffff", width=3)
        draw.line([(cx + 7, cy - 11), (cx + 7, cy + 7)], fill="#ffffff", width=3)

    def _draw_click_cursor(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, clicked: bool = True):
        """Draws a clean pointer hand icon."""
        # Simple crisp white pointer hand with black outline
        hand_pts = [
            (cx, cy),
            (cx + 6, cy + 14),
            (cx + 12, cy + 10),
            (cx + 18, cy + 24),
            (cx + 24, cy + 20),
            (cx + 18, cy + 7),
            (cx + 26, cy + 7),
            (cx + 26, cy - 2),
            (cx + 18, cy - 2),
            (cx + 18, cy - 10),
            (cx + 10, cy - 10),
            (cx + 10, cy + 4),
            (cx + 4, cy + 4)
        ]
        # Draw black shadow/outline
        draw.polygon([(px + 2, py + 2) for px, py in hand_pts], fill="#000000")
        # Draw main white hand
        draw.polygon(hand_pts, fill="#ffffff", outline="#111111", width=2)

        if clicked:
            # Click ripple rings
            draw.arc([cx - 16, cy - 16, cx + 16, cy + 16], start=0, end=360, fill="#ffffff", width=2)
            draw.arc([cx - 24, cy - 24, cx + 24, cy + 24], start=0, end=360, fill=(255, 255, 255, 128), width=2)

    def render_card(self, output_path: Path, click_animation_ratio: float = 1.0) -> Path:
        """
        Renders the static or animated Outro Subscribe Card.
        click_animation_ratio: 0.0 (unclicked) to 1.0 (fully clicked).
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # RGBA canvas with smooth rounded dark card container
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Main Container Box
        card_rect = [10, 10, self.width - 10, self.height - 10]
        draw.rounded_rectangle(
            card_rect,
            radius=24,
            fill="#161922",
            outline="#3b4252",
            width=2
        )

        # Top subtle highlight bar
        draw.rounded_rectangle(
            [10, 10, self.width - 10, 20],
            radius=10,
            fill="#2e3440"
        )

        # 2. Left Platform Logos & Channel Info
        logo_y = 45
        self._draw_yt_shorts_logo(draw, 40, logo_y, size=54)
        self._draw_tiktok_logo(draw, 106, logo_y, size=54)

        # Vertical Divider
        draw.line([(178, logo_y + 4), (178, logo_y + 50)], fill="#3b4252", width=2)

        # Channel Branding Title & Subtitle
        channel_name = "Onter's inn"
        draw.text((195, logo_y - 2), channel_name, fill="#ffffff", font=self.font_title)
        
        # Calculate badge X based on channel name width
        c_bbox = draw.textbbox((195, logo_y - 2), channel_name, font=self.font_title)
        badge_x = c_bbox[2] + 15
        
        # Red 'SHORTS' badge
        draw.rounded_rectangle([badge_x, logo_y + 4, badge_x + 90, logo_y + 30], radius=8, fill="#e11d48")
        draw.text((badge_x + 10, logo_y + 7), "SHORTS", fill="#ffffff", font=self.font_badge)

        draw.text((195, logo_y + 36), "Свежие разборы багов каждый день!", fill="#94a3b8", font=self.font_sub)

        # 3. Large 'ПОДПИСАТЬСЯ' Subscribe Button
        btn_y = 145
        btn_w, btn_h = 920, 140
        btn_x = (self.width - btn_w) // 2

        # Button background
        btn_fill = "#be123c" if click_animation_ratio > 0.5 else "#e11d48"
        btn_outline = "#ffffff" if click_animation_ratio > 0.5 else "#f43f5e"

        draw.rounded_rectangle(
            [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
            radius=20,
            fill=btn_fill,
            outline=btn_outline,
            width=3
        )

        # Button text
        btn_text = "ПОДПИСАТЬСЯ НА КАНАЛ"
        text_bbox = draw.textbbox((0, 0), btn_text, font=self.font_btn)
        tw = text_bbox[2] - text_bbox[0]
        th = text_bbox[3] - text_bbox[1]

        text_x = btn_x + (btn_w - tw) // 2 - 30
        text_y = btn_y + (btn_h - th) // 2 - 4
        draw.text((text_x, text_y), btn_text, fill="#ffffff", font=self.font_btn)

        # 4. Animated Click Hand Cursor
        cursor_x = btn_x + btn_w - 220
        cursor_y = btn_y + btn_h // 2 + 10

        self._draw_click_cursor(draw, cursor_x, cursor_y, clicked=(click_animation_ratio > 0.5))

        # Save card PNG
        img.save(output_path, "PNG")
        return output_path


def generate_default_outro_card(output_path: Path = None) -> Path:
    if output_path is None:
        output_path = Path("e:/social/output/templates/outro_subscribe_cta.png")
    gen = OutroCTAGenerator()
    return gen.render_card(output_path, click_animation_ratio=1.0)


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    out = generate_default_outro_card()
    print(f"[SUCCESS] Generated universal subscribe card: {out}")
