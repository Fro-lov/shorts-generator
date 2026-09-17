import subprocess
import tempfile
import os
from pathlib import Path
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class HTMLMotionRenderer:
    """
    Renders high-end modern CSS/SVG Motion UI cards using Headless Chrome/Edge.
    Features:
    - Glassmorphism & backdrop-blur design
    - CSS gradients, glowing borders, smooth shadows
    - SVG CAD engineering blueprints with coordinate vectors
    - Monospace code editors with syntax highlight
    - High-DPI transparent rendering
    """
    def __init__(self, width: int = 1000, height: int = 540, browser_path: str = CHROME_PATH):
        self.width = width
        self.height = height
        self.browser_path = browser_path

    def render_html_to_image(self, html_content: str, output_image_path: Path) -> Path:
        output_image_path = Path(output_image_path).resolve()
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Montserrat, Arial, sans-serif;
    }}
    body {{
        width: {self.width}px;
        height: {self.height}px;
        background: transparent;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""

        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as f:
            temp_html_path = f.name
            f.write(full_html)

        try:
            cmd = [
                self.browser_path,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--default-background-color=00000000",
                f"--window-size={self.width},{self.height}",
                f"--screenshot={str(output_image_path)}",
                f"file:///{Path(temp_html_path).resolve().as_posix()}"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print("Browser stderr:", res.stderr)
        finally:
            if os.path.exists(temp_html_path):
                os.remove(temp_html_path)

        return output_image_path

    def render_scheme1a_normal(self, output_path: Path, lang: str = "ru") -> Path:
        badge_text = "НОРМА: 3D-ОСИ ВРАЩЕНИЯ" if lang == "ru" else "NORMAL: 3D ROTATION AXES"
        title_text = "Раздельные оси руления и качения" if lang == "ru" else "Decoupled Steering & Roll Axes"
        sub_desc = "Ось качения (Pitch) и ось поворота (Yaw) работают отдельно" if lang == "ru" else "Pitch roll axis and Yaw steer axis work independently"
        rule_text = "ИТОГ: Колесо катится строго вперёд по асфальту" if lang == "ru" else "RESULT: Wheel rolls straight forward along tarmac"

        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, rgba(6, 40, 25, 0.96) 0%, rgba(15, 23, 42, 0.94) 100%);
            border: 2.5px solid #22c55e;
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), inset 0 0 35px rgba(34, 197, 94, 0.15);
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="
                    display: inline-block;
                    padding: 6px 18px;
                    background: rgba(34, 197, 94, 0.2);
                    border: 2px solid #22c55e;
                    border-radius: 8px;
                    color: #4ade80;
                    font-size: 18px;
                    font-weight: 900;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                ">{badge_text}</div>
                <h1 style="color: #ffffff; font-size: 32px; font-weight: 900;">{title_text}</h1>
            </div>

            <!-- Visual Center -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 40px; margin: 10px 0;">
                <svg width="280" height="150" viewBox="0 0 280 150">
                    <line x1="20" y1="75" x2="260" y2="75" stroke="#4ade80" stroke-width="5" stroke-dasharray="8,6"/>
                    <polygon points="270,75 255,66 255,84" fill="#4ade80"/>
                    <rect x="95" y="15" width="90" height="120" rx="20" fill="#0f172a" stroke="#22c55e" stroke-width="4"/>
                    <circle cx="140" cy="75" r="18" fill="#22c55e" stroke="#ffffff" stroke-width="3"/>
                </svg>
                <div style="color: #bbf7d0; font-size: 24px; font-weight: 800; max-width: 500px; line-height: 1.4;">
                    {sub_desc}
                </div>
            </div>

            <div style="
                background: rgba(15, 23, 42, 0.9);
                border: 1.5px solid #22c55e;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                color: #86efac;
                font-size: 20px;
                font-weight: 800;
            ">{rule_text}</div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_scheme1b_glitch(self, output_path: Path, lang: str = "ru") -> Path:
        badge_text = "БАГ: СБОЙ 4D КВАТЕРНИОНА" if lang == "ru" else "GLITCH: 4D QUATERNION ERROR"
        title_text = "Сложение углов вывернуло ось колеса!" if lang == "ru" else "Rotation Mix Tangled Local 4D Axis!"
        sub_desc = "Умножение кватернионов смешало оси и направило вращение вверх" if lang == "ru" else "Quaternion multiplication tangled yaw and pitch into vertical propeller axis"
        rule_text = "ИТОГ: Колесо вращается вертикально как вертолёт" if lang == "ru" else "RESULT: Wheel spins vertically like a helicopter rotor"

        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, rgba(50, 10, 20, 0.96) 0%, rgba(15, 23, 42, 0.94) 100%);
            border: 2.5px solid #ef4444;
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), inset 0 0 35px rgba(239, 68, 68, 0.15);
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="
                    display: inline-block;
                    padding: 6px 18px;
                    background: rgba(239, 68, 68, 0.2);
                    border: 2px solid #ef4444;
                    border-radius: 8px;
                    color: #f87171;
                    font-size: 18px;
                    font-weight: 900;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                ">{badge_text}</div>
                <h1 style="color: #ffffff; font-size: 32px; font-weight: 900;">{title_text}</h1>
            </div>

            <!-- Visual Center -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 40px; margin: 10px 0;">
                <svg width="280" height="150" viewBox="0 0 280 150">
                    <line x1="140" y1="140" x2="140" y2="15" stroke="#f87171" stroke-width="5" stroke-dasharray="8,6"/>
                    <polygon points="140,8 131,22 149,22" fill="#f87171"/>
                    <ellipse cx="140" cy="75" rx="120" ry="32" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10,6"/>
                    <rect x="40" y="52" width="200" height="46" rx="14" fill="#27141e" stroke="#ef4444" stroke-width="4"/>
                    <circle cx="140" cy="75" r="18" fill="#ef4444" stroke="#ffffff" stroke-width="3"/>
                </svg>
                <div style="color: #fca5a5; font-size: 24px; font-weight: 800; max-width: 500px; line-height: 1.4;">
                    {sub_desc}
                </div>
            </div>

            <div style="
                background: rgba(15, 23, 42, 0.9);
                border: 1.5px solid #ef4444;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                color: #fca5a5;
                font-size: 20px;
                font-weight: 800;
            ">{rule_text}</div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_scheme2a_physics(self, output_path: Path, lang: str = "ru") -> Path:
        badge_text = "ФИЗИЧЕСКИЙ ДВИЖОК" if lang == "ru" else "PHYSICS SOLVER"
        title_text = "Физический луч сцепления (Raycast Collider)" if lang == "ru" else "Physics Raycast Traction Solver"
        desc_text = "Сцепление с дорогой: 100% ИДЕАЛ • Машина слушается руля" if lang == "ru" else "Road Grip: 100% PERFECT • Full traction and steering response"
        rule_text = "ИТОГ: Физический солвер работает автономно и стабильно" if lang == "ru" else "RESULT: Physics solver operates independently with full grip"

        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, rgba(6, 40, 25, 0.96) 0%, rgba(15, 23, 42, 0.94) 100%);
            border: 2.5px solid #22c55e;
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), inset 0 0 35px rgba(34, 197, 94, 0.15);
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="
                    display: inline-block;
                    padding: 6px 18px;
                    background: rgba(34, 197, 94, 0.2);
                    border: 2px solid #22c55e;
                    border-radius: 8px;
                    color: #4ade80;
                    font-size: 18px;
                    font-weight: 900;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                ">{badge_text}</div>
                <h1 style="color: #ffffff; font-size: 32px; font-weight: 900;">{title_text}</h1>
            </div>

            <!-- Big KPI & Desc -->
            <div style="
                background: linear-gradient(180deg, rgba(5, 46, 22, 0.7) 0%, rgba(6, 78, 59, 0.4) 100%);
                border: 2px solid #22c55e;
                border-radius: 20px;
                padding: 24px;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: space-around;
            ">
                <div style="font-family: 'Consolas', monospace; font-size: 74px; font-weight: 900; color: #4ade80;">
                    GRIP: 100%
                </div>
                <div style="color: #bbf7d0; font-size: 24px; font-weight: 800; max-width: 440px; line-height: 1.4; text-align: left;">
                    {desc_text}
                </div>
            </div>

            <div style="
                background: rgba(15, 23, 42, 0.9);
                border: 1.5px solid #22c55e;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                color: #86efac;
                font-size: 20px;
                font-weight: 800;
            ">{rule_text}</div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_scheme2b_visual(self, output_path: Path, lang: str = "ru") -> Path:
        badge_text = "ГРАФИЧЕСКИЙ ДВИЖОК" if lang == "ru" else "GRAPHICS RENDER ENGINE"
        title_text = "3D-модель колеса крутится как волчок" if lang == "ru" else "3D Wheel Mesh Spinning Like a Blender"
        desc_text = "Режим: НИЖНИЙ БРЕЙК • Трёхмерная сетка режет асфальт" if lang == "ru" else "Mode: LOWER BREAKDANCE • 3D mesh slicing through tarmac"
        rule_text = "ИТОГ: Графический баг не ломает физику машины" if lang == "ru" else "RESULT: Visual glitch does not disrupt driving physics"

        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, rgba(60, 10, 20, 0.96) 0%, rgba(20, 10, 30, 0.94) 100%);
            border: 2.5px solid #ef4444;
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), inset 0 0 35px rgba(239, 68, 68, 0.15);
            padding: 30px 40px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="
                    display: inline-block;
                    padding: 6px 18px;
                    background: rgba(239, 68, 68, 0.2);
                    border: 2px solid #ef4444;
                    border-radius: 8px;
                    color: #f87171;
                    font-size: 18px;
                    font-weight: 900;
                    letter-spacing: 1px;
                    margin-bottom: 10px;
                ">{badge_text}</div>
                <h1 style="color: #ffffff; font-size: 32px; font-weight: 900;">{title_text}</h1>
            </div>

            <!-- Big KPI & Desc -->
            <div style="
                background: linear-gradient(180deg, rgba(69, 10, 10, 0.7) 0%, rgba(127, 29, 29, 0.4) 100%);
                border: 2px solid #ef4444;
                border-radius: 20px;
                padding: 24px;
                text-align: center;
                display: flex;
                align-items: center;
                justify-content: space-around;
            ">
                <div style="font-family: 'Consolas', monospace; font-size: 74px; font-weight: 900; color: #f87171;">
                    3 500 RPM
                </div>
                <div style="color: #fecaca; font-size: 24px; font-weight: 800; max-width: 440px; line-height: 1.4; text-align: left;">
                    {desc_text}
                </div>
            </div>

            <div style="
                background: rgba(15, 23, 42, 0.9);
                border: 1.5px solid #ef4444;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                color: #fca5a5;
                font-size: 20px;
                font-weight: 800;
            ">{rule_text}</div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_scheme3_code_fix(self, output_path: Path, lang: str = "ru") -> Path:
        badge_text = "ФИКС В КОДЕ" if lang == "ru" else "CODE FIX"
        title_text = "Нормализация кватерниона колеса" if lang == "ru" else "Wheel Quaternion Normalization"
        rule_text = "РЕЗУЛЬТАТ: Оси разделены, колесо катится ровно по асфальту" if lang == "ru" else "RESULT: Axes decoupled, wheel rolls forward on tarmac"
        comment_err = "// ОШИБКА: Смешение осей в Эйлеровых углах!" if lang == "ru" else "// ERROR: Axis entanglement in Euler angles!"
        comment_fix = "// ФИКС: Раздельное умножение чистых осей!" if lang == "ru" else "// FIX: Multiply decoupled pure quaternions!"

        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: linear-gradient(135deg, rgba(9, 13, 22, 0.98) 0%, rgba(15, 23, 42, 0.96) 100%);
            border: 2.5px solid rgba(34, 197, 94, 0.5);
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), inset 0 0 35px rgba(34, 197, 94, 0.15);
            padding: 28px 36px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        ">
            <!-- Header -->
            <div>
                <div style="
                    display: inline-block;
                    padding: 6px 18px;
                    background: rgba(22, 163, 74, 0.2);
                    border: 2px solid #16a34a;
                    border-radius: 8px;
                    color: #4ade80;
                    font-size: 19px;
                    font-weight: 900;
                    letter-spacing: 1px;
                    margin-bottom: 8px;
                ">{badge_text}</div>
                <h1 style="color: #ffffff; font-size: 32px; font-weight: 900;">{title_text}</h1>
            </div>

            <!-- Terminal Window (Extra Large & Bold for Phone Screens) -->
            <div style="
                background: #020617;
                border: 2px solid #334155;
                border-radius: 18px;
                padding: 20px 24px;
                box-shadow: 0 12px 35px rgba(0,0,0,0.6);
            ">
                <!-- Mac dots -->
                <div style="display: flex; align-items: center; gap: 9px; margin-bottom: 14px;">
                    <div style="width: 14px; height: 14px; border-radius: 50%; background: #ef4444;"></div>
                    <div style="width: 14px; height: 14px; border-radius: 50%; background: #f59e0b;"></div>
                    <div style="width: 14px; height: 14px; border-radius: 50%; background: #22c55e;"></div>
                    <span style="font-family: 'Consolas', monospace; color: #94a3b8; font-size: 17px; font-weight: 700; margin-left: 10px;">WheelTransform.cpp</span>
                </div>

                <!-- Wrong Line -->
                <div style="
                    background: rgba(127, 29, 29, 0.35);
                    border: 1.5px solid rgba(239, 68, 68, 0.5);
                    border-radius: 12px;
                    padding: 12px 18px;
                    margin-bottom: 12px;
                    font-family: 'Consolas', monospace;
                    font-size: 22px;
                    line-height: 1.35;
                ">
                    <div style="color: #f87171; font-weight: 800;">[-] wheel.rotation = Quaternion.Euler(speed, steer, roll);</div>
                    <div style="color: #fca5a5; font-size: 18px; font-weight: 700; margin-top: 4px;">{comment_err}</div>
                </div>

                <!-- Fixed Line -->
                <div style="
                    background: rgba(20, 83, 45, 0.4);
                    border: 2px solid #22c55e;
                    border-radius: 12px;
                    padding: 12px 18px;
                    font-family: 'Consolas', monospace;
                    font-size: 22px;
                    line-height: 1.35;
                ">
                    <div style="color: #4ade80; font-weight: 800;">[+] wheel.rotation = SteerQuat(yaw) * RollQuat(pitch);</div>
                    <div style="color: #86efac; font-size: 18px; font-weight: 700; margin-top: 4px;">{comment_fix}</div>
                </div>
            </div>

            <!-- Footer Rule -->
            <div style="
                background: rgba(15, 23, 42, 0.9);
                border: 1.5px solid #22c55e;
                border-radius: 12px;
                padding: 12px;
                text-align: center;
                color: #4ade80;
                font-size: 20px;
                font-weight: 800;
            ">{rule_text}</div>
        </div>
        """
        return self.render_html_to_image(html, output_path)
