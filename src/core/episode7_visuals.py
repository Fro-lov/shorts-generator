import subprocess
import tempfile
import os
from pathlib import Path
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class Episode7VisualsGenerator:
    def __init__(self, width: int = 1000, height: int = 540, browser_path: str = CHROME_PATH):
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

    def render_card1_causes(self, output_path: Path) -> Path:
        """
        Card 1: Causes (Streaming Lag & State Machine NULL) in strict gray minimal style.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border-radius: 24px;
            padding: 32px 38px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">
                    ПОЧЕМУ АНИМАЦИЯ НЕ ЗАГРУЗИЛАСЬ?
                </div>
                <div style="font-size: 20px; font-weight: 800; color: #71717a; font-family: monospace;">
                    ЧАСТЬ 1/2
                </div>
            </div>

            <!-- 2 Large Block Rows -->
            <div style="display: flex; flex-direction: column; gap: 16px; margin: 8px 0;">
                
                <!-- Block 1 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #38bdf8;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #38bdf8;">
                            1. Задержка стриминга памяти
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #94a3b8; font-weight: 700;">
                            VRAM Lag
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Мир RDR гигантский — файл анимации верховой езды не успел считаться с диска за 1 кадр.
                    </div>
                </div>

                <!-- Block 2 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #f59e0b;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #f59e0b;">
                            2. Сбой State Machine графа
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #94a3b8; font-weight: 700;">
                            NULL Pointer
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Граф перешел в режим езды, но ссылка на анимационный клип вернула пустоту (NULL).
                    </div>
                </div>

            </div>

            <!-- Minimal Footer Note -->
            <div style="
                background: #1e2126;
                border-radius: 12px;
                padding: 10px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 19px;
                color: #a1a1aa;
                font-weight: 700;
            ">
                <span>Движок не получает кадров движения</span>
                <span style="color: #f87171; font-family: monospace; font-weight: 800;">AnimClip == nullptr</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_fallback(self, output_path: Path) -> Path:
        """
        Card 2: Fail-safe Protection & Bind Pose explanation in strict gray minimal style.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border-radius: 24px;
            padding: 32px 38px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">
                    ЗАЩИТА ДВИЖКА ОТ КРАША
                </div>
                <div style="font-size: 20px; font-weight: 800; color: #71717a; font-family: monospace;">
                    ЧАСТЬ 2/2
                </div>
            </div>

            <!-- Large Content Blocks -->
            <div style="display: flex; flex-direction: column; gap: 16px; margin: 8px 0;">
                
                <!-- Fail Safe Card -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #22c55e;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #22c55e;">
                            3. Защитный Fallback (Fail-Safe)
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #86efac; font-weight: 700;">
                            Zero Crash
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Чтобы игра не вылетела с ошибкой, движок сбрасывает все углы суставов в <span style="white-space: nowrap; color: #ffffff; font-weight: 800;">(0°, 0°, 0°)</span>.
                    </div>
                </div>

                <!-- Summary Big Card -->
                <div style="
                    background: #272a30;
                    border: 2px solid #3f3f46;
                    border-radius: 14px;
                    padding: 18px 24px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <div>
                        <div style="font-size: 24px; font-weight: 900; color: #ffffff;">
                            Т-поза = базовая поза скелета
                        </div>
                        <div style="font-size: 18px; color: #a1a1aa; font-weight: 600; margin-top: 2px;">
                            Это предохранитель, пока нужный файл догружается в память.
                        </div>
                    </div>
                    <div style="background: #18181b; border: 1.5px solid #22c55e; padding: 8px 16px; border-radius: 10px; font-size: 19px; font-family: monospace; font-weight: 900; color: #4ade80; white-space: nowrap;">
                        Bind Pose
                    </div>
                </div>

            </div>

            <!-- Footer Badge -->
            <div style="
                background: #1e2126;
                border-radius: 12px;
                padding: 10px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 19px;
                font-weight: 800;
            ">
                <span style="color: #ffffff;">ИТОГ: Т-поза спасает игру от вылетов при лагах памяти</span>
                <span style="color: #38bdf8; font-family: monospace;">BoneRot = 0°</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card1_causes_en(self, output_path: Path) -> Path:
        """
        Card 1: Causes (English) in strict minimal dark style.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border-radius: 24px;
            padding: 32px 38px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">
                    WHY DID THE ANIMATION FAIL?
                </div>
                <div style="font-size: 20px; font-weight: 800; color: #71717a; font-family: monospace;">
                    PART 1/2
                </div>
            </div>

            <!-- 2 Large Block Rows -->
            <div style="display: flex; flex-direction: column; gap: 16px; margin: 8px 0;">
                
                <!-- Block 1 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #38bdf8;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #38bdf8;">
                            1. VRAM Memory Streaming Lag
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #94a3b8; font-weight: 700;">
                            VRAM Lag
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        RDR world is massive — horse riding clip didn't stream from disk to VRAM in time.
                    </div>
                </div>

                <!-- Block 2 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #f59e0b;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #f59e0b;">
                            2. Animation State Machine Fault
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #94a3b8; font-weight: 700;">
                            NULL Pointer
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Transition switched to riding, but clip reference returned NULL (condition conflict).
                    </div>
                </div>

            </div>

            <!-- Minimal Footer Note -->
            <div style="
                background: #1e2126;
                border-radius: 12px;
                padding: 10px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 19px;
                color: #a1a1aa;
                font-weight: 700;
            ">
                <span>Engine received no motion keyframes</span>
                <span style="color: #f87171; font-family: monospace; font-weight: 800;">AnimClip == nullptr</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_fallback_en(self, output_path: Path) -> Path:
        """
        Card 2: Fail-safe Protection & Bind Pose (English) in strict minimal dark style.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border-radius: 24px;
            padding: 32px 38px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-size: 34px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">
                    ENGINE FAIL-SAFE PROTECTION
                </div>
                <div style="font-size: 20px; font-weight: 800; color: #71717a; font-family: monospace;">
                    PART 2/2
                </div>
            </div>

            <!-- Large Content Blocks -->
            <div style="display: flex; flex-direction: column; gap: 16px; margin: 8px 0;">
                
                <!-- Fail Safe Card -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #22c55e;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #22c55e;">
                            3. Safety Fallback (Zero Crash)
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #86efac; font-weight: 700;">
                            Zero Crash
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Instead of crashing or freezing, engine resets all bone angles to <span style="white-space: nowrap; color: #ffffff; font-weight: 800;">(0°, 0°, 0°)</span>.
                    </div>
                </div>

                <!-- Summary Big Card -->
                <div style="
                    background: #272a30;
                    border: 2px solid #3f3f46;
                    border-radius: 14px;
                    padding: 18px 24px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <div>
                        <div style="font-size: 24px; font-weight: 900; color: #ffffff;">
                            T-Pose = Default Skeleton Bind Pose
                        </div>
                        <div style="font-size: 18px; color: #a1a1aa; font-weight: 600; margin-top: 2px;">
                            It's a protective fuse holding the frame while assets finish loading.
                        </div>
                    </div>
                    <div style="background: #18181b; border: 1.5px solid #22c55e; padding: 8px 16px; border-radius: 10px; font-size: 19px; font-family: monospace; font-weight: 900; color: #4ade80; white-space: nowrap;">
                        Bind Pose
                    </div>
                </div>

            </div>

            <!-- Footer Badge -->
            <div style="
                background: #1e2126;
                border-radius: 12px;
                padding: 10px 20px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 19px;
                font-weight: 800;
            ">
                <span style="color: #ffffff;">RESULT: T-Pose saves the engine from fatal crashes</span>
                <span style="color: #38bdf8; font-family: monospace;">BoneRot = 0°</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

