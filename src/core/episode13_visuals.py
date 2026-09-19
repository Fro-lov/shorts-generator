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


class Episode13VisualsGenerator:
    """
    Generates high-contrast vertical diagrams (1000x1280) for Episode 13 (CS2 Sub-Tick & Prediction Rollback):
    - Card 1: Client-Side Prediction (Local Hitmarker & Premature Despawn Animation)
    - Card 2: Server Rollback & Revert (Server Authority, Sub-tick Timestamp Validation, Revert Command)
    """

    def __init__(self, width: int = 1000, height: int = 1280):
        self.width = width
        self.height = height

    def render_html_to_image(self, html_content: str, output_image_path: Path) -> Path:
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    body {{
        background: transparent;
        width: {self.width}px;
        height: {self.height}px;
        overflow: hidden;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""
            f.write(full_html)
            temp_html_path = f.name

        try:
            output_image_path = output_image_path.resolve()
            cmd = [
                CHROME_PATH,
                "--headless=new",
                "--disable-gpu",
                "--force-device-scale-factor=1",
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

    def render_card1_client_prediction(self, output_path: Path) -> Path:
        """
        Card 1: Client-Side Prediction Flow (1000x1280)
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 3px solid #2d3340;
            border-radius: 36px;
            padding: 44px 48px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 35px 80px rgba(0, 0, 0, 0.95);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #282e3b; padding-bottom: 24px;">
                <div>
                    <h2 style="font-size: 42px; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px;">МЕХАНИКА CS2: ЭТАП 1</h2>
                    <p style="font-size: 26px; color: #94a3b8; font-weight: 600; margin-top: 6px;">Клиентское предсказание (Client Prediction)</p>
                </div>
                <div style="background: #38bdf8; color: #0f172a; padding: 12px 24px; border-radius: 16px; font-weight: 900; font-size: 24px;">
                    0 MS LAG
                </div>
            </div>

            <!-- Block 1: Input & Sub-tick timestamp -->
            <div style="
                flex: 1;
                margin-top: 24px;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #38bdf8;
                border-radius: 26px;
                padding: 30px 36px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="font-size: 34px; font-weight: 800; color: #38bdf8;">1. ЛКМ КЛИК (SUB-TICK)</span>
                    <span style="background: rgba(56,189,248,0.2); color: #38bdf8; padding: 6px 16px; border-radius: 10px; font-size: 20px; font-weight: 700;">t = 14.2ms</span>
                </div>
                <p style="font-size: 30px; color: #e2e8f0; line-height: 1.4; font-weight: 500;">
                    Твой ПК мгновенно фиксирует нажатие клавиши и ставит микросекундную метку (Sub-tick Timestamp).
                </p>
            </div>

            <!-- Connector Arrow -->
            <div style="text-align: center; margin: 10px 0; color: #fbbf24; font-size: 36px; font-weight: 900;">
                ⇓ ПРЕДСКАЗАНИЕ БЕЗ ЗАДЕРЖКИ ⇓
            </div>

            <!-- Block 2: Premature Visual hit & fall -->
            <div style="
                flex: 1;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #fbbf24;
                border-radius: 26px;
                padding: 30px 36px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="font-size: 34px; font-weight: 800; color: #fbbf24;">2. ЛОКАЛЬНЫЙ ХИТМАРКЕР</span>
                    <span style="background: rgba(251,191,36,0.2); color: #fbbf24; padding: 6px 16px; border-radius: 10px; font-size: 20px; font-weight: 700;">PREDICTED HEADSHOT</span>
                </div>
                <p style="font-size: 30px; color: #e2e8f0; line-height: 1.4; font-weight: 500;">
                    Чтобы не было отзывчивого лага, ПК <b style="color: #fff;">сразу запускает анимацию отлета врага на спавн</b>, не дожидаясь ответа сервера!
                </p>
            </div>

            <!-- Footer -->
            <div style="margin-top: 24px; background: #1f2533; border: 2px solid #3b465e; border-radius: 22px; padding: 22px 32px; display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 40px;">🎯</span>
                <span style="font-size: 26px; font-weight: 700; color: #f8fafc; line-height: 1.3;">
                    На твоем мониторе противник уже отлетает, но сервер пока ничего не знает!
                </span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_server_rollback(self, output_path: Path) -> Path:
        """
        Card 2: Server Rollback & Revert State (1000x1280)
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 3px solid #2d3340;
            border-radius: 36px;
            padding: 44px 48px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 35px 80px rgba(0, 0, 0, 0.95);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #282e3b; padding-bottom: 24px;">
                <div>
                    <h2 style="font-size: 42px; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px;">МЕХАНИКА CS2: ЭТАП 2</h2>
                    <p style="font-size: 26px; color: #94a3b8; font-weight: 600; margin-top: 6px;">Серверная отмотка и отмена выстрела (Rollback)</p>
                </div>
                <div style="background: #ef4444; color: #ffffff; padding: 12px 24px; border-radius: 16px; font-weight: 900; font-size: 24px;">
                    HIT REJECTED
                </div>
            </div>

            <!-- Block 1: Server Rollback check -->
            <div style="
                flex: 1;
                margin-top: 22px;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #ef4444;
                border-radius: 26px;
                padding: 28px 34px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 33px; font-weight: 800; color: #f87171;">1. СЕРВЕРНЫЙ РОЛЛБЭК (ROLLBACK)</span>
                    <span style="background: rgba(239,68,68,0.2); color: #f87171; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">SERVER AUTHORITY</span>
                </div>
                <p style="font-size: 29px; color: #e2e8f0; line-height: 1.35; font-weight: 500;">
                    Сервер получает пакет с пингом, отматывает мир назад на t = 14.2ms и проверяет позицию хитбокса.
                </p>
            </div>

            <!-- Connector -->
            <div style="text-align: center; margin: 8px 0; color: #ef4444; font-size: 36px; font-weight: 900;">
                ⚡ РАССИНХРОН: СЕРВЕР ФИКСИРУЕТ ПРОМАХ ⚡
            </div>

            <!-- Block 2: Revert Animation & Resurrect -->
            <div style="
                flex: 1;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #a855f7;
                border-radius: 26px;
                padding: 28px 34px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 33px; font-weight: 800; color: #c084fc;">2. ВОСКРЕШЕНИЕ И REVERT</span>
                    <span style="background: rgba(168,85,247,0.2); color: #c084fc; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">PREDICTION REJECT</span>
                </div>
                <p style="font-size: 29px; color: #e2e8f0; line-height: 1.35; font-weight: 500;">
                    Сервер шлет команду: <b style="color: #f87171;">«ТЫ МИМО!»</b> Клиент вынужден отменить анимацию и <b style="color: #fff;">поднять врага из деспавна!</b>
                </p>
            </div>

            <!-- Fix code block -->
            <div style="
                flex: 1.1;
                margin-top: 18px;
                background: #13221b;
                border: 2px solid #1a4a35;
                border-left: 12px solid #10b981;
                border-radius: 26px;
                padding: 26px 34px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 31px; font-weight: 800; color: #4ade80;">РЕШЕНИЕ: СТАБИЛЬНЫЙ PING & JITTER</span>
                    <span style="background: rgba(16,185,129,0.2); color: #4ade80; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">NET CODE</span>
                </div>
                <pre style="font-family: monospace; font-size: 26px; color: #86efac; line-height: 1.4; white-space: pre-wrap; font-weight: 700;">
if (packet_jitter > MAX_THRESHOLD) {{
    // Убираем лаги предсказания:
    Use_Wired_Ethernet(); 
    cl_interp_ratio 1;
}}</pre>
            </div>

            <!-- Footer -->
            <div style="margin-top: 20px; background: #1f2533; border: 2px solid #3b465e; border-radius: 22px; padding: 20px 32px; display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 38px;">🛡️</span>
                <span style="font-size: 25px; font-weight: 700; color: #f8fafc; line-height: 1.3;">
                    Итог: Твой глаз видит предсказание, но последнее слово всегда за сервером!
                </span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)


if __name__ == "__main__":
    gen = Episode13VisualsGenerator()
    out1 = Path(r"e:\social\output\13\visuals\card1_client_prediction.png")
    out2 = Path(r"e:\social\output\13\visuals\card2_server_rollback.png")
    print("Generating Card 1 (Client Prediction)...")
    gen.render_card1_client_prediction(out1)
    print("Generating Card 2 (Server Rollback)...")
    gen.render_card2_server_rollback(out2)
    print("Done Episode 13 Visuals!")
