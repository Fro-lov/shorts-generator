import subprocess
import tempfile
import os
from pathlib import Path
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


class Episode8VisualsGenerator:
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

    def render_card1_detach(self, output_path: Path) -> Path:
        """
        Card 1: Socket Detach & Collider Overlap in strict graphite mobile style.
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
                    РАЗРЫВ ИЕРАРХИИ СОКЕТОВ
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
                    border-left: 6px solid #f87171;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #f87171;">
                            1. Коллизия балки (Head Overlap)
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #fca5a5; font-weight: 700;">
                            Static Mesh Hit
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Капсула персонажа врезается в балку ворот. В движке нет триггера падения с седла (Dismount).
                    </div>
                </div>

                <!-- Block 2 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #38bdf8;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #38bdf8;">
                            2. Срыв привязки к седлу (Socket Detach)
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #94a3b8; font-weight: 700;">
                            Transform Freeze
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Координаты самурая блокируются в воздухе, а конь продолжает путь по инерции.
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
                <span>Персонаж зафиксирован коллизией</span>
                <span style="color: #f87171; font-family: monospace; font-weight: 800;">AttachToSocket = FAILED</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_camera(self, output_path: Path) -> Path:
        """
        Card 2: Blind Follow Camera & Mount Autonomy in strict graphite mobile style.
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
                    СЛЕПАЯ КАМЕРА СЛЕДОВАНИЯ
                </div>
                <div style="font-size: 20px; font-weight: 800; color: #71717a; font-family: monospace;">
                    ЧАСТЬ 2/2
                </div>
            </div>

            <!-- Large Content Blocks -->
            <div style="display: flex; flex-direction: column; gap: 16px; margin: 8px 0;">
                
                <!-- Block 1 -->
                <div style="
                    background: #1e2126;
                    border-left: 6px solid #f59e0b;
                    border-radius: 14px;
                    padding: 18px 24px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <div style="font-size: 26px; font-weight: 900; color: #f59e0b;">
                            3. Таргет камеры: Лошадь (Mount Root)
                        </div>
                        <div style="font-family: monospace; font-size: 18px; color: #fde68a; font-weight: 700;">
                            CameraRig Target
                        </div>
                    </div>
                    <div style="font-size: 21px; color: #e2e8f0; font-weight: 600; line-height: 1.35;">
                        Камера следит за транспортом, а не за игроком. Она не замечает пропажу наездника.
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
                            Конь не проверяет наличие всадника
                        </div>
                        <div style="font-size: 18px; color: #a1a1aa; font-weight: 600; margin-top: 2px;">
                            Контроллер скакуна автономно завершает переход моста.
                        </div>
                    </div>
                    <div style="background: #18181b; border: 1.5px solid #22c55e; padding: 8px 16px; border-radius: 10px; font-size: 19px; font-family: monospace; font-weight: 900; color: #4ade80; white-space: nowrap;">
                        Horse Autonomous
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
                <span style="color: #ffffff;">ИТОГ: Оператор уехал с конем, оставив самурая позади</span>
                <span style="color: #38bdf8; font-family: monospace;">Target = HorseActor</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card3_fix(self, output_path: Path) -> Path:
        """
        Card 3: Code Card Fix in strict graphite style.
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border-radius: 24px;
            padding: 28px 36px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div style="font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: -0.5px;">
                    ИСПРАВЛЕНИЕ В КОДЕ ДВИЖКА
                </div>
                <div style="font-size: 18px; font-weight: 800; color: #22c55e; font-family: monospace;">
                    BUG FIX
                </div>
            </div>

            <!-- Code Comparison -->
            <div style="display: flex; flex-direction: column; gap: 14px; margin: 4px 0;">
                
                <!-- Wrong Code -->
                <div style="
                    background: #1c1517;
                    border-left: 6px solid #ef4444;
                    border-radius: 12px;
                    padding: 14px 20px;
                    font-family: monospace;
                ">
                    <div style="font-size: 18px; font-weight: 900; color: #f87171; margin-bottom: 6px;">
                        [-] БАГ: Лошадь скачет без проверки всадника
                    </div>
                    <div style="font-size: 20px; color: #fca5a5; font-weight: 700;">
                        Horse.MoveForward(); // Камера и конь уезжают в закат
                    </div>
                </div>

                <!-- Fixed Code -->
                <div style="
                    background: #132219;
                    border-left: 6px solid #22c55e;
                    border-radius: 12px;
                    padding: 14px 20px;
                    font-family: monospace;
                ">
                    <div style="font-size: 18px; font-weight: 900; color: #4ade80; margin-bottom: 6px;">
                        [+] ПРАВИЛЬНО: Проверка сокета и сброс в Ragdoll
                    </div>
                    <div style="font-size: 20px; color: #86efac; font-weight: 700; line-height: 1.4;">
                        if (!Rider.IsAttached()) &#123;<br>
                        &nbsp;&nbsp;Horse.Stop();<br>
                        &nbsp;&nbsp;Rider.EnableRagdoll(); // Самурай падает на землю<br>
                        &#125;
                    </div>
                </div>

            </div>

            <!-- Footer Badge -->
            <div style="
                background: #1e2126;
                border-radius: 12px;
                padding: 8px 18px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 18px;
                color: #a1a1aa;
                font-weight: 700;
            ">
                <span>Безопасный Ragdoll при столкновении с препятствием</span>
                <span style="color: #22c55e; font-family: monospace;">Pass Collision Check</span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)


if __name__ == "__main__":
    from config.settings import OUTPUT_DIR
    vis = Episode8VisualsGenerator()
    test_dir = OUTPUT_DIR / "8" / "visuals"
    vis.render_card1_detach(test_dir / "card1_detach.png")
    vis.render_card2_camera(test_dir / "card2_camera.png")
    vis.render_card3_fix(test_dir / "card3_fix.png")
    print("Test cards rendered successfully!")
