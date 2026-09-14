from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageFont


class CodeCardGenerator:
    def __init__(
        self,
        width: int = 960,
        bg_color: str = "#181825",
        header_color: str = "#11111b",
        border_color: str = "#313244",
        text_color: str = "#cdd6f4"
    ):
        self.width = width
        self.bg_color = bg_color
        self.header_color = header_color
        self.border_color = border_color
        self.text_color = text_color

        # Load fonts
        self.font_path = "C:/Windows/Fonts/consola.ttf"
        self.header_font_path = "C:/Windows/Fonts/arialbd.ttf"
        try:
            self.code_font = ImageFont.truetype(self.font_path, 28)
            self.header_font = ImageFont.truetype(self.header_font_path, 22)
            self.badge_font = ImageFont.truetype(self.header_font_path, 20)
        except Exception:
            self.code_font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()
            self.badge_font = ImageFont.load_default()

    def generate_card(
        self,
        title: str,
        lines: List[Dict[str, str]],
        output_image_path: Path
    ) -> Path:
        """
        Generates a code card PNG.
        lines format:
        [
            {"text": "uint8_t aggression = 1;", "type": "bug", "line_no": "12"},
            {"text": "aggression -= 2; // underflow -> 255!", "type": "bug", "line_no": "13"},
            {"text": "int aggression = 1;", "type": "fix", "line_no": "12"},
            {"text": "aggression = max(0, aggression - 2);", "type": "fix", "line_no": "13"},
            {"text": "...", "type": "normal", "line_no": "14"}
        ]
        """
        output_image_path = Path(output_image_path)
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        header_height = 56
        line_height = 44
        padding_top_bottom = 24
        total_height = header_height + padding_top_bottom + (len(lines) * line_height)

        # Create transparent canvas for card with rounded corners
        img = Image.new("RGBA", (self.width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw main card background with rounded rectangle
        corner_radius = 20
        draw.rounded_rectangle(
            [0, 0, self.width, total_height],
            radius=corner_radius,
            fill=self.bg_color,
            outline=self.border_color,
            width=2
        )

        # Draw header bar
        header_img = Image.new("RGBA", (self.width, header_height), (0, 0, 0, 0))
        header_draw = ImageDraw.Draw(header_img)
        header_draw.rounded_rectangle(
            [0, 0, self.width, header_height + corner_radius],
            radius=corner_radius,
            fill=self.header_color
        )
        img.paste(header_img.crop((0, 0, self.width, header_height)), (0, 0), mask=header_img.crop((0, 0, self.width, header_height)))

        # Draw macOS window control dots
        dot_y = header_height // 2
        dots = [
            (28, dot_y, "#f38ba8"),  # Red
            (52, dot_y, "#f9e2af"),  # Yellow
            (76, dot_y, "#a6e3a1")   # Green
        ]
        for dx, dy, color in dots:
            draw.ellipse([dx - 7, dy - 7, dx + 7, dy + 7], fill=color)

        # Draw Header Title (e.g. file name / bug info)
        draw.text((110, 16), title, fill="#a6adc8", font=self.header_font)

        # Draw code lines
        curr_y = header_height + 14

        for line in lines:
            l_type = line.get("type", "normal")
            l_text = line.get("text", "")
            l_num = line.get("line_no", "")

            # Highlight row background for bug or fix
            if l_type == "bug":
                # Red highlight background
                draw.rectangle(
                    [10, curr_y - 4, self.width - 10, curr_y + line_height - 6],
                    fill="#451a24"
                )
                badge_bg = "#f38ba8"
                badge_fg = "#11111b"
                badge_text = " BUG "
                line_color = "#f38ba8"
            elif l_type == "fix":
                # Green highlight background
                draw.rectangle(
                    [10, curr_y - 4, self.width - 10, curr_y + line_height - 6],
                    fill="#1b3d2f"
                )
                badge_bg = "#a6e3a1"
                badge_fg = "#11111b"
                badge_text = " FIX "
                line_color = "#a6e3a1"
            else:
                badge_bg = None
                line_color = self.text_color

            # Draw Line Number
            if l_num:
                draw.text((25, curr_y), str(l_num).rjust(3), fill="#585b70", font=self.code_font)

            # Draw Type Badge
            badge_x = 90
            if badge_bg:
                draw.rounded_rectangle(
                    [badge_x, curr_y + 2, badge_x + 58, curr_y + 26],
                    radius=4,
                    fill=badge_bg
                )
                draw.text((badge_x + 6, curr_y + 2), badge_text, fill=badge_fg, font=self.badge_font)

            # Draw Code Text
            text_x = 165 if badge_bg else 90
            draw.text((text_x, curr_y), l_text, fill=line_color, font=self.code_font)

            curr_y += line_height

        img.save(output_image_path, "PNG")
        return output_image_path
