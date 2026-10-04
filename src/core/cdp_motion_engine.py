"""
CDP Motion Engine for Onter's inn Shorts Generator.
Renders interactive HTML5/CSS3 motion design cards via Chromium/Edge Chrome DevTools Protocol (CDP)
with hardware-accelerated NVIDIA NVENC assembly.
"""

import asyncio
import json
import base64
import os
import subprocess
import time
import wave
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image
import aiohttp
import edge_tts
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_EXE):
    EDGE_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


class CDPMotionEngine:
    """Universal CDP Motion Cards Engine for 1080x1920 Vertical Shorts."""

    def __init__(self, workdir: Path, port: int = 9229):
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.port = port
        self.user_data_dir = self.workdir / "cdp_browser_profile"
        self.frames_dir = self.workdir / "cdp_frames"

    @staticmethod
    def format_ass_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds - int(seconds)) * 100))
        if centis >= 100: centis = 99
        return f"{hrs:01d}:{mins:02d}:{secs:02d}.{centis:02d}"

    async def synthesize_voice_blocks(
        self,
        blocks: List[Dict[str, Any]],
        default_voice: str = "ru-RU-SvetlanaNeural"
    ) -> Tuple[List[Dict[str, Any]], Path, float]:
        """
        Synthesize speech blocks at 100% natural rate (no speedup/pitch distortions)
        and export standardized PCM 44.1kHz stereo WAVs.
        """
        v_dir = self.workdir / "voice_blocks"
        v_dir.mkdir(exist_ok=True)
        
        timings = []
        current_time = 0.0
        concat_lines = []
        
        for b in blocks:
            raw_mp3 = v_dir / f"{b['id']}_raw.mp3"
            final_wav = v_dir / f"{b['id']}.wav"
            voice = b.get("voice", default_voice)
            
            comm = edge_tts.Communicate(text=b["text"], voice=voice)
            await comm.save(str(raw_mp3))
            
            cmd = [
                FFMPEG_EXE, "-y", "-i", str(raw_mp3),
                "-ar", "44100", "-ac", "2",
                str(final_wav)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            with wave.open(str(final_wav), 'rb') as wf:
                dur = wf.getnframes() / float(wf.getframerate())
                
            b_info = dict(b)
            b_info["start"] = current_time
            b_info["duration"] = dur
            b_info["end"] = current_time + dur
            b_info["wav_path"] = final_wav
            timings.append(b_info)
            
            concat_lines.append(f"file '{final_wav.name}'")
            current_time += dur
            
        concat_file = v_dir / "voice_concat.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            f.write("\n".join(concat_lines))
            
        full_voice_wav = v_dir / "full_voice.wav"
        subprocess.run([
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:a", "pcm_s16le",
            str(full_voice_wav)
        ], check=True, capture_output=True)
        
        return timings, full_voice_wav, current_time

    def generate_subtitles(self, timings: List[Dict[str, Any]], output_ass: Path) -> Path:
        """Generate high-contrast ASS subtitles positioned in safe lower zone (MarginV=260)."""
        header = """[Script Info]
Title: Motion Engine Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,46,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,60,60,260,1
Style: Highlight,Montserrat,48,&H0000F0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4.0,2,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for b in timings:
            st = self.format_ass_time(b["start"])
            et = self.format_ass_time(b["end"])
            text = b["text"]
            hl = b.get("highlight", "")
            if hl and hl in text:
                styled_text = text.replace(hl, r"{\c&H00F0FF&}" + hl + r"{\c&HFFFFFF&}")
            else:
                styled_text = text
            events.append(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{styled_text}")
            
        with open(output_ass, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))
        return output_ass

    async def record_motion_deck_cdp(
        self,
        html_player_path: Path,
        slide_durations: List[float],
        output_mp4: Path
    ) -> Path:
        """Capture live HTML motion design from browser via Chrome DevTools Protocol."""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        
        for f in self.frames_dir.glob("*.jpg"):
            try: os.remove(f)
            except: pass
            
        cmd = [
            EDGE_EXE,
            "--headless=new",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={str(self.user_data_dir.resolve())}",
            "--hide-scrollbars",
            "--window-size=1080,1920",
            "--force-device-scale-factor=1",
            "--autoplay-policy=no-user-gesture-required",
            f"file:///{html_player_path.resolve().as_posix()}"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        total_slides_duration = sum(slide_durations)
        frame_count = 0
        
        try:
            await asyncio.sleep(2)
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{self.port}/json") as resp:
                    tabs = await resp.json()
                    page_tab = next(t for t in tabs if t.get("type") == "page")
                    ws_url = page_tab["webSocketDebuggerUrl"]
                    
                async with session.ws_connect(ws_url) as ws:
                    await ws.send_json({"id": 1, "method": "Page.enable"})
                    await ws.send_json({"id": 2, "method": "Runtime.enable"})
                    await ws.send_json({
                        "id": 3,
                        "method": "Emulation.setDeviceMetricsOverride",
                        "params": {
                            "width": 1080,
                            "height": 1920,
                            "deviceScaleFactor": 1,
                            "mobile": False
                        }
                    })
                    
                    eval_setup = """
                    document.body.style.margin = '0';
                    document.body.style.padding = '0';
                    document.body.style.overflow = 'hidden';
                    document.body.style.background = '#04060a';
                    
                    const tb = document.getElementById('toolbar');
                    if (tb) tb.style.display = 'none';
                    
                    const frame = document.getElementById('phone-frame');
                    if (frame) {
                        frame.style.width = '1080px';
                        frame.style.height = '1920px';
                        frame.style.border = 'none';
                        frame.style.borderRadius = '0';
                        frame.style.boxShadow = 'none';
                        frame.style.background = 'radial-gradient(120% 80% at 50% 20%, #0d1726 0%, #060a11 50%, #030508 100%)';
                    }
                    const inner = document.getElementById('phone-inner');
                    if (inner) {
                        inner.style.transform = 'scale(1)';
                        inner.style.left = '0';
                        inner.style.top = '0';
                    }
                    const sub = document.getElementById('subtitles-box');
                    if (sub) sub.style.display = 'none';
                    """
                    await ws.send_json({
                        "id": 4,
                        "method": "Runtime.evaluate",
                        "params": {"expression": eval_setup}
                    })
                    
                    await asyncio.sleep(1.0)
                    
                    await ws.send_json({
                        "id": 5,
                        "method": "Page.startScreencast",
                        "params": {
                            "format": "jpeg",
                            "quality": 95,
                            "maxWidth": 1080,
                            "maxHeight": 1920,
                            "everyNthFrame": 1
                        }
                    })
                    
                    async def switch_slides():
                        for idx, dur in enumerate(slide_durations):
                            await ws.send_json({
                                "id": 100 + idx,
                                "method": "Runtime.evaluate",
                                "params": {"expression": f"showSlide({idx});"}
                            })
                            await asyncio.sleep(dur)
                            
                    slide_task = asyncio.create_task(switch_slides())
                    start_rec_t = time.time()
                    
                    while not slide_task.done() or (time.time() - start_rec_t < (total_slides_duration + 0.3)):
                        try:
                            msg = await asyncio.wait_for(ws.receive(), timeout=1.0)
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if data.get("method") == "Page.screencastFrame":
                                    frame_count += 1
                                    frame_b64 = data["params"]["data"]
                                    session_id = data["params"]["sessionId"]
                                    
                                    await ws.send_json({
                                        "id": 1000 + frame_count,
                                        "method": "Page.screencastFrameAck",
                                        "params": {"sessionId": session_id}
                                    })
                                    
                                    f_path = self.frames_dir / f"frame_{frame_count:05d}.jpg"
                                    with open(f_path, "wb") as f_out:
                                        f_out.write(base64.b64decode(frame_b64))
                        except asyncio.TimeoutError:
                            if slide_task.done():
                                break
                                
                    await ws.send_json({"id": 6, "method": "Page.stopScreencast"})
        finally:
            proc.terminate()
            try: proc.wait(timeout=3)
            except: proc.kill()
            
        # Ensure 1080x1920 dimensions
        for fp in sorted(list(self.frames_dir.glob("frame_*.jpg"))):
            with Image.open(fp) as im:
                if im.size != (1080, 1920):
                    im_res = im.resize((1080, 1920), Image.Resampling.LANCZOS)
                    im_res.save(fp, quality=95)
                    
        fps = frame_count / total_slides_duration
        if fps < 15: fps = 30.0
        
        cmd = [
            FFMPEG_EXE, "-y",
            "-framerate", f"{fps:.2f}",
            "-i", str(self.frames_dir / "frame_%05d.jpg"),
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "19",
            "-pix_fmt", "yuv420p",
            str(output_mp4)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_mp4

    def assemble_final_video(
        self,
        gameplay_path: Path,
        memes: List[Path],
        motion_deck_path: Path,
        outro_path: Path,
        voice_wav_path: Path,
        ambient_music_path: Path,
        subtitles_ass_path: Path,
        timings: List[Dict[str, Any]],
        output_video_path: Path
    ) -> Path:
        """Assemble full vertical Shorts video with FFmpeg NVIDIA NVENC."""
        t_hook_start = timings[0]["start"]
        t_hook_dur = timings[0]["duration"]
        t_inv_start = timings[1]["start"]
        t_inv_dur = timings[1]["duration"]
        
        t_motion_start = timings[2]["start"]
        t_motion_end = timings[6]["end"]
        
        t_outro_start = timings[7]["start"]
        total_dur = timings[7]["end"] + 0.5
        
        ass_escaped = str(subtitles_ass_path.resolve()).replace('\\', '/').replace(':', r'\:')
        
        filter_complex = f"""
        [0:v]loop=loop=-1:size=300:start=0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];
        [0:v]loop=loop=-1:size=300:start=0,scale=1000:574:force_original_aspect_ratio=decrease,pad=1000:574:(ow-iw)/2:(oh-ih)/2:color=black[gp_core];
        [bg][gp_core]overlay=(W-w)/2:200[v_base];
        
        [1:v]scale=720:-1:force_original_aspect_ratio=decrease,fade=t=in:st={t_hook_start + 0.5:.2f}:d=0.3:alpha=1,fade=t=out:st={t_hook_start + t_hook_dur - 0.4:.2f}:d=0.3:alpha=1[m1];
        [2:v]scale=720:-1:force_original_aspect_ratio=decrease,fade=t=in:st={t_inv_start + 0.3:.2f}:d=0.3:alpha=1,fade=t=out:st={t_inv_start + t_inv_dur - 0.4:.2f}:d=0.3:alpha=1[m2];
        
        [v_base][m1]overlay=(W-w)/2:860:enable='between(t,{t_hook_start + 0.5:.2f},{t_hook_start + t_hook_dur - 0.1:.2f})'[v_m1];
        [v_m1][m2]overlay=(W-w)/2:860:enable='between(t,{t_inv_start + 0.3:.2f},{t_inv_start + t_inv_dur - 0.1:.2f})'[v_m2];
        
        [3:v]setpts=PTS-STARTPTS+{t_motion_start:.2f}/TB[motion_deck];
        [v_m2][motion_deck]overlay=0:0:enable='between(t,{t_motion_start:.2f},{t_motion_end:.2f})'[v_motion];
        
        [4:v]chromakey=0x00FF00:0.28:0.15,scale=920:-1,setpts=PTS-STARTPTS+{t_outro_start:.2f}/TB[outro_chroma];
        [v_motion][outro_chroma]overlay=(W-w)/2:860:enable='gte(t,{t_outro_start:.2f})'[v_outro];
        
        [v_outro]ass='{ass_escaped}'[v_final];
        
        [6:a]volume=0.15,afade=t=in:st=0:d=1.5,afade=t=out:st={total_dur - 1.5:.2f}:d=1.5[music];
        [4:a]adelay={int(t_outro_start * 1000)}|{int(t_outro_start * 1000)},volume=0.8[outro_sound];
        [5:a][music][outro_sound]amix=inputs=3:duration=first:dropout_transition=2[a_final]
        """
        
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(gameplay_path.resolve()),
            "-stream_loop", "-1", "-i", str(memes[0].resolve()),
            "-stream_loop", "-1", "-i", str(memes[1].resolve()),
            "-i", str(motion_deck_path.resolve()),
            "-i", str(outro_path.resolve()),
            "-i", str(voice_wav_path.resolve()),
            "-i", str(ambient_music_path.resolve()),
            "-filter_complex", filter_complex,
            "-map", "[v_final]",
            "-map", "[a_final]",
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-cq", "19",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_dur:.2f}",
            str(output_video_path.resolve())
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg NVENC assembly failed: {res.stderr}")
            
        return output_video_path

    @staticmethod
    def smoke_test(video_path: Path) -> bool:
        """Verify video container integrity and decodability of all frames."""
        cmd = [FFMPEG_EXE, "-v", "error", "-i", str(video_path.resolve()), "-f", "null", "-"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
