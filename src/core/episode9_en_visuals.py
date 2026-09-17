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


class Episode9ENVisualsGenerator:
    """
    Vertical Top-to-Bottom Diagram Generator (English) for Mobile Shorts (1080x1920).
    Occupies top 2/3 of the vertical screen (1000 x 1280 px).
    """
    def __init__(self, width: int = 1000, height: int = 1280, browser_path: str = CHROME_PATH):
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
        Card 1: Camera 3D projection & NaN out-of-bounds error.
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
                    HOW CAMERA PROJECTS 3D TO SCREEN
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #38bdf8; font-family: monospace; background: #0f172a; border: 2px solid #0284c7; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    1. MATH
                </div>
            </div>

            <!-- STEP 1: 3D World (Top Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 34px 34px; border-left: 10px solid #38bdf8; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #38bdf8;">
                        STEP 1: 3D WORLD (GAME ENGINE)
                    </div>
                    <div style="font-size: 22px; font-weight: 800; color: #94a3b8; font-family: monospace;">
                        World Space (X, Y, Z)
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; gap: 32px;">
                    <div style="width: 175px; height: 165px; background: #0f1115; border: 3px dashed #475569; border-radius: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 66px;">🎥</span>
                        <span style="font-size: 22px; font-weight: 900; color: #38bdf8;">3D Camera</span>
                    </div>

                    <div style="flex: 1; display: flex; flex-direction: column; gap: 14px;">
                        <div style="font-size: 28px; font-weight: 700; color: #f1f5f9; line-height: 1.35;">
                            The engine tracks 3D object positions in world coordinates.
                        </div>
                        <div style="background: #450a0a; border: 2px solid #ef4444; border-radius: 12px; padding: 10px 22px; display: inline-flex; align-items: center; gap: 12px; width: fit-content;">
                            <span style="font-size: 26px;">⚠️</span>
                            <span style="font-size: 24px; font-weight: 900; color: #fca5a5;">Shader Error: Division by Zero!</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- CONNECTOR ARROW DOWN -->
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; margin: 2px 0;">
                <div style="background: #0f1115; border: 2.5px solid #334155; padding: 14px 42px; border-radius: 16px; font-family: monospace; font-size: 30px; font-weight: 900; color: #fbbf24; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
                    Screen Pos = 3D Pos × Projection Matrix
                </div>
                
                <div style="display: flex; align-items: center; gap: 24px;">
                    <div style="color: #ef4444; font-size: 44px; font-weight: 900; line-height: 1;">⬇ ⬇ ⬇</div>
                    <div style="background: #7f1d1d66; border: 2px solid #ef4444; color: #fecaca; padding: 10px 26px; border-radius: 14px; font-size: 26px; font-weight: 900; font-family: monospace;">
                        Coordinates = NaN (Infinity)
                    </div>
                    <div style="color: #ef4444; font-size: 44px; font-weight: 900; line-height: 1;">⬇ ⬇ ⬇</div>
                </div>
            </div>

            <!-- STEP 2: Screen Space (Bottom Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 34px 34px; border-left: 10px solid #ef4444; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #f87171;">
                        STEP 2: MONITOR SCREEN SPACE
                    </div>
                    <div style="font-size: 22px; font-weight: 800; color: #94a3b8; font-family: monospace;">
                        Normalized Screen [-1, 1]
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; gap: 32px;">
                    <!-- Screen Box -->
                    <div style="width: 300px; height: 175px; background: #000000; border: 3.5px solid #ef4444; border-radius: 20px; position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0; overflow: visible;">
                        <span style="font-size: 24px; font-weight: 900; color: #94a3b8;">Screen Zone [-1, 1]</span>
                        <span style="font-size: 18px; color: #64748b; font-family: monospace;">(Visible Viewport)</span>
                        <div style="position: absolute; right: -24px; top: -20px; background: #dc2626; color: #ffffff; padding: 8px 18px; border-radius: 10px; font-size: 20px; font-weight: 900; box-shadow: 0 8px 20px rgba(0,0,0,0.7); border: 2px solid #fecaca; white-space: nowrap;">
                            🚀 Out of Bounds!
                        </div>
                    </div>

                    <!-- GPU Reaction -->
                    <div style="flex: 1; display: flex; flex-direction: column; gap: 12px;">
                        <div style="font-size: 28px; font-weight: 900; color: #fca5a5; line-height: 1.35;">
                            GPU: <span style="color: #ffffff;">«Coordinates broken — skip rendering»</span>
                        </div>
                        <div style="font-size: 24px; color: #cbd5e1; line-height: 1.35;">
                            Screen Space Culling discards draw calls, leaving frozen pixels.
                        </div>
                    </div>
                </div>
            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">📌</span>
                    <span style="color: #94a3b8; font-size: 27px;">Result: <b style="color: #ffffff;">Anomaly pixels never refresh</b></span>
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
        Card 2: Buffer Trail & Hall of Mirrors.
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
                    WHY DOES THE HAND LEAVE A TRAIL?
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #38bdf8; font-family: monospace; background: #0f172a; border: 2px solid #0284c7; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    2. FRAME BUFFER
                </div>
            </div>

            <!-- STEP 1: Hand appears (Top Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 36px 34px; border-left: 10px solid #38bdf8; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #38bdf8;">
                        FRAME 1: HAND SWING
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
                        The hand swings across the black void. The GPU successfully writes glove pixels into frame buffer memory.
                    </div>
                </div>
            </div>

            <!-- CONNECTOR ARROW DOWN -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin: 4px 0;">
                <div style="color: #94a3b8; font-size: 42px; font-weight: 900;">⬇</div>
                <div style="background: #0f1115; border: 2px solid #334155; color: #e2e8f0; padding: 10px 32px; border-radius: 14px; font-size: 26px; font-weight: 800;">
                    Next Rendering Frame
                </div>
                <div style="color: #94a3b8; font-size: 42px; font-weight: 900;">⬇</div>
            </div>

            <!-- STEP 2: Hand moved away (Bottom Block) -->
            <div style="background: #1c1f26; border-radius: 24px; padding: 36px 34px; border-left: 10px solid #ef4444; display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 29px; font-weight: 900; color: #f87171;">
                        FRAME 2: HAND MOVED AWAY
                    </div>
                    <div style="background: #450a0a; color: #fca5a5; border: 1.5px solid #ef4444; padding: 6px 16px; border-radius: 10px; font-size: 22px; font-weight: 900; font-family: monospace;">
                        Frame #101 (VOID)
                    </div>
                </div>

                <div style="display: flex; align-items: center; gap: 32px;">
                    <div style="width: 175px; height: 155px; background: #0f1115; border: 2.5px solid #ef4444; border-radius: 22px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 60px;">❌ 🧹</span>
                    </div>
                    <div style="font-size: 28px; color: #f1f5f9; line-height: 1.4; font-weight: 600;">
                        There is only void behind. The engine <b style="color: #f87171;">never overwrites old pixels</b>, freezing them forever like in Windows XP!
                    </div>
                </div>
            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">🪞</span>
                    <span style="color: #94a3b8; font-size: 27px;">Effect: <b style="color: #ffffff;">Old pixels never get cleared</b></span>
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
        Card 3: Developer fix.
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
                    HOW DEVELOPERS FIX THIS
                </div>
                <div style="font-size: 23px; font-weight: 900; color: #22c55e; font-family: monospace; background: #052e16; border: 2px solid #16a34a; padding: 7px 18px; border-radius: 12px; white-space: nowrap;">
                    3. FIX
                </div>
            </div>

            <!-- Terminal Box (Wrong vs Fixed) -->
            <div style="display: flex; flex-direction: column; gap: 32px;">
                
                <!-- WRONG BLOCK -->
                <div style="background: #1c1f26; border-left: 10px solid #ef4444; border-radius: 24px; padding: 34px 36px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div style="font-size: 29px; font-weight: 900; color: #ef4444;">
                            [-] ENGINE BUG (UNHANDLED PASS)
                        </div>
                        <div style="font-family: monospace; color: #fca5a5; font-size: 22px; font-weight: 800;">
                            Shader_Cull_Pass.hlsl
                        </div>
                    </div>
                    <div style="background: #090d16; border: 2px solid #7f1d1d; border-radius: 16px; padding: 22px 26px; font-family: monospace; font-size: 28px; color: #f87171; margin-bottom: 14px;">
                        if (isnan(pixel_pos)) discard; // Pixel skipped!
                    </div>
                    <div style="font-size: 26px; color: #cbd5e1; line-height: 1.35; font-weight: 600;">
                        The engine skips buffer clears whenever NaN coordinates appear.
                    </div>
                </div>

                <!-- FIXED BLOCK -->
                <div style="background: #1c1f26; border-left: 10px solid #22c55e; border-radius: 24px; padding: 34px 36px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <div style="font-size: 29px; font-weight: 900; color: #4ade80;">
                            [+] PROPER FIX (RENDER TARGET CLEAR)
                        </div>
                        <div style="font-family: monospace; color: #86efac; font-size: 22px; font-weight: 800;">
                            PostProcess_Buffer.hlsl
                        </div>
                    </div>
                    <div style="background: #090d16; border: 2px solid #22c55e; border-radius: 16px; padding: 22px 26px; font-family: monospace; font-size: 28px; color: #4ade80; margin-bottom: 14px;">
                        RenderTarget.Clear(Color::SkyVoid); // 100% Cleared
                    </div>
                    <div style="font-size: 26px; color: #cbd5e1; line-height: 1.35; font-weight: 600;">
                        Always force clear the full screen with background sky color before every frame.
                    </div>
                </div>

            </div>

            <!-- FOOTER SUMMARY BADGE -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: #0d0e11; border: 2px solid #232730; padding: 22px 34px; border-radius: 20px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 30px;">🛡️</span>
                    <span style="color: #94a3b8; font-size: 27px;">Solution: <b style="color: #22c55e;">Full Frame Clear Buffer</b></span>
                </div>
                <div style="color: #22c55e; font-size: 25px; font-weight: 900; font-family: monospace; background: #052e1688; border: 2px solid #16a34a; padding: 8px 20px; border-radius: 12px;">
                    Clean Render 100%
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)


if __name__ == "__main__":
    out_dir = Path("e:/social/output/9_en/visuals")
    gen = Episode9ENVisualsGenerator(width=1000, height=1280)
    gen.render_card1_camera(out_dir / "card1_camera_vertical_en.png")
    gen.render_card2_buffer(out_dir / "card2_buffer_vertical_en.png")
    gen.render_card3_fix(out_dir / "card3_fix_vertical_en.png")
    print("English vertical cards rendered successfully!")
