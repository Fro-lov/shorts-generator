import io
import sys
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from config.settings import FFMPEG_PATH, VIDEO_WIDTH, VIDEO_HEIGHT, FPS, VIDEO_CODEC, VIDEO_PRESET, VIDEO_CQ


def ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3)


def ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    x = max(0.0, min(1.0, x))
    return 1.0 + c3 * math.pow(x - 1.0, 3) + c1 * math.pow(x - 1.0, 2)


class MotionUIRenderer:
    def __init__(self, width: int = VIDEO_WIDTH, height: int = VIDEO_HEIGHT, fps: int = FPS):
        self.width = width
        self.height = height
        self.fps = fps

        # Fonts
        try:
            self.font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 40)
            self.font_subtitle = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
            self.font_sub_highlight = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
            self.font_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
            self.font_counter = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 76)
            self.font_mono = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 32)
            self.font_mono_small = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 26)
            self.font_regular = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 28)
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_sub_highlight = ImageFont.load_default()
            self.font_badge = ImageFont.load_default()
            self.font_counter = ImageFont.load_default()
            self.font_mono = ImageFont.load_default()
            self.font_mono_small = ImageFont.load_default()
            self.font_regular = ImageFont.load_default()

    def draw_rounded_card(self, draw: ImageDraw.ImageDraw, x1, y1, x2, y2, radius=24, fill="#121826ee", outline="#38bdf844", width=2):
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)

    def draw_badge(self, draw: ImageDraw.ImageDraw, x: int, y: int, text: str, bg_color: str = "#1e293b", text_color: str = "#38bdf8", border_color: str = "#0ea5e9"):
        bbox = draw.textbbox((x + 16, y + 8), text, font=self.font_badge)
        draw.rounded_rectangle([x, y, bbox[2] + 16, bbox[3] + 8], radius=8, fill=bg_color, outline=border_color, width=2)
        draw.text((x + 16, y + 8), text, fill=text_color, font=self.font_badge)

    def draw_hazard_stripes(self, draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, stripe_w: int = 18):
        w = x2 - x1
        h = y2 - y1
        draw.rectangle([x1, y1, x2, y2], fill="#18181b", outline="#eab308", width=2)
        for sx in range(-h, w + h, stripe_w * 2):
            pts = [
                (max(x1, min(x2, x1 + sx)), y1),
                (max(x1, min(x2, x1 + sx + stripe_w)), y1),
                (max(x1, min(x2, x1 + sx + stripe_w - h)), y2),
                (max(x1, min(x2, x1 + sx - h)), y2)
            ]
            if pts[0][0] < x2 and pts[2][0] > x1:
                draw.polygon([(max(x1, min(x2, px)), max(y1, min(y2, py))) for px, py in pts], fill="#eab308")

    def draw_subtitles_with_highlight(self, draw: ImageDraw.ImageDraw, prefix: str, highlight: str, y: int = 1480):
        # Calculate text widths
        prefix_box = draw.textbbox((0, 0), prefix, font=self.font_subtitle)
        hl_box = draw.textbbox((0, 0), highlight, font=self.font_sub_highlight)

        prefix_w = prefix_box[2] - prefix_box[0]
        hl_w = hl_box[2] - hl_box[0]
        space_w = 14
        total_w = prefix_w + space_w + hl_w + 24

        start_x = (self.width - total_w) // 2

        # Draw prefix
        draw.text((start_x, y), prefix, fill="#ffffff", font=self.font_subtitle, anchor="lm")

        # Draw orange highlight capsule for keyword
        hl_x = start_x + prefix_w + space_w
        draw.rounded_rectangle([hl_x - 10, y - 26, hl_x + hl_w + 10, y + 26], radius=10, fill="#f97316")
        draw.text((hl_x, y), highlight, fill="#ffffff", font=self.font_sub_highlight, anchor="lm")

    def render_overlay_frame(self, t: float) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        card_x1 = 60
        card_x2 = self.width - 60
        base_y1 = 880
        base_y2 = 1420

        # Determine active scene (4 scenes, 3.0s each)
        scene_idx = int(t // 3.0)
        scene_t = t % 3.0
        anim_progress = ease_out_cubic(min(1.0, scene_t / 0.45))
        slide_offset = int((1.0 - anim_progress) * 80)
        cur_y1 = base_y1 + slide_offset
        cur_y2 = base_y2 + slide_offset

        if scene_idx == 0:
            # SCENE 1: HOOK / KINEMATIC MASS
            self.draw_rounded_card(draw, card_x1, cur_y1, card_x2, cur_y2, radius=28, fill="#0f172acc", outline="#38bdf855", width=2)
            self.draw_badge(draw, card_x1 + 36, cur_y1 + 36, "СЦЕНА 1: КИНЕМАТИКА", bg_color="#0f172a", text_color="#38bdf8", border_color="#0284c7")
            draw.text((card_x1 + 36, cur_y1 + 105), "Дверь двигается как неуязвимый объект", fill="#ffffff", font=self.font_title)

            # 2 Big Stat Boxes
            box_w = 400
            box_h = 160
            b1_x = card_x1 + 36
            b2_x = card_x2 - 36 - box_w
            box_y = cur_y1 + 175

            # Box 1: Door Mass
            draw.rounded_rectangle([b1_x, box_y, b1_x + box_w, box_y + box_h], radius=18, fill="#1e293b", outline="#38bdf8", width=2)
            draw.text((b1_x + box_w//2, box_y + 60), "∞ кг", fill="#38bdf8", font=self.font_counter, anchor="mm")
            draw.text((b1_x + box_w//2, box_y + 120), "МАССА ДВЕРИ", fill="#94a3b8", font=self.font_mono_small, anchor="mm")

            # Box 2: Player HP
            draw.rounded_rectangle([b2_x, box_y, b2_x + box_w, box_y + box_h], radius=18, fill="#1e293b", outline="#22c55e", width=2)
            draw.text((b2_x + box_w//2, box_y + 60), "100 HP", fill="#4ade80", font=self.font_counter, anchor="mm")
            draw.text((b2_x + box_w//2, box_y + 120), "ЗДОРОВЬЕ NPC", fill="#94a3b8", font=self.font_mono_small, anchor="mm")

            # Subtitle
            self.draw_subtitles_with_highlight(draw, "ДВЕРЬ ДВИГАЛАСЬ С", "БЕСКОНЕЧНОЙ МАССОЙ")

        elif scene_idx == 1:
            # SCENE 2: COLLISION PINCHING
            self.draw_rounded_card(draw, card_x1, cur_y1, card_x2, cur_y2, radius=28, fill="#0f172acc", outline="#f59e0b55", width=2)
            self.draw_badge(draw, card_x1 + 36, cur_y1 + 36, "СЦЕНА 2: ЗАЖАТИЕ У СТЕНЫ", bg_color="#0f172a", text_color="#fbbf24", border_color="#d97706")
            draw.text((card_x1 + 36, cur_y1 + 105), "Капсула зажата между дверью и стеной", fill="#ffffff", font=self.font_title)

            # 2D Collision Visual Area
            vis_x1 = card_x1 + 36
            vis_x2 = card_x2 - 36
            vis_y1 = cur_y1 + 170
            vis_y2 = cur_y2 - 36
            draw.rounded_rectangle([vis_x1, vis_y1, vis_x2, vis_y2], radius=18, fill="#0b1120", outline="#1e293b", width=2)

            # Static Wall (Right)
            wall_x = vis_x2 - 140
            self.draw_hazard_stripes(draw, wall_x, vis_y1 + 20, wall_x + 80, vis_y2 - 20, stripe_w=16)
            draw.text((wall_x + 40, vis_y1 - 18), "СТЕНА", fill="#eab308", font=self.font_badge, anchor="mm")

            # NPC Capsule (Pinned against Wall)
            npc_cx = wall_x - 70
            npc_cy = (vis_y1 + vis_y2) // 2
            draw.rounded_rectangle([npc_cx - 40, npc_cy - 90, npc_cx + 40, npc_cy + 90], radius=40, fill="#16653455", outline="#22c55e", width=3)
            draw.text((npc_cx, npc_cy), "NPC", fill="#86efac", font=self.font_badge, anchor="mm")

            # Rotating Door Animation (rotates into NPC)
            rot_t = ease_out_cubic(min(1.0, scene_t / 1.5))
            door_angle = math.radians(10 + rot_t * 26)  # 10 to 36 degrees
            hinge_x = vis_x1 + 80
            hinge_y = vis_y2 - 30
            door_len = 360
            door_end_x = hinge_x + door_len * math.cos(door_angle - math.pi/2)
            door_end_y = hinge_y + door_len * math.sin(door_angle - math.pi/2)

            draw.line([(hinge_x, hinge_y), (door_end_x, door_end_y)], fill="#38bdf8", width=18)
            draw.ellipse([hinge_x - 14, hinge_y - 14, hinge_x + 14, hinge_y + 14], fill="#f59e0b", outline="#fef08a", width=3)

            # Contact Pulse Ring
            pulse_r = int(14 + 10 * math.sin(scene_t * 8))
            draw.ellipse([npc_cx - 40 - pulse_r, npc_cy - pulse_r, npc_cx - 40 + pulse_r, npc_cy + pulse_r], outline="#ef4444", width=3)
            draw.ellipse([npc_cx - 40 - 8, npc_cy - 8, npc_cx - 40 + 8, npc_cy + 8], fill="#ef4444")
            draw.text((npc_cx - 40, npc_cy - 40), "ТОЧКА КОНТАКТА", fill="#f87171", font=self.font_mono_small, anchor="mm")

            # Subtitle
            self.draw_subtitles_with_highlight(draw, "В МОМЕНТ УДАРА КАПСУЛУ", "ЗАЖАЛО В СТЕНУ")

        elif scene_idx == 2:
            # SCENE 3: DAMAGE OVERLOAD SPIKE
            self.draw_rounded_card(draw, card_x1, cur_y1, card_x2, cur_y2, radius=28, fill="#0f172acc", outline="#ef444455", width=2)
            self.draw_badge(draw, card_x1 + 36, cur_y1 + 36, "СЦЕНА 3: ПЕРЕГРУЗКА ИМПУЛЬСА", bg_color="#0f172a", text_color="#f87171", border_color="#dc2626")
            draw.text((card_x1 + 36, cur_y1 + 105), "Импульс сжатия превысил максимум", fill="#ffffff", font=self.font_title)

            # Animated Damage Counter
            count_t = ease_out_cubic(min(1.0, scene_t / 0.8))
            current_dmg = int(100 + count_t * (9999 - 100))

            counter_box_y1 = cur_y1 + 175
            counter_box_y2 = cur_y2 - 36
            draw.rounded_rectangle([card_x1 + 36, counter_box_y1, card_x2 - 36, counter_box_y2], radius=18, fill="#1c1017", outline="#ef4444", width=2)

            draw.text((self.width // 2, counter_box_y1 + 75), f"{current_dmg:,} HP".replace(",", " "), fill="#f87171", font=self.font_counter, anchor="mm")
            draw.text((self.width // 2, counter_box_y1 + 145), "РАСЧЕТНЫЙ УРОН ЗА 1 ТИК ДВИЖКА", fill="#fca5a5", font=self.font_mono_small, anchor="mm")

            # Progress Bar
            pb_x1 = card_x1 + 80
            pb_x2 = card_x2 - 80
            pb_y = counter_box_y1 + 200
            draw.rounded_rectangle([pb_x1, pb_y, pb_x2, pb_y + 20], radius=10, fill="#27272a")
            fill_w = int((pb_x2 - pb_x1) * count_t)
            if fill_w > 0:
                draw.rounded_rectangle([pb_x1, pb_y, pb_x1 + fill_w, pb_y + 20], radius=10, fill="#ef4444")

            # Subtitle
            self.draw_subtitles_with_highlight(draw, "ДВИЖОК НАНЁС", "9999 УРОНА ЗА ТИК")

        else:
            # SCENE 4: CODE FIX TERMINAL
            self.draw_rounded_card(draw, card_x1, cur_y1, card_x2, cur_y2, radius=28, fill="#0f172acc", outline="#22c55e55", width=2)
            self.draw_badge(draw, card_x1 + 36, cur_y1 + 36, "СЦЕНА 4: ИСПРАВЛЕНИЕ В КОДЕ", bg_color="#0f172a", text_color="#4ade80", border_color="#16a34a")
            draw.text((card_x1 + 36, cur_y1 + 105), "Проверка препятствий перед открытием", fill="#ffffff", font=self.font_title)

            # Code Terminal Box
            term_x1 = card_x1 + 36
            term_x2 = card_x2 - 36
            term_y1 = cur_y1 + 175
            term_y2 = cur_y2 - 36
            draw.rounded_rectangle([term_x1, term_y1, term_x2, term_y2], radius=18, fill="#090d16", outline="#1e293b", width=2)

            # Window dots
            draw.ellipse([term_x1 + 24, term_y1 + 24, term_x1 + 38, term_y1 + 38], fill="#ef4444")
            draw.ellipse([term_x1 + 48, term_y1 + 24, term_x1 + 62, term_y1 + 38], fill="#f59e0b")
            draw.ellipse([term_x1 + 72, term_y1 + 24, term_x1 + 86, term_y1 + 38], fill="#22c55e")

            # Line 1: Wrong
            draw.rounded_rectangle([term_x1 + 24, term_y1 + 60, term_x2 - 24, term_y1 + 115], radius=10, fill="#7f1d1d44", outline="#ef444466", width=1)
            draw.text((term_x1 + 40, term_y1 + 87), "[-] door.force_push(target: npc, mass: INF)", fill="#f87171", font=self.font_mono, anchor="lm")

            # Line 2: Fixed (Glows green)
            draw.rounded_rectangle([term_x1 + 24, term_y1 + 130, term_x2 - 24, term_y1 + 185], radius=10, fill="#14532d55", outline="#22c55e", width=2)
            draw.text((term_x1 + 40, term_y1 + 157), "[+] if (!door.has_obstacle()) door.open()", fill="#4ade80", font=self.font_mono, anchor="lm")

            # Subtitle
            self.draw_subtitles_with_highlight(draw, "ФИКС: ДВЕРЬ ДОЛЖНА", "ПРОВЕРЯТЬ ПРЕПЯТСТВИЯ")

        return img


def render_test_clip(gameplay_path: Path, output_mp4: Path, total_duration: float = 12.0):
    gameplay_path = Path(gameplay_path)
    output_mp4 = Path(output_mp4)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    renderer = MotionUIRenderer()
    total_frames = int(total_duration * FPS)

    print(f"\n🎬 Рендеринг Motion UI демо-клипа ({total_duration:.1f} сек, {total_frames} кадров)...")

    # Launch FFmpeg pipe with NVENC GPU encoding
    cmd = [
        FFMPEG_PATH, "-y",
        # Input 0: Background gameplay video (looped)
        "-stream_loop", "-1",
        "-i", str(gameplay_path),
        # Input 1: Motion UI raw frames pipe
        "-f", "rawvideo",
        "-pix_fmt", "rgba",
        "-s", f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "-r", str(FPS),
        "-i", "pipe:0",
        "-filter_complex",
        # Top half blurred background + sharp overlay
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=24:6[bg];"
        f"[0:v]scale=1020:-1[fg];"
        f"[bg][fg]overlay=(W-w)/2:200[comp_bg];"
        f"[comp_bg][1:v]overlay=0:0[v_out]",
        "-map", "[v_out]",
        "-c:v", VIDEO_CODEC,
        "-preset", VIDEO_PRESET,
        "-cq", VIDEO_CQ,
        "-t", str(total_duration),
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f_idx in range(total_frames):
        t = f_idx / FPS
        frame_img = renderer.render_overlay_frame(t)
        proc.stdin.write(frame_img.tobytes())

        if f_idx % 60 == 0:
            pct = int((f_idx / total_frames) * 100)
            print(f"   ✓ Прогресс: {pct}% ({f_idx}/{total_frames} кадров)...")

    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed with code {proc.returncode}")

    print(f"\n✨ [УСПЕХ] Тестовый Motion UI ролик готов: {output_mp4}")


if __name__ == "__main__":
    gp_file = Path("assets/downloads/cyberpunk_door_kill.mp4")
    if not gp_file.exists():
        gp_file = Path("output/3/door_kill_glitch.mp4")

    out_file = Path("output/motion_preview/test_motion_clip.mp4")
    render_test_clip(gp_file, out_file, total_duration=12.0)
