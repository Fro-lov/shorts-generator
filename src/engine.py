import sys
import io
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from config.settings import (
    ASSETS_DIR,
    FFMPEG_PATH,
    DEFAULT_VOICE,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    FPS
)
from src.core.tts import TTSEngine
from src.core.subtitles import SubtitleGenerator
from src.core.episode2_visuals import Episode2VisualsGenerator
from src.core.output_manager import EpisodeOutputManager
from src.core.music_generator import get_random_bgm
from src.core.youtube_downloader import YouTubeDownloader


class FFmpegInputManager:
    """Helper to keep track of exact 0-indexed FFmpeg inputs."""
    def __init__(self):
        self.inputs = []  # list of tuples: (type, path_str)

    def add_file(self, path: Path, is_looped_image: bool = False) -> int:
        idx = len(self.inputs)
        self.inputs.append(("loop_image" if is_looped_image else "standard", str(path)))
        return idx

    def get_cmd_args(self) -> List[str]:
        args = []
        for inp_type, p in self.inputs:
            if inp_type == "loop_image":
                args.extend(["-loop", "1", "-i", p])
            else:
                args.extend(["-i", p])
        return args


class ShortsEngine:
    """
    Unified GameBug Shorts Production Engine.
    Executes the entire end-to-end shorts creation pipeline in a single command.
    """

    def __init__(self, scenario_path: Path):
        self.scenario_path = Path(scenario_path)
        with open(self.scenario_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.episode_id = str(self.data.get("episode_id", "1"))
        self.mgr = EpisodeOutputManager(self.episode_id)
        self.paths = self.mgr.get_paths("video.mp4")

    def prepare_background(self, gameplay_src: Path, cut_time: float, total_duration: float, output_bg: Path) -> Path:
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", "00:00:00",
            "-to", f"00:00:{cut_time:04.1f}",
            "-i", str(gameplay_src),
            "-filter_complex",
            f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},boxblur=22:6[bg];"
            f"[0:v]scale=1020:-1[fg];"
            f"[bg][fg]overlay=(W-w)/2:220[v_comp];"
            f"[v_comp]tpad=stop_mode=clone:stop_duration={max(0, total_duration - cut_time)}[v_out]",
            "-map", "[v_out]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-t", str(total_duration),
            "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            str(output_bg)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed creating background: {res.stderr}")
        return output_bg

    def run(self) -> Dict[str, Any]:
        game_title = self.data.get("game", "Game")
        bug_title = self.data.get("bug_title", "Glitch")
        print("=" * 65)
        print(f"🚀 ЗАПУСК GAMEBUG SHORTS ENGINE: Выпуск #{self.episode_id} ({game_title} - {bug_title})")
        print("=" * 65)

        # 1. Gameplay Resolution
        gp_info = self.data.get("gameplay", {})
        gp_src = Path(gp_info.get("source", ""))
        if not gp_src.exists() and "youtube_url" in gp_info:
            print(f"\n[1/6] Скачивание фрагмента с YouTube: {gp_info['youtube_url']}...")
            dl = YouTubeDownloader()
            gp_src = dl.download_clip(
                url=gp_info["youtube_url"],
                output_name=f"gameplay_{self.episode_id}.mp4",
                start_time=gp_info.get("start_time"),
                end_time=gp_info.get("end_time")
            )
        cut_time = float(gp_info.get("cut_time", 5.0))

        # 2. Ambient Music Selection
        ambient_dir = ASSETS_DIR / "music" / "ambient"
        bgm_path = get_random_bgm(ambient_dir)

        # 3. Scene-based Block TTS
        print("\n[2/6] Синтез речи по смысловым блокам (Edge-TTS)...")
        tts = TTSEngine(voice=DEFAULT_VOICE, rate="+8%")
        blocks_def = self.data.get("blocks", [])

        block_timings = {}
        current_time = 0.0
        all_subtitles = []
        block_audio_paths = []
        bgm_start_time = None

        for idx, b in enumerate(blocks_def):
            b_id = b["id"]
            b_audio = self.mgr.voice_dir / f"block_{idx+1}_{b_id}.mp3"
            res = tts.generate_speech(b["text"], b_audio)
            events = res["events"]
            b_dur = events[-1]["end"] + 0.35 if events else 3.0

            b_start = current_time
            b_end = current_time + b_dur

            if b.get("trigger_bgm") and bgm_start_time is None:
                bgm_start_time = b_start

            block_timings[b_id] = {
                "start": b_start,
                "end": b_end,
                "duration": b_dur,
                "def": b
            }

            for ev in events:
                all_subtitles.append({
                    "text": ev["text"],
                    "start": b_start + ev["start"],
                    "end": b_start + ev["end"]
                })

            block_audio_paths.append(b_audio)
            current_time = b_end + 0.15

        total_duration = current_time + 0.5
        if bgm_start_time is None:
            bgm_start_time = 0.0

        print(f"   ✓ Блоков речи: {len(blocks_def)}")
        print(f"   ✓ Общая длительность: {total_duration:.2f} сек.")
        print(f"   ✓ Старт эмбиента ({bgm_path.name}): {bgm_start_time:.2f} сек.")

        # Concatenate block audio
        concat_txt = self.mgr.temp_dir / "voice_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for ap in block_audio_paths:
                f.write(f"file '{ap.resolve().as_posix()}'\n")

        cmd_concat = [FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(self.paths["voice"])]
        subprocess.run(cmd_concat, capture_output=True, check=True)

        # 4. Generate Subtitles
        print("\n[3/6] Генерация желтых караоке-субтитров (.ass)...")
        sub_gen = SubtitleGenerator(
            font_name="Arial",
            font_size=46,
            primary_color="&H0000FFFF",
            outline_width=5,
            margin_v=160
        )
        sub_gen.generate_ass_file(all_subtitles, self.paths["subtitles"], max_words_per_line=3)

        # 5. Generate Visual Cards (Diagrams & Code)
        print("\n[4/6] Отрисовка схем и карточки кода...")
        vis_gen = Episode2VisualsGenerator(width=1000, height=560)
        diag1_path = self.mgr.visuals_dir / "step1_door.png"
        diag2_path = self.mgr.visuals_dir / "step2_impact.png"
        code_path = self.mgr.visuals_dir / "door_fix_card.png"
        vis_gen.generate_step1_door(diag1_path)
        vis_gen.generate_step2_impact(diag2_path)
        vis_gen.generate_door_fix_card(code_path)

        # 6. Prepare Background Video
        print("\n[5/6] Создание видеоряда с геймплеем (9:16)...")
        self.prepare_background(gp_src, cut_time=cut_time, total_duration=total_duration, output_bg=self.paths["temp_bg"])

        # 7. Dynamic FFmpeg Filter Graph Assembly
        print("\n[6/6] Финальный монтаж видеоряда и аудиомикшера...")

        inp_mgr = FFmpegInputManager()
        bg_idx = inp_mgr.add_file(self.paths["temp_bg"])       # 0: video
        voice_idx = inp_mgr.add_file(self.paths["voice"])      # 1: audio
        bgm_idx = inp_mgr.add_file(bgm_path)                  # 2: audio

        audio_sources = [
            f"[{voice_idx}:a]volume=1.0[a_voice]",
            f"[{bgm_idx}:a]adelay={int(bgm_start_time*1000)}|{int(bgm_start_time*1000)},volume=0.14[a_bgm]"
        ]
        mix_inputs = ["[a_voice]", "[a_bgm]"]
        video_filters = []
        last_v = f"[{bg_idx}:v]"

        # Process overlays and SFX per block
        for b in blocks_def:
            b_info = block_timings[b["id"]]
            b_start = b_info["start"]
            b_end = b_info["end"]
            b_dur = b_info["duration"]

            # Direct block SFX
            if "sfx" in b and b["sfx"]:
                s_path = Path(b["sfx"])
                if s_path.exists():
                    s_idx = inp_mgr.add_file(s_path)
                    s_delay = int(b_start * 1000)
                    s_lbl = f"[sfx_{s_idx}]"
                    audio_sources.append(f"[{s_idx}:a]adelay={s_delay}|{s_delay},volume=0.35{s_lbl}")
                    mix_inputs.append(s_lbl)

            # Multiple memes inside block
            if "memes" in b:
                cur_m_start = b_start
                for m in b["memes"]:
                    m_ratio = m.get("ratio", 1.0 / len(b["memes"]))
                    m_dur = b_dur * m_ratio
                    m_end = cur_m_start + m_dur

                    m_file = Path(m["file"])
                    if m_file.exists():
                        m_idx = inp_mgr.add_file(m_file, is_looped_image=True)
                        v_lbl = f"[v_ov_{m_idx}]"
                        out_v = f"[v_mix_{m_idx}]"
                        video_filters.append(
                            f"[{m_idx}:v]scale=960:-1,format=rgba,fade=t=in:st={cur_m_start:.2f}:d=0.2:alpha=1,fade=t=out:st={m_end-0.2:.2f}:d=0.2:alpha=1{v_lbl};"
                            f"{last_v}{v_lbl}overlay=(W-w)/2:840:enable='between(t,{cur_m_start:.2f},{m_end:.2f})'{out_v}"
                        )
                        last_v = out_v

                    if "sfx" in m and m["sfx"]:
                        ms_path = Path(m["sfx"])
                        if ms_path.exists():
                            ms_idx = inp_mgr.add_file(ms_path)
                            ms_delay = int(cur_m_start * 1000)
                            ms_lbl = f"[sfx_m_{ms_idx}]"
                            audio_sources.append(f"[{ms_idx}:a]adelay={ms_delay}|{ms_delay},volume=0.35{ms_lbl}")
                            mix_inputs.append(ms_lbl)

                    cur_m_start = m_end

            # Diagram Step 1
            elif b.get("visual_type") == "diagram_door_step1":
                d1_idx = inp_mgr.add_file(diag1_path, is_looped_image=True)
                v_lbl = f"[v_ov_{d1_idx}]"
                out_v = f"[v_mix_{d1_idx}]"
                video_filters.append(
                    f"[{d1_idx}:v]scale=980:-1,format=rgba,fade=t=in:st={b_start:.2f}:d=0.25:alpha=1,fade=t=out:st={b_end-0.25:.2f}:d=0.25:alpha=1{v_lbl};"
                    f"{last_v}{v_lbl}overlay=(W-w)/2:840:enable='between(t,{b_start:.2f},{b_end:.2f})'{out_v}"
                )
                last_v = out_v

            # Split Diagram + Meme
            elif b.get("visual_type") == "split_diagram_and_meme":
                mid = b_start + (b_dur * 0.5)

                # Part 1: Diagram 2
                d2_idx = inp_mgr.add_file(diag2_path, is_looped_image=True)
                v_lbl1 = f"[v_ov_{d2_idx}]"
                out_v1 = f"[v_mix_{d2_idx}]"
                video_filters.append(
                    f"[{d2_idx}:v]scale=980:-1,format=rgba,fade=t=in:st={b_start:.2f}:d=0.25:alpha=1,fade=t=out:st={mid-0.25:.2f}:d=0.25:alpha=1{v_lbl1};"
                    f"{last_v}{v_lbl1}overlay=(W-w)/2:840:enable='between(t,{b_start:.2f},{mid:.2f})'{out_v1}"
                )
                last_v = out_v1

                # Part 2: Meme
                m_file = Path(b.get("meme", ""))
                if m_file.exists():
                    bm_idx = inp_mgr.add_file(m_file, is_looped_image=True)
                    v_lbl2 = f"[v_ov_{bm_idx}]"
                    out_v2 = f"[v_mix_{bm_idx}]"
                    video_filters.append(
                        f"[{bm_idx}:v]scale=960:-1,format=rgba,fade=t=in:st={mid:.2f}:d=0.25:alpha=1,fade=t=out:st={b_end-0.25:.2f}:d=0.25:alpha=1{v_lbl2};"
                        f"{last_v}{v_lbl2}overlay=(W-w)/2:840:enable='between(t,{mid:.2f},{b_end:.2f})'{out_v2}"
                    )
                    last_v = out_v2

            # Code Card
            elif b.get("visual_type") == "code_card_door":
                c_idx = inp_mgr.add_file(code_path, is_looped_image=True)
                v_lbl = f"[v_ov_{c_idx}]"
                out_v = f"[v_mix_{c_idx}]"
                video_filters.append(
                    f"[{c_idx}:v]scale=980:-1,format=rgba,fade=t=in:st={b_start:.2f}:d=0.25:alpha=1,fade=t=out:st={b_end-0.25:.2f}:d=0.25:alpha=1{v_lbl};"
                    f"{last_v}{v_lbl}overlay=(W-w)/2:840:enable='between(t,{b_start:.2f},{b_end:.2f})'{out_v}"
                )
                last_v = out_v

        # Subtitles Layer
        rel_sub = Path(self.paths["subtitles"]).resolve().as_posix().replace(":", "\\:")
        video_filters.append(f"{last_v}subtitles=filename='{rel_sub}'[v_final]")

        # Audio Mix Layer
        audio_mix_str = f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[a_final]"
        audio_sources.append(audio_mix_str)

        full_filter = ";".join(video_filters + audio_sources)

        final_mp4 = self.paths["final_video"]
        cmd_render = [
            FFMPEG_PATH, "-y",
            *inp_mgr.get_cmd_args(),
            "-filter_complex", full_filter,
            "-map", "[v_final]",
            "-map", "[a_final]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_duration),
            "-pix_fmt", "yuv420p",
            str(final_mp4)
        ]

        res = subprocess.run(cmd_render, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg execution failed:\n{res.stderr}")

        # Generate Preview Frames
        frame_samples = [1.0, 6.0, 9.0, 13.0, 20.0, 26.0, 31.0, 35.0]
        for idx, t in enumerate(frame_samples):
            if t < total_duration:
                f_path = self.mgr.frames_dir / f"frame_{idx+1}_{t:.1f}s.jpg"
                f_cmd = [FFMPEG_PATH, "-y", "-ss", str(t), "-i", str(final_mp4), "-vframes", "1", "-q:v", "2", str(f_path)]
                subprocess.run(f_cmd, capture_output=True)

        print(f"\n✨ [УСПЕХ] ВЫПУСК #{self.episode_id} УСПЕШНО СОБРАН: {final_mp4}")
        return {
            "final_video": final_mp4,
            "duration": total_duration,
            "bgm": bgm_path.name,
            "blocks": block_timings
        }


def main():
    parser = argparse.ArgumentParser(description="GameBug Shorts Unified Engine")
    parser.add_argument("scenario", type=str, help="Path to scenario JSON file")
    args = parser.parse_args()

    engine = ShortsEngine(Path(args.scenario))
    engine.run()


if __name__ == "__main__":
    main()
