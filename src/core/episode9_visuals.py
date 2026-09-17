import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class Episode9VisualsGenerator:
    """
    Vertical Top-to-Bottom Diagram Generator for Mobile Shorts (1080x1920).
    Occupies the top 2/3 of the vertical screen (1000 x 1280 px), with extra
    large mobile typography filling the vertical space seamlessly.
    """
    def __init__(self, width: int = 1000, height: int = 1280, browser_path: str = CHROME_PATH):
        self.width = width
        self.height = height
        self.browser_path = browser_path

    def render_html_to_image(self, html_content: str, output_image_path: Path) -> Path:
        output_image_path = Path(output_image_path).resolve()
        output_image_path.parent.mkdir(parents=True, exist_ok=True)

        full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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

        with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as f_temp:
            temp_html_path = f_temp.name
            f_temp.write(full_html)

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

    def render_card1_camera(self, output_path: Path) -> Path:
        """
        Card 1: Top-to-Bottom Vertical Architecture with Extra Large Typography.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 42px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2.5px solid #232730; padding-bottom: 22px;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; white-space: nowrap;">
                    КАК КАМЕРА ПРОЕЦИРУЕТ 3D НА ЭКРАН
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #38bdf8; font-family: monospace; background: #0f172a; border: 2px solid #0284c7; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    1. МАТЕМАТИКА
                </div>
            </div>

            <!-- STEP 1: 3D World (Top Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 34px 34px; border-left: 10px solid #38bdf8; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #38bdf8;">
                        ШАГ 1: 3D-МИР (ИГРОВОЙ ДВИЖОК)
                    </div>
                    <div style="font-size: 22px; font-weight: 800; color: #94a3b8; font-family: monospace;">
                        World Space (X, Y, Z)
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; gap: 32px;">
                    <div style="width: 175px; height: 165px; background: #0f1115; border: 3px dashed #475569; border-radius: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 66px;">🎥</span>
                        <span style="font-size: 22px; font-weight: 900; color: #38bdf8;">Камера 3D</span>
                    </div>

                    <div style="flex: 1; display: flex; flex-direction: column; gap: 14px;">
                        <div style="font-size: 28px; font-weight: 700; color: #f1f5f9; line-height: 1.35;">
                            Движок считывает 3D-позицию объектов в мировом пространстве.
                        </div>
                        <div style="background: #450a0a; border: 2px solid #ef4444; border-radius: 12px; padding: 10px 22px; display: inline-flex; align-items: center; gap: 12px; width: fit-content;">
                            <span style="font-size: 26px;">⚠️</span>
                            <span style="font-size: 24px; font-weight: 900; color: #fca5a5;">Ошибка: Деление на 0 в шейдере!</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- CONNECTOR ARROW DOWN (Formula & Math Transition) -->
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; margin: 2px 0;">
                <div style="background: #0f1115; border: 2.5px solid #334155; padding: 14px 42px; border-radius: 16px; font-family: monospace; font-size: 30px; font-weight: 900; color: #fbbf24; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
                    Экран = 3D × Матрица Проекции
                </div>
                
                <div style="display: flex; align-items: center; gap: 24px;">
                    <div style="color: #ef4444; font-size: 44px; font-weight: 900; line-height: 1;">⬇ ⬇ ⬇</div>
                    <div style="background: #7f1d1d66; border: 2px solid #ef4444; color: #fecaca; padding: 10px 26px; border-radius: 14px; font-size: 26px; font-weight: 900; font-family: monospace;">
                        Координаты = NaN (Бесконечность)
                    </div>
                    <div style="color: #ef4444; font-size: 44px; font-weight: 900; line-height: 1;">⬇ ⬇ ⬇</div>
                </div>
            </div>

            <!-- STEP 2: Screen Space (Bottom Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 34px 34px; border-left: 10px solid #ef4444; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #f87171;">
                        ШАГ 2: ЭКРАН МОНИТОРА
                    </div>
                    <div style="font-size: 22px; font-weight: 800; color: #94a3b8; font-family: monospace;">
                        Screen Space [-1, 1]
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; gap: 32px;">
                    <!-- Screen Box -->
                    <div style="width: 300px; height: 175px; background: #000000; border: 3.5px solid #ef4444; border-radius: 20px; position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0; overflow: visible;">
                        <span style="font-size: 24px; font-weight: 900; color: #94a3b8;">Зона экрана [-1, 1]</span>
                        <span style="font-size: 18px; color: #64748b; font-family: monospace;">(Видимая область)</span>
                        <!-- Out of bounds tag -->
                        <div style="position: absolute; right: -24px; top: -20px; background: #dc2626; color: #ffffff; padding: 8px 18px; border-radius: 10px; font-size: 20px; font-weight: 900; box-shadow: 0 8px 20px rgba(0,0,0,0.7); border: 2px solid #fecaca; white-space: nowrap;">
                            🚀 Улетели за экран!
                        </div>
                    </div>

                    <!-- GPU Reaction -->
                    <div style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
                        <div style="font-size: 28px; font-weight: 900; color: #fca5a5; line-height: 1.35;">
                            Видеокарта: <span style="color: #ffffff;">«Координаты сломаны — рисовать не надо»</span>
                        </div>
                        <div style="font-size: 24px; color: #cbd5e1; line-height: 1.35;">
                            Screen Space Culling отсекает отрисовку, оставляя старое изображение.
                        </div>
                    </div>
                </div>
            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">📌</span>
                    <span style="color: #94a3b8; font-size: 27px;">Итог: <b style="color: #ffffff;">Пиксели аномалии не обновляются</b></span>
                </div>
                <div style="color: #ef4444; font-size: 25px; font-weight: 900; font-family: monospace; background: #450a0a66; border: 2px solid #ef4444; padding: 8px 20px; border-radius: 12px;">
                    Screen Space Culling Fail
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_buffer(self, output_path: Path) -> Path:
        """
        Card 2: Top-to-Bottom Vertical Buffer trail explanation with Extra Large Typography.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 42px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2.5px solid #232730; padding-bottom: 22px;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; white-space: nowrap;">
                    ПОЧЕМУ РУКА ОСТАВЛЯЕТ СЛЕД?
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #38bdf8; font-family: monospace; background: #0f172a; border: 2px solid #0284c7; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    2. БУФЕР КАДРА
                </div>
            </div>

            <!-- STEP 1: Hand appears (Top Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 36px 34px; border-left: 10px solid #38bdf8; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #38bdf8;">
                        КАДР 1: ВЗМАХ РУКИ
                    </div>
                    <div style="background: #0f172a; color: #38bdf8; border: 1.5px solid #0284c7; padding: 6px 16px; border-radius: 10px; font-size: 22px; font-weight: 900; font-family: monospace;">
                        Frame #100
                    </div>
                </div>

                <div style="display: flex; align-items: center; gap: 32px;">
                    <div style="width: 175px; height: 155px; background: #0f1115; border: 2.5px solid #334155; border-radius: 22px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 60px;">🧤 ➔ 🖥️</span>
                    </div>
                    <div style="font-size: 28px; color: #f1f5f9; line-height: 1.4; font-weight: 600;">
                        Рука проходит перед «дырой». Видеокарта честно записывает пиксели перчатки в память видео-буфера.
                    </div>
                </div>
            </div>

            <!-- CONNECTOR ARROW DOWN -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin: 4px 0;">
                <div style="color: #94a3b8; font-size: 42px; font-weight: 900;">⬇</div>
                <div style="background: #0f1115; border: 2px solid #334155; color: #e2e8f0; padding: 10px 32px; border-radius: 14px; font-size: 26px; font-weight: 800;">
                    Следующий кадр рендеринга
                </div>
                <div style="color: #94a3b8; font-size: 42px; font-weight: 900;">⬇</div>
            </div>

            <!-- STEP 2: Hand moved away (Bottom Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 36px 34px; border-left: 10px solid #ef4444; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #f87171;">
                        КАДР 2: РУКА УШЛА ИЗ КАДРА
                    </div>
                    <div style="background: #450a0a; color: #fca5a5; border: 1.5px solid #ef4444; padding: 6px 16px; border-radius: 10px; font-size: 22px; font-weight: 900; font-family: monospace;">
                        Frame #101 (ПУСТОТА)
                    </div>
                </div>

                <div style="display: flex; align-items: center; gap: 32px;">
                    <div style="width: 175px; height: 155px; background: #0f1115; border: 2.5px solid #ef4444; border-radius: 22px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 60px;">❌ 🧹</span>
                    </div>
                    <div style="font-size: 28px; color: #f1f5f9; line-height: 1.4; font-weight: 600;">
                        Сзади дыра. Движок <b style="color: #f87171;">не стирает старые пиксели</b>, поэтому они зависают намертво как в Windows XP!
                    </div>
                </div>
            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">🪞</span>
                    <span style="color: #94a3b8; font-size: 27px;">Эффект: <b style="color: #ffffff;">Старые пиксели не затираются</b></span>
                </div>
                <div style="color: #38bdf8; font-size: 25px; font-weight: 900; font-family: monospace; background: #0c4a6e55; border: 2px solid #0284c7; padding: 8px 20px; border-radius: 12px;">
                    Hall of Mirrors
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card3_fix(self, output_path: Path) -> Path:
        """
        Card 3: Top-to-Bottom Vertical Code & Solution comparison with Extra Large Typography.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 42px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2.5px solid #232730; padding-bottom: 22px;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px; white-space: nowrap;">
                    КАК ЭТО ПРАВИЛЬНО ИСПРАВИТЬ
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #22c55e; font-family: monospace; background: #052e16; border: 2px solid #16a34a; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    3. РЕШЕНИЕ
                </div>
            </div>

            <!-- Terminal Box (Wrong vs Fixed) -->
            <div style="display: flex; flex-direction: column; gap: 32px;">
                
                <!-- WRONG BLOCK -->
                <div style="background: #1c1f26; border-left: 10px solid #ef4444; border-radius: 24px; padding: 34px 36px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div style="font-size: 29px; font-weight: 900; color: #ef4444;">
                            [-] КАК БЫЛО В ДВИЖКЕ (БАГ)
                        </div>
                        <div style="font-family: monospace; color: #fca5a5; font-size: 22px; font-weight: 800;">
                            Shader_Cull_Pass.hlsl
                        </div>
                    </div>
                    <div style="background: #090d16; border: 2px solid #7f1d1d; border-radius: 16px; padding: 22px 26px; font-family: monospace; font-size: 28px; color: #f87171; margin-bottom: 14px;">
                        if (isnan(pixel_pos)) discard; // Пиксель брошен!
                    </div>
                    <div style="font-size: 26px; color: #cbd5e1; line-height: 1.35; font-weight: 600;">
                        Движок пропускает очистку буфера при NaN-координатах.
                    </div>
                </div>

                <!-- FIXED BLOCK -->
                <div style="background: #1c1f26; border-left: 10px solid #22c55e; border-radius: 24px; padding: 34px 36px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div style="font-size: 29px; font-weight: 900; color: #4ade80;">
                            [+] КАК НАДО (ПРАВИЛЬНЫЙ ФИКС)
                        </div>
                        <div style="font-family: monospace; color: #86efac; font-size: 22px; font-weight: 800;">
                            PostProcess_Buffer.hlsl
                        </div>
                    </div>
                    <div style="background: #090d16; border: 2px solid #22c55e; border-radius: 16px; padding: 22px 26px; font-family: monospace; font-size: 28px; color: #4ade80; margin-bottom: 14px;">
                        RenderTarget.Clear(Color::SkyVoid); // 100% Очистка
                    </div>
                    <div style="font-size: 26px; color: #cbd5e1; line-height: 1.35; font-weight: 600;">
                        Принудительная очистка всего экрана фоновым цветом перед началом каждого кадра.
                    </div>
                </div>

            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">🛡️</span>
                    <span style="color: #94a3b8; font-size: 27px;">Решение: <b style="color: #22c55e;">Full Frame Clear Buffer</b></span>
                </div>
                <div style="color: #22c55e; font-size: 25px; font-weight: 900; font-family: monospace; background: #052e1688; border: 2px solid #16a34a; padding: 8px 20px; border-radius: 12px;">
                    Clean Render 100%
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)


if __name__ == "__main__":
    out_dir = Path("e:/social/output/9/visuals")
    gen = Episode9VisualsGenerator(width=1000, height=1280)
    gen.render_card1_camera(out_dir / "card1_camera_vertical.png")
    gen.render_card2_buffer(out_dir / "card2_buffer_vertical.png")
    gen.render_card3_fix(out_dir / "card3_fix_vertical.png")
    print("Vertical cards with large fonts and perfect 1-line headers rendered successfully!")
