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


class Episode12ENVisualsGenerator:
    """
    Generates massive high-contrast vertical diagrams (1000x1280) for Episode 12 (English):
    - Zero empty space, huge 30-36px fonts for mobile readability.
    - Card 1: Pipeline Steps 1-3 (Ball Physics & Bone Attachment)
    - Card 2: Pipeline Steps 4-5 + Engine Code Fix (Impulse Catapult & Abort Rule)
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
                f"--window-size={self.width},{self.height}",
                "--hide-scrollbars",
                "--default-background-color=00000000",
                f"--screenshot={str(output_image_path)}",
                temp_html_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"[Warning] Chrome headless returned error: {res.stderr}")
            return output_image_path
        finally:
            if os.path.exists(temp_html_path):
                try:
                    os.remove(temp_html_path)
                except Exception:
                    pass

    def render_card1_pipeline_part1(self, output_path: Path) -> Path:
        """
        Card 1: Pipeline Steps 1-3 (English)
        Huge fonts (30-34px), zero empty space, fills full 1280px height.
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
                    <h2 style="font-size: 44px; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px;">BUG PIPELINE: STAGE 1</h2>
                    <p style="font-size: 26px; color: #94a3b8; font-weight: 600; margin-top: 6px;">How the catch attachment trapped the physics</p>
                </div>
                <div style="background: #38bdf8; color: #0f172a; padding: 12px 24px; border-radius: 16px; font-weight: 900; font-size: 24px;">
                    STEPS 1 — 3
                </div>
            </div>

            <!-- Step 1 -->
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
                    <span style="font-size: 34px; font-weight: 800; color: #38bdf8;">1. BALL FLIES ON RIGIDBODY</span>
                    <span style="background: rgba(56,189,248,0.2); color: #38bdf8; padding: 6px 16px; border-radius: 10px; font-size: 20px; font-weight: 700;">RIGIDBODY</span>
                </div>
                <p style="font-size: 30px; color: #e2e8f0; line-height: 1.4; font-weight: 500;">
                    The ball in the air obeys physics solver: velocity, spin, and gravity are actively calculated each tick.
                </p>
            </div>

            <!-- Step 2 -->
            <div style="
                flex: 1;
                margin-top: 22px;
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
                    <span style="font-size: 34px; font-weight: 800; color: #fbbf24;">2. SAVE ANIMATION TRIGGER</span>
                    <span style="background: rgba(251,191,36,0.2); color: #fbbf24; padding: 6px 16px; border-radius: 10px; font-size: 20px; font-weight: 700;">AI CHECK: OK</span>
                </div>
                <p style="font-size: 30px; color: #e2e8f0; line-height: 1.4; font-weight: 500;">
                    Engine decides the goalkeeper can react in time and triggers the dive-and-catch animation.
                </p>
            </div>

            <!-- Step 3 -->
            <div style="
                flex: 1;
                margin-top: 22px;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #ef4444;
                border-radius: 26px;
                padding: 30px 36px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <span style="font-size: 34px; font-weight: 800; color: #f87171;">3. HARD BONE ATTACHMENT</span>
                    <span style="background: rgba(239,68,68,0.2); color: #f87171; padding: 6px 16px; border-radius: 10px; font-size: 20px; font-weight: 700;">BONE LOCK</span>
                </div>
                <p style="font-size: 30px; color: #e2e8f0; line-height: 1.4; font-weight: 500;">
                    Goalkeeper's hand bones are <b style="color: #fff;">locked to the ball</b>, but ball physics was <b style="color: #f87171;">never disabled!</b>
                </p>
            </div>

            <!-- Footer -->
            <div style="margin-top: 24px; background: #1f2533; border: 2px solid #3b465e; border-radius: 22px; padding: 22px 32px; display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 40px;">⚠️</span>
                <span style="font-size: 26px; font-weight: 700; color: #f8fafc; line-height: 1.3;">
                    The trap is sprung: goalkeeper model is chained to an active physics object!
                </span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_pipeline_part2(self, output_path: Path) -> Path:
        """
        Card 2: Pipeline Steps 4-5 + Code Fix (English)
        Huge fonts (30-34px), zero empty space, fills full 1280px height.
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
                    <h2 style="font-size: 44px; font-weight: 900; color: #f8fafc; letter-spacing: -0.5px;">BUG PIPELINE: STAGE 2</h2>
                    <p style="font-size: 26px; color: #94a3b8; font-weight: 600; margin-top: 6px;">Catapult launch into orbit & engine code fix</p>
                </div>
                <div style="background: #e11d48; color: #ffffff; padding: 12px 24px; border-radius: 16px; font-weight: 900; font-size: 24px;">
                    STEPS 4 — 5
                </div>
            </div>

            <!-- Step 4 -->
            <div style="
                flex: 1;
                margin-top: 22px;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #e11d48;
                border-radius: 26px;
                padding: 26px 34px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 33px; font-weight: 800; color: #f43f5e;">4. STRIKER'S IMPULSE STRIKE</span>
                    <span style="background: rgba(225,29,72,0.2); color: #f43f5e; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">+9999 m/s</span>
                </div>
                <p style="font-size: 29px; color: #e2e8f0; line-height: 1.35; font-weight: 500;">
                    At that exact frame, the striker boots the ball! The ball gains massive upward kinetic impulse.
                </p>
            </div>

            <!-- Step 5 -->
            <div style="
                flex: 1;
                margin-top: 20px;
                background: #1a1e27;
                border: 2px solid #2d3545;
                border-left: 12px solid #a855f7;
                border-radius: 26px;
                padding: 26px 34px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 33px; font-weight: 800; color: #c084fc;">5. GOALKEEPER TOWED TO SPACE</span>
                    <span style="background: rgba(168,85,247,0.2); color: #c084fc; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">🚀 ORBIT</span>
                </div>
                <p style="font-size: 29px; color: #e2e8f0; line-height: 1.35; font-weight: 500;">
                    Because hands are locked to the ball, <b style="color: #fff;">the ball tows the 80-kg keeper</b> straight into the stratosphere!
                </p>
            </div>

            <!-- Code Fix -->
            <div style="
                flex: 1.2;
                margin-top: 20px;
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
                    <span style="font-size: 31px; font-weight: 800; color: #4ade80;">FIX: IF BALL IS TOO FAST — ABORT CATCH!</span>
                    <span style="background: rgba(16,185,129,0.2); color: #4ade80; padding: 5px 14px; border-radius: 10px; font-size: 19px; font-weight: 700;">C++ FIX</span>
                </div>
                <pre style="font-family: monospace; font-size: 27px; color: #86efac; line-height: 1.4; white-space: pre-wrap; font-weight: 700;">
if (ball->velocity > MAX_CATCH_SPEED) {{
    keeper->AbortCatch(); <span style="color: #38bdf8;">// cancel attachment!</span>
}} else {{
    ball->SetKinematic(true); <span style="color: #fbbf24;">// disable physics!</span>
}}</pre>
            </div>

            <!-- Footer -->
            <div style="margin-top: 20px; background: #1f2533; border: 2px solid #3b465e; border-radius: 22px; padding: 20px 32px; display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 38px;">🛡️</span>
                <span style="font-size: 25px; font-weight: 700; color: #f8fafc; line-height: 1.3;">
                    Result: A simple velocity check prevents goalkeepers from being launched like a kite!
                </span>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)


if __name__ == "__main__":
    gen = Episode12ENVisualsGenerator()
    out1 = Path(r"e:\social\output\12_en\visuals\card1_impulse_explosion_en.png")
    out2 = Path(r"e:\social\output\12_en\visuals\card2_fix_en.png")
    print("Generating English Card 1...")
    gen.render_card1_pipeline_part1(out1)
    print("Generating English Card 2...")
    gen.render_card2_pipeline_part2(out2)
    print("Done!")
