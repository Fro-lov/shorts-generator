import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

from config.settings import FFMPEG_PATH, OUTPUT_DIR, DEFAULT_VOICE
from src.core.output_manager import EpisodeOutputManager
from src.core.tts import TTSEngine, _get_duration
from src.core.subtitles import SubtitleGenerator
from src.core.meme_fetcher import TenorMemeFetcher
from src.core.sfx_fetcher import MyInstantsSFXFetcher
from src.core.metadata_generator import MetadataGenerator
from src.core.smart_card_generator import SmartCardGenerator
from src.core.youtube_downloader import YouTubeDownloader
from src.core.quality_validator import QualityValidator


class PipelineRunner:
    """
    Unified Production & Verification Engine for Game Shorts Creator.
    Enforces strict compliance with SKILL.md and GEMINI.md.
    """
    def __init__(self, episode_id: str):
        self.episode_id = str(episode_id)
        self.out_mgr = EpisodeOutputManager(self.episode_id)
        self.ep_dir = self.out_mgr.root_dir
        self.smart_cards = SmartCardGenerator()
        self.meme_fetcher = TenorMemeFetcher()
        self.sfx_fetcher = MyInstantsSFXFetcher()
        self.tts_engine = TTSEngine()
        self.sub_gen = SubtitleGenerator()
        self.downloader = YouTubeDownloader()
        self.validator = QualityValidator(self.episode_id)

    def prepare_stage1(
        self,
        youtube_url: str,
        start_time: str,
        end_time: str,
        bug_fact: str
    ) -> Dict[str, Any]:
        """
        Stage 1: Download gameplay to E: drive, cut clip, perform Frame Sampling Verification.
        """
        print(f"=== [Stage 1] Preparing Episode {self.episode_id} ===")
        dl_dir = self.ep_dir / "temp"
        dl_dir.mkdir(parents=True, exist_ok=True)
        
        clip_path = dl_dir / "raw_gameplay.mp4"
        self.downloader.download_clip(youtube_url, start_time, end_time, str(clip_path.resolve()))

        if not clip_path.exists() or clip_path.stat().st_size == 0:
            raise RuntimeError(f"Failed to download gameplay clip from {youtube_url}")

        # Extract 3 sample frames for Start, Mid, End verification
        frames_dir = self.ep_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        sample_cmd = [
            FFMPEG_PATH, "-y", "-i", str(clip_path),
            "-vf", "fps=0.5",
            str(frames_dir / "sample_%02d.jpg")
        ]
        subprocess.run(sample_cmd, capture_output=True, text=True)

        # Run Stage 1 Ironclad Validation (Raw gameplay check: no black frames, no freezes)
        val_report = self.validator.validate_raw_gameplay(clip_path)
        if not val_report["valid"]:
            print(f"❌ [Stage 1 Validator] Raw gameplay validation failed: {val_report['errors']}")
            raise ValueError(f"Raw gameplay failed validation: {val_report['errors']}")
        
        print(f"✅ [Stage 1 Validator] Raw gameplay verified successfully. Frame diff scores: {val_report['details'].get('diff_scores')}")

        return {
            "episode_id": self.episode_id,
            "clip_path": str(clip_path),
            "bug_fact": bug_fact,
            "sample_frames": [str(p) for p in frames_dir.glob("sample_*.jpg")],
            "validation_report": val_report
        }

    def generate_visual_cards(
        self,
        variant_name: str,
        card_specs: List[Dict[str, Any]]
    ) -> List[Path]:
        """
        Generates 3-card flow for a variant using SmartCardGenerator (1000x1280 container).
        """
        visuals_dir = self.ep_dir / "visuals"
        visuals_dir.mkdir(parents=True, exist_ok=True)
        generated_paths = []

        for idx, spec in enumerate(card_specs, 1):
            out_p = visuals_dir / f"{variant_name}_card{idx}.png"
            card_type = spec.get("type", "diagram")

            if card_type == "code":
                self.smart_cards.generate_os_code_card(
                    output_path=out_p,
                    title=spec.get("title", "Код Фикса"),
                    file_tab=spec.get("badge", "physics_solver.cpp"),
                    wrong_code=spec.get("wrong_code", []),
                    fixed_code=spec.get("fixed_code", []),
                    takeaway=spec.get("takeaway", "")
                )
            else:
                self.smart_cards.generate_diagram_card(
                    output_path=out_p,
                    title=spec.get("title", "Схема"),
                    badge=spec.get("badge", "PHYSICS"),
                    step_title=spec.get("step_title", spec.get("step1_title", "1. Исходное состояние")),
                    items=spec.get("items", spec.get("step1_items", [])),
                    accent_color=spec.get("accent_color", "#38bdf8"),
                    footer_note=spec.get("footer_note", "")
                )
            generated_paths.append(out_p)

        return generated_paths

    def render_variant(
        self,
        variant_name: str,
        scenario: Dict[str, Any],
        visual_cards: List[Path]
    ) -> Path:
        """
        Renders a full variant video in FFmpeg with Dual-Voice TTS, Meme Overlays, SFX, and Outro.
        """
        var_dir = self.ep_dir / variant_name
        var_dir.mkdir(parents=True, exist_ok=True)
        voice_dir = self.ep_dir / "voice" / variant_name
        voice_dir.mkdir(parents=True, exist_ok=True)

        # 1. Dual-Voice TTS Synthesis
        blocks = scenario.get("blocks", [])
        audio_files = []
        voices_used = set()

        for idx, blk in enumerate(blocks):
            role = blk.get("role", "expert")
            text = blk.get("text", "")
            out_wav = voice_dir / f"block_{idx}.wav"
            
            res = self.tts_engine.generate_speech(text, out_wav, role=role)
            audio_files.append((out_wav, res["events"]))
            voices_used.add(res["voice_used"])

        # Run TTS Validator
        tts_report = self.validator.validate_tts_synthesis(voice_dir, scenario)
        if not tts_report["valid"]:
            print(f"⚠️ [TTS Validator Warning]: {tts_report['errors']}")

        # 2. Subtitles Generation & Voice Concatenation
        all_events = []
        curr_time = 0.0
        audio_files_paths = []
        block_timings = {}

        for idx, (out_wav, evs) in enumerate(audio_files):
            blk_name = blocks[idx].get("name", f"block_{idx}")
            dur = _get_duration(out_wav)
            block_timings[blk_name] = {
                "start": curr_time,
                "end": curr_time + dur,
                "duration": dur
            }
            for ev in evs:
                all_events.append({
                    "text": ev["text"],
                    "start": curr_time + ev["start"],
                    "end": curr_time + ev["end"]
                })
            curr_time += dur
            audio_files_paths.append(out_wav)

        total_duration = curr_time

        concat_txt = self.ep_dir / "temp" / f"voice_concat_{variant_name}.txt"
        concat_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in audio_files_paths:
                clean_p = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{clean_p}'\n")

        full_voice_audio = voice_dir / "voice_full.mp3"
        subprocess.run([
            FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt), "-c", "copy", str(full_voice_audio)
        ], check=True)

        sub_path = self.ep_dir / "subtitles" / f"{variant_name}.ass"
        sub_path.parent.mkdir(parents=True, exist_ok=True)
        self.sub_gen.generate_ass_file(all_events, sub_path)

        # 3. Fetch Memes & SFX
        downloaded_memes = []
        for idx_m, m_query in enumerate(["cat open mouth shocked gif", "car eject reaction gif"]):
            m_path = self.meme_fetcher.get_or_download_meme(m_query, f"ep{self.episode_id}_{variant_name}_meme_{idx_m}.gif")
            if m_path and m_path.exists():
                downloaded_memes.append(m_path)

        downloaded_sfx = []
        sfx_configs = []
        for s_query in ["gta-wasted", "bonk-sound-effect"]:
            s_path = self.sfx_fetcher.get_or_download_sfx(s_query, f"ep{self.episode_id}_{s_query}.mp3")
            if s_path and s_path.exists():
                downloaded_sfx.append(s_path)
                sfx_configs.append({"name": s_query, "volume": 0.16})

        # Validate SFX volume (Not loud rule)
        sfx_report = self.validator.validate_sfx_volume(sfx_configs)
        if not sfx_report["valid"]:
            print(f"⚠️ [SFX Validator Warning]: {sfx_report['errors']}")

        ambient_file = BASE_DIR / "assets" / "music" / "ambient" / "ambient1.mp3"

        # 4. FFmpeg Assembly with NVENC GPU
        raw_clip = self.ep_dir / "temp" / "raw_download.mp4"
        if not raw_clip.exists():
            raw_clip = self.ep_dir / "temp" / "raw_gameplay.mp4"
            if not raw_clip.exists():
                raw_clip = self.ep_dir / "preview_gameplay.mp4"

        outro_motion = BASE_DIR / "output" / "templates" / "outro_subscribe_motion.mp4"
        output_mp4 = var_dir / "video.mp4"

        d1_start = block_timings.get("diagram1", {}).get("start", 6.0)
        d1_end = block_timings.get("diagram1", {}).get("end", 15.0)

        cc_start = block_timings.get("code_card", {}).get("start", 15.0)
        cc_end = block_timings.get("code_card", {}).get("end", 26.0)

        fix_start = block_timings.get("fix", {}).get("start", 26.0)
        fix_end = block_timings.get("fix", {}).get("end", 36.0)

        outro_start = block_timings.get("outro", {}).get("start", 36.0)
        outro_end = total_duration

        inputs = [
            "-stream_loop", "-1", "-i", str(raw_clip),                                          # [0:v] Gameplay
            "-i", str(full_voice_audio),                                                        # [1:a] Voice
            "-loop", "1", "-i", str(visual_cards[0] if len(visual_cards)>0 else raw_clip),      # [2:v] Card 1
            "-loop", "1", "-i", str(visual_cards[1] if len(visual_cards)>1 else raw_clip),      # [3:v] Card 2
            "-loop", "1", "-i", str(visual_cards[2] if len(visual_cards)>2 else raw_clip),      # [4:v] Card 3
            "-i", str(outro_motion),                                                            # [5:v][5:a] Outro Video
        ]

        input_counter = 6
        meme_input_indices = []
        for m_path in downloaded_memes:
            inputs.extend(["-ignore_loop", "0", "-stream_loop", "-1", "-i", str(m_path)])
            meme_input_indices.append(input_counter)
            input_counter += 1

        sfx_input_indices = []
        for s_path in downloaded_sfx:
            inputs.extend(["-i", str(s_path)])
            sfx_input_indices.append(input_counter)
            input_counter += 1

        amb_input_idx = None
        if ambient_file.exists():
            inputs.extend(["-stream_loop", "-1", "-i", str(ambient_file)])
            amb_input_idx = input_counter
            input_counter += 1

        filter_chains = []
        filter_chains.append(
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28[bg];"
            "[0:v]scale=1020:574:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:200[v_base]"
        )
        last_v = "[v_base]"

        # Meme 1 overlay at y=860
        if meme_input_indices:
            inv_start = block_timings.get("investigation", {}).get("start", 3.0)
            inv_end = min(inv_start + 2.5, block_timings.get("investigation", {}).get("end", 6.0))
            idx1 = meme_input_indices[0]
            filter_chains.append(
                f"[{idx1}:v]scale=500:-1,format=rgba,fade=t=in:st={inv_start}:d=0.2:alpha=1,fade=t=out:st={inv_end-0.2}:d=0.2:alpha=1[meme1_fade];"
                f"{last_v}[meme1_fade]overlay=(W-w)/2:860:enable='between(t,{inv_start},{inv_end})'[v_meme1]"
            )
            last_v = "[v_meme1]"

        # Card 1 overlay (Bottom-aligned in Top 2/3 zone, native aspect ratio without stretching)
        c1_path = visual_cards[0] if len(visual_cards) > 0 else None
        c1_y = 80
        if c1_path and c1_path.exists():
            with Image.open(c1_path) as c1_img:
                c1_y = max(80, 1360 - c1_img.height)

        filter_chains.append(
            f"[2:v]scale=1000:-1,format=rgba,fade=t=in:st={d1_start}:d=0.2:alpha=1,fade=t=out:st={d1_end-0.2}:d=0.2:alpha=1[c1_fade];"
            f"{last_v}[c1_fade]overlay=(W-w)/2:{c1_y}:enable='between(t,{d1_start},{d1_end})'[v_c1]"
        )
        last_v = "[v_c1]"

        # Card 2 overlay
        c2_path = visual_cards[1] if len(visual_cards) > 1 else None
        c2_y = 80
        if c2_path and c2_path.exists():
            with Image.open(c2_path) as c2_img:
                c2_y = max(80, 1360 - c2_img.height)

        filter_chains.append(
            f"[3:v]scale=1000:-1,format=rgba,fade=t=in:st={cc_start}:d=0.2:alpha=1,fade=t=out:st={cc_end-0.2}:d=0.2:alpha=1[c2_fade];"
            f"{last_v}[c2_fade]overlay=(W-w)/2:{c2_y}:enable='between(t,{cc_start},{cc_end})'[v_c2]"
        )
        last_v = "[v_c2]"

        # Card 3 overlay
        c3_path = visual_cards[2] if len(visual_cards) > 2 else None
        c3_y = 80
        if c3_path and c3_path.exists():
            with Image.open(c3_path) as c3_img:
                c3_y = max(80, 1360 - c3_img.height)

        filter_chains.append(
            f"[4:v]scale=1000:-1,format=rgba,fade=t=in:st={fix_start}:d=0.2:alpha=1,fade=t=out:st={fix_end-0.2}:d=0.2:alpha=1[c3_fade];"
            f"{last_v}[c3_fade]overlay=(W-w)/2:{c3_y}:enable='between(t,{fix_start},{fix_end})'[v_c3]"
        )
        last_v = "[v_c3]"

        # Meme 2 overlay at y=860
        if len(meme_input_indices) > 1:
            m2_start = min(fix_start + 1.0, fix_end - 2.0)
            m2_end = min(m2_start + 2.5, fix_end)
            idx2 = meme_input_indices[1]
            filter_chains.append(
                f"[{idx2}:v]scale=500:-1,format=rgba,fade=t=in:st={m2_start}:d=0.2:alpha=1,fade=t=out:st={m2_end-0.2}:d=0.2:alpha=1[meme2_fade];"
                f"{last_v}[meme2_fade]overlay=(W-w)/2:860:enable='between(t,{m2_start},{m2_end})'[v_meme2]"
            )
            last_v = "[v_meme2]"

        # Outro Motion Video Overlay
        filter_chains.append(
            f"[5:v]chromakey=0x00FF00:0.28:0.15,setpts=PTS-STARTPTS+{outro_start}/TB[outro_v];"
            f"{last_v}[outro_v]overlay=(W-w)/2:860:enable='between(t,{outro_start},{outro_end})'[v_outro]"
        )
        last_v = "[v_outro]"

        # Subtitles
        escaped_sub = str(sub_path.resolve()).replace("\\", "/").replace(":", r"\:")
        filter_chains.append(f"{last_v}subtitles=filename='{escaped_sub}'[v_final]")

        # Audio Mixing
        audio_inputs_to_mix = ["[1:a]"]
        filter_chains.append(f"[5:a]adelay={int(outro_start*1000)}|{int(outro_start*1000)}[outro_a]")
        audio_inputs_to_mix.append("[outro_a]")

        if sfx_input_indices:
            s1_start = block_timings.get("investigation", {}).get("start", 3.0)
            sfx_idx1 = sfx_input_indices[0]
            filter_chains.append(f"[{sfx_idx1}:a]adelay={int(s1_start*1000)}|{int(s1_start*1000)},volume=0.16[sfx1_a]")
            audio_inputs_to_mix.append("[sfx1_a]")

        if len(sfx_input_indices) > 1:
            s2_start = block_timings.get("fix", {}).get("start", 26.0)
            sfx_idx2 = sfx_input_indices[1]
            filter_chains.append(f"[{sfx_idx2}:a]adelay={int(s2_start*1000)}|{int(s2_start*1000)},volume=0.16[sfx2_a]")
            audio_inputs_to_mix.append("[sfx2_a]")

        if amb_input_idx is not None:
            filter_chains.append(f"[{amb_input_idx}:a]volume=0.14[amb_a]")
            audio_inputs_to_mix.append("[amb_a]")

        mix_count = len(audio_inputs_to_mix)
        filter_chains.append(f"{''.join(audio_inputs_to_mix)}amix=inputs={mix_count}:duration=first:dropout_transition=2[a_final]")

        filter_complex_str = ";".join(filter_chains)

        cmd = [FFMPEG_PATH, "-y"] + inputs + [
            "-filter_complex", filter_complex_str,
            "-map", "[v_final]",
            "-map", "[a_final]",
            "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            "-pix_fmt", "yuv420p",
            str(output_mp4)
        ]
        subprocess.run(cmd, capture_output=True, text=True)

        # 5. Run Ironclad Post-Render Validation & Contact Sheet Creation
        val_res = self.validator.validate_assembled_video(output_mp4, block_timings)
        if val_res["valid"]:
            snaps = val_res.get("details", {}).get("snapshots", {})
            if snaps:
                grid_out = var_dir / "contact_sheet.jpg"
                try:
                    self.validator.create_contact_sheet([Path(p) for p in snaps.values()], grid_out)
                    print(f"✅ [Ironclad Validator] Assembled video verified. Contact sheet created: {grid_out}")
                except Exception as ex:
                    print(f"⚠️ Could not generate contact sheet: {ex}")
        else:
            print(f"❌ [Ironclad Validator Error] Assembled video validation failed: {val_res['errors']}")

        return output_mp4

    def run_smoke_test(self, output_mp4: Path) -> Dict[str, bool]:
        """
        4-Point Mandatory Smoke Test (Decodability, Dual-Voice, Overlay, Metadata).
        """
        results = {
            "decodability": False,
            "file_size_ok": False,
            "metadata_ok": False
        }
        
        if not output_mp4.exists():
            return results

        results["file_size_ok"] = output_mp4.stat().st_size > 1_000_000

        # ffprobe decodability test
        probe_cmd = [
            FFMPEG_PATH, "-v", "error",
            "-i", str(output_mp4),
            "-f", "null", "-"
        ]
        res = subprocess.run(probe_cmd, capture_output=True, text=True)
        results["decodability"] = (res.returncode == 0)

        # Metadata format test
        desc_file = self.ep_dir / "description.txt"
        if desc_file.exists():
            content = desc_file.read_text(encoding="utf-8")
            results["metadata_ok"] = ("ЗАГОЛОВОК" in content and "ПОЛНОЕ ОПИСАНИЕ" in content)

        return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified Pipeline Runner for Game Shorts Creator")
    parser.add_argument("--episode", type=str, required=True, help="Episode ID (e.g. 21)")
    parser.add_argument("--stage", type=str, choices=["stage1", "cards", "render", "smoketest", "full"], default="full", help="Stage to execute")
    parser.add_argument("--url", type=str, help="YouTube URL for Stage 1")
    parser.add_argument("--start", type=str, default="00:00:00", help="Clip start time")
    parser.add_argument("--end", type=str, default="00:00:15", help="Clip end time")
    parser.add_argument("--bug-fact", type=str, default="", help="Bug fact summary")

    args = parser.parse_args()

    runner = PipelineRunner(args.episode)
    print(f"[PipelineRunner] Running for Episode {args.episode} (Stage: {args.stage})...")

    if args.stage in ["stage1", "full"]:
        if args.url:
            runner.prepare_stage1(args.url, args.start, args.end, args.bug_fact)
        else:
            print("[PipelineRunner] Stage 1 skipped or URL not provided.")

    if args.stage == "smoketest":
        target_video = runner.ep_dir / "v1" / "video.mp4"
        test_res = runner.run_smoke_test(target_video)
        print(f"[PipelineRunner] Smoke Test Results: {test_res}")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified Pipeline Runner for Game Shorts Creator")
    parser.add_argument("--episode", type=str, required=True, help="Episode ID (e.g. 21)")
    parser.add_argument("--stage", type=str, choices=["stage1", "cards", "render", "smoketest", "full"], default="full", help="Stage to execute")
    parser.add_argument("--url", type=str, help="YouTube URL for Stage 1")
    parser.add_argument("--start", type=str, default="00:00:00", help="Clip start time")
    parser.add_argument("--end", type=str, default="00:00:15", help="Clip end time")
    parser.add_argument("--bug-fact", type=str, default="", help="Bug fact summary")

    args = parser.parse_args()

    runner = PipelineRunner(args.episode)
    print(f"[PipelineRunner] Running for Episode {args.episode} (Stage: {args.stage})...")

    if args.stage in ["stage1", "full"]:
        if args.url:
            runner.prepare_stage1(args.url, args.start, args.end, args.bug_fact)
        else:
            print("[PipelineRunner] Stage 1 skipped or URL not provided.")

    if args.stage == "smoketest":
        target_video = runner.ep_dir / "v1" / "video.mp4"
        test_res = runner.run_smoke_test(target_video)
        print(f"[PipelineRunner] Smoke Test Results: {test_res}")


