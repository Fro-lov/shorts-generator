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


class Episode11ENVisualsGenerator:
    """
    Generates high-contrast vertical diagrams (1000x1280) for Episode 11 (English):
    - Card 1: 4-Step Out-of-Bounds & Death Animation Conflict
    - Card 2: Engine Code Fix (Preventing Unstuck on dead/falling actors)
    """

    def __init__(self, width: int = 1000, height: int = 1280):
        self.width = width
        self.height = height

    def render_html_to_image(self, html_content: str, output_image_path: Path) -> Path:
        output_image_path = output_image_path.resolve()
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

    def render_card1_navmesh_state(self, output_path: Path) -> Path:
        """
        Card 1: Simple 4-Step Chain (English)
        """
        html = f"""
        <div style="
            width: {self.width}px;
            height: {self.height}px;
            background: #14161a;
            border: 2.5px solid #2a2e37;
            border-radius: 36px;
            padding: 38px 44px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #ffffff;
            box-shadow: 0 30px 70px rgba(0, 0, 0, 0.9);
        ">
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #232730; padding-bottom: 20px;">
                <div>
                    <h2 style="font-size: 34px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">HOW DID THE BUG HAPPEN? (4 STEPS)</h2>
                    <p style="font-size: 21px; color: #94a3b8; margin-top: 4px;">A double coincidence of game engine rules</p>
                </div>
                <div style="background: #0f172a; border: 2px solid #0284c7; padding: 8px 18px; border-radius: 12px; font-size: 20px; font-weight: 700; color: #38bdf8; font-family: monospace;">
                    ENGINE LOGIC
                </div>
            </div>

            <!-- Step 1: Kicked Out of Bounds -->
            <div style="background: #1c1f26; border-left: 8px solid #38bdf8; border-radius: 18px; padding: 18px 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 25px; font-weight: 800; color: #38bdf8;">1. Kicked Out of Bounds</span>
                    <span style="font-size: 18px; background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 3px 12px; border-radius: 8px; font-family: monospace;">OUT OF BOUNDS</span>
                </div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.3;">
                    The Mongol is kicked off a 200-foot coastal cliff straight into the open ocean.
                </div>
            </div>

            <!-- Arrow 1 -->
            <div style="text-align: center; font-size: 24px; color: #64748b; margin: -2px 0;">⇓</div>

            <!-- Step 2: Unfinished Business -->
            <div style="background: #1c1f26; border-left: 8px solid #f59e0b; border-radius: 18px; padding: 18px 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 25px; font-weight: 800; color: #fbbf24;">2. Unfinished Business on Land</span>
                    <span style="font-size: 18px; background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 3px 12px; border-radius: 8px; font-family: monospace;">STATE PENDING</span>
                </div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.3;">
                    The engine strictly requires flat, solid terrain to play out the grounded dying animation.
                </div>
            </div>

            <!-- Arrow 2 -->
            <div style="text-align: center; font-size: 24px; color: #64748b; margin: -2px 0;">⇓</div>

            <!-- Step 3: Snapped Back to Cliff -->
            <div style="background: #1c1f26; border-left: 8px solid #ef4444; border-radius: 18px; padding: 18px 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 25px; font-weight: 800; color: #f87171;">3. Snapped Back to Cliff</span>
                    <span style="font-size: 18px; background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 3px 12px; border-radius: 8px; font-family: monospace;">UNSTUCK SAFETY</span>
                </div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.3;">
                    The boundary safety system catapults the NPC back to the last valid walkable ledge.
                </div>
            </div>

            <!-- Arrow 3 -->
            <div style="text-align: center; font-size: 24px; color: #64748b; margin: -2px 0;">⇓</div>

            <!-- Step 4: Died on Arrival -->
            <div style="background: #1c1f26; border-left: 8px solid #22c55e; border-radius: 18px; padding: 18px 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 25px; font-weight: 800; color: #4ade80;">4. Died on Arrival</span>
                    <span style="font-size: 18px; background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 3px 12px; border-radius: 8px; font-family: monospace;">HP = 0</span>
                </div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.3;">
                    HP is already zero: the moment he hits the ground, he finally completes his death state!
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #0d0e11; border: 2px solid #232730; border-radius: 18px; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 22px; color: #94a3b8;">
                    Result: <b style="color: #ffffff;">Boundary safety rescued a corpse just to let it die</b>
                </div>
                <div style="background: rgba(56, 189, 248, 0.2); border: 1.5px solid #38bdf8; color: #38bdf8; padding: 6px 16px; border-radius: 10px; font-size: 19px; font-family: monospace; font-weight: 700;">
                    4 Bug Steps
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)

    def render_card2_fix(self, output_path: Path) -> Path:
        """
        Card 2: Simplified Engine Code Fix Diff Card (English)
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
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #232730; padding-bottom: 24px;">
                <div>
                    <h2 style="font-size: 34px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">ENGINE CODE FIX (PATCH)</h2>
                    <p style="font-size: 22px; color: #94a3b8; margin-top: 6px;">If HP is zero — never return the actor to the surface</p>
                </div>
                <div style="background: #0f172a; border: 2px solid #22c55e; padding: 10px 20px; border-radius: 12px; font-size: 20px; font-weight: 700; color: #4ade80; font-family: monospace;">
                    PATCH APPLIED
                </div>
            </div>

            <!-- Code Diff Box -->
            <div style="background: #0a0c10; border: 2.5px solid #1e293b; border-radius: 20px; padding: 28px 32px; font-family: Consolas, Monaco, monospace; font-size: 23px; line-height: 1.7;">
                <div style="color: #64748b; margin-bottom: 16px; font-size: 20px;">// WorldBoundsManager.cpp</div>

                <!-- Wrong Line -->
                <div style="background: rgba(239, 68, 68, 0.15); border-left: 6px solid #ef4444; padding: 12px 16px; margin-bottom: 16px; border-radius: 0 10px 10px 0; color: #fca5a5;">
                    <span style="color: #ef4444; font-weight: 900; margin-right: 12px;">[-]</span>if (npc-&gt;IsOutOfBounds()) {{<br>
                    <span style="color: #ef4444; font-weight: 900; margin-right: 12px;">[-]</span>&nbsp;&nbsp;&nbsp;&nbsp;npc-&gt;TeleportToSurface();<br>
                    <span style="color: #94a3b8; font-size: 20px; margin-left: 32px;">// ➔ Catapults corpses right back to the cliff!</span><br>
                    <span style="color: #ef4444; font-weight: 900; margin-right: 12px;">[-]</span>}}
                </div>

                <!-- Fixed Lines -->
                <div style="background: rgba(34, 197, 94, 0.15); border-left: 6px solid #22c55e; padding: 12px 16px; border-radius: 0 10px 10px 0; color: #86efac;">
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>if (npc-&gt;IsOutOfBounds()) {{<br>
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>&nbsp;&nbsp;&nbsp;&nbsp;if (npc-&gt;hp &lt;= 0) return npc-&gt;Destroy();<br>
                    <span style="color: #22c55e; font-weight: 900; margin-right: 12px;">[+]</span>}} // 🌊 Corpses sink peacefully and get cleaned up!
                </div>
            </div>

            <!-- Explanation Callout -->
            <div style="background: #1c1f26; border-left: 8px solid #38bdf8; border-radius: 18px; padding: 22px 28px;">
                <div style="font-size: 24px; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">💡 Simple Rule</div>
                <div style="font-size: 22px; color: #cbd5e1; line-height: 1.4;">
                    If an actor has zero health points remaining, the boundary protection system should never save them. Bodies should stay at the bottom without a boomerang effect.
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #0d0e11; border: 2px solid #232730; border-radius: 20px; padding: 20px 28px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 23px; color: #94a3b8;">
                    Result: <b style="color: #ffffff;">No more flying boomerang corpses</b>
                </div>
                <div style="background: rgba(34, 197, 94, 0.2); border: 1.5px solid #22c55e; color: #4ade80; padding: 8px 18px; border-radius: 10px; font-size: 20px; font-family: monospace; font-weight: 700;">
                    100% Fixed
                </div>
            </div>
        </div>
        """
        return self.render_html_to_image(html, output_path)
