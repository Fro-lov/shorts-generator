import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from config.settings import FFMPEG_PATH, VIDEO_WIDTH, VIDEO_HEIGHT, FPS, OUTPUT_DIR, PLACEHOLDERS_DIR


class VideoCompositor:
    def __init__(self, ffmpeg_path: str = FFMPEG_PATH):
        self.ffmpeg_path = ffmpeg_path

    def create_placeholder_background(
        self,
        duration: float,
        game_title: str,
        bug_name: str,
        output_bg_video: Path
    ) -> Path:
        """
        Creates a high-quality vertical 1080x1920 placeholder video with stylish gaming aesthetic.
        """
        output_bg_video = Path(output_bg_video)
        output_bg_video.parent.mkdir(parents=True, exist_ok=True)
        bg_frame_path = PLACEHOLDERS_DIR / "placeholder_frame.png"

        # Generate base frame image
        img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (15, 17, 26))
        draw = ImageDraw.Draw(img)

        # Draw subtle background grid lines
        grid_color = (25, 30, 45)
        for y in range(0, VIDEO_HEIGHT, 60):
            draw.line([(0, y), (VIDEO_WIDTH, y)], fill=grid_color, width=1)
        for x in range(0, VIDEO_WIDTH, 60):
            draw.line([(x, 0), (x, VIDEO_HEIGHT)], fill=grid_color, width=1)

        # Fonts
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 38)
            sub_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
            box_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
            small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
        except Exception:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
            box_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Top Badge: "РАЗБОР БАГА В КОДЕ"
        badge_w, badge_h = 440, 52
        badge_x = (VIDEO_WIDTH - badge_w) // 2
        badge_y = 120
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
            radius=12,
            fill="#e11d48"
        )
        draw.text((badge_x + 35, badge_y + 10), "🔥 КАК РАБОТАЕТ БАГ", fill="#ffffff", font=sub_font)

        # Game & Bug Title Header
        header_text = f"{game_title.upper()}"
        draw.text((VIDEO_WIDTH // 2, 210), header_text, fill="#38bdf8", font=title_font, anchor="mm")

        bug_text = f"«{bug_name}»"
        draw.text((VIDEO_WIDTH // 2, 265), bug_text, fill="#f1f5f9", font=sub_font, anchor="mm")

        # Gameplay Video Box Placeholder (16:9 area in upper-middle)
        box_w = 980
        box_h = int(box_w * 9 / 16)  # ~551 px
        box_x = (VIDEO_WIDTH - box_w) // 2
        box_y = 340

        # Outer glow border
        draw.rounded_rectangle(
            [box_x - 4, box_y - 4, box_x + box_w + 4, box_y + box_h + 4],
            radius=20,
            outline="#38bdf8",
            width=3
        )
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=16,
            fill="#0f172a"
        )

        # Placeholder Icon and text inside box
        draw.text((VIDEO_WIDTH // 2, box_y + (box_h // 2) - 30), "🎬 [ МЕСТО ДЛЯ ГЕЙМПЛЕЯ С БАГОМ ]", fill="#94a3b8", font=box_font, anchor="mm")
        draw.text((VIDEO_WIDTH // 2, box_y + (box_h // 2) + 25), "Здесь будет видео с геймплеем (16:9 / 9:16)", fill="#64748b", font=small_font, anchor="mm")

        # Save template image
        img.save(bg_frame_path, "PNG")

        # Render looping video background with FFmpeg for the duration
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-loop", "1",
            "-i", str(bg_frame_path),
            "-t", str(duration),
            "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            str(output_bg_video)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg failed creating placeholder background: {res.stderr}")

        return output_bg_video

    def render_clip(
        self,
        duration: float,
        audio_path: Path,
        ass_subtitles_path: Optional[Path],
        output_video_path: Path,
        background_video: Optional[Path] = None,
        game_title: str = "ИГРОВОЙ БАГ",
        bug_name: str = "Разбор механики",
        code_card_img: Optional[Path] = None,
        code_card_timing: Optional[Dict[str, float]] = None,
        memes: Optional[List[Dict[str, Any]]] = None
    ) -> Path:
        """
        Composes the final 9:16 video with background, code overlay, meme images, audio and subtitles.
        """
        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        temp_bg = OUTPUT_DIR / "temp_bg.mp4"
        if not background_video or not Path(background_video).exists():
            self.create_placeholder_background(duration, game_title, bug_name, temp_bg)
            base_bg = temp_bg
        else:
            base_bg = background_video

        # Prepare FFmpeg Filter Complex
        filter_chains = []
        inputs = ["-i", str(base_bg), "-i", str(audio_path)]
        input_idx = 2
        last_v_label = "[0:v]"

        # Code card overlay input if present
        if code_card_img and Path(code_card_img).exists() and code_card_timing:
            inputs.extend(["-i", str(code_card_img)])
            t_start = code_card_timing.get("start", 0.0)
            t_end = code_card_timing.get("end", duration)
            fade_in = 0.3
            fade_out = 0.3
            card_label = f"[{input_idx}:v]"
            filter_chains.append(
                f"{card_label}format=rgba,fade=t=in:st={t_start}:d={fade_in}:alpha=1,fade=t=out:st={t_end-fade_out}:d={fade_out}:alpha=1[card_fade]"
            )
            filter_chains.append(
                f"{last_v_label}[card_fade]overlay=(W-w)/2:960:enable='between(t,{t_start},{t_end})'[v_card]"
            )
            last_v_label = "[v_card]"
            input_idx += 1

        # Meme overlays if present
        if memes:
            for idx, meme in enumerate(memes):
                meme_path = Path(meme.get("image", ""))
                if not meme_path.exists():
                    continue
                inputs.extend(["-i", str(meme_path)])
                m_start = float(meme.get("start", 0.0))
                m_dur = float(meme.get("duration", 2.5))
                m_end = float(meme.get("end", m_start + m_dur))
                m_scale = meme.get("scale", 640)
                m_pos = meme.get("position", "center")

                # Positioning coordinates
                if m_pos == "gameplay_box":
                    pos_expr = "(W-w)/2:360"
                elif m_pos == "bottom":
                    pos_expr = "(W-w)/2:H-h-300"
                elif m_pos == "top":
                    pos_expr = "(W-w)/2:120"
                else:  # center
                    pos_expr = "(W-w)/2:(H-h)/2"

                m_label = f"[{input_idx}:v]"
                m_out = f"[meme_{idx}]"
                v_next = f"[v_meme_{idx}]"

                filter_chains.append(
                    f"{m_label}scale={m_scale}:-1,format=rgba,fade=t=in:st={m_start}:d=0.2:alpha=1,fade=t=out:st={m_end-0.2}:d=0.2:alpha=1{m_out}"
                )
                filter_chains.append(
                    f"{last_v_label}{m_out}overlay={pos_expr}:enable='between(t,{m_start},{m_end})'{v_next}"
                )
                last_v_label = v_next
                input_idx += 1

        # Add Subtitles filter
        if ass_subtitles_path and Path(ass_subtitles_path).exists():
            rel_sub_path = Path(ass_subtitles_path).resolve().as_posix()
            escaped_path = rel_sub_path.replace(":", "\\:")
            filter_chains.append(f"{last_v_label}subtitles=filename='{escaped_path}'[v_out]")
            map_v = "[v_out]"
        else:
            map_v = last_v_label

        filter_complex_str = ";".join(filter_chains)

        cmd = [self.ffmpeg_path, "-y"]
        cmd.extend(inputs)

        if filter_complex_str:
            cmd.extend(["-filter_complex", filter_complex_str, "-map", map_v, "-map", "1:a"])
        else:
            cmd.extend(["-map", "0:v", "-map", "1:a"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            str(output_video_path)
        ])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg composite failed:\n{res.stderr}")

        return output_video_path
