import re
from pathlib import Path
from typing import List, Dict, Any


def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS subtitle time string: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


class SubtitleGenerator:
    def __init__(
        self,
        font_name: str = "Arial",
        font_size: int = 42,
        primary_color: str = "&H0000FFFF",   # Bright Yellow in BGR: &H00BBGGRR
        outline_color: str = "&H00000000",   # Black border
        outline_width: int = 5,
        shadow_width: int = 2,
        margin_v: int = 420                  # Placed comfortably above YouTube Subscribe button and Shorts UI
    ):
        self.font_name = font_name
        self.font_size = font_size
        self.primary_color = primary_color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.shadow_width = shadow_width
        self.margin_v = margin_v

    def split_sentence_into_chunks(self, sentence_event: Dict[str, Any], max_words: int = 4) -> List[Dict[str, Any]]:
        """
        Splits a sentence into punchy short phrases of 2-4 words with proportional timing.
        """
        raw_text = sentence_event["text"].strip()
        words = [w for w in re.split(r'\s+', raw_text) if w]
        if not words:
            return []

        start = sentence_event["start"]
        end = sentence_event["end"]
        duration = max(0.2, end - start)

        total_chars = sum(len(w) for w in words)
        if total_chars == 0:
            total_chars = 1

        # Group words into chunks of max_words
        chunks = []
        for i in range(0, len(words), max_words):
            chunk_words = words[i:i + max_words]
            chunks.append(chunk_words)

        result = []
        current_time = start
        for chunk_words in chunks:
            chunk_chars = sum(len(w) for w in chunk_words)
            chunk_duration = duration * (chunk_chars / total_chars)
            chunk_end = current_time + chunk_duration

            # Capitalize and format
            display_text = " ".join(chunk_words).upper()

            result.append({
                "text": display_text,
                "start": current_time,
                "end": chunk_end
            })
            current_time = chunk_end

        return result

    def generate_ass_file(
        self,
        events: List[Dict[str, Any]],
        output_ass_path: Path,
        max_words_per_line: int = 3
    ) -> Path:
        """
        Generates an ASS subtitle file with TikTok Shorts style.
        """
        output_ass_path = Path(output_ass_path)
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)

        all_dialogue_chunks = []
        for ev in events:
            # We process sentences or words
            chunks = self.split_sentence_into_chunks(ev, max_words=max_words_per_line)
            all_dialogue_chunks.extend(chunks)

        header = f"""[Script Info]
Title: Dynamic Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TikTokStyle,{self.font_name},{self.font_size},{self.primary_color},&H000000FF,{self.outline_color},&H80000000,-1,0,0,0,100,100,1,0,1,{self.outline_width},{self.shadow_width},2,40,40,{self.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogue_lines = []
        for ch in all_dialogue_chunks:
            start_str = format_ass_time(ch["start"])
            end_str = format_ass_time(ch["end"])
            # ASS tag {\b1} for extra bold
            line_text = f"{{\\b1}}{ch['text']}"
            dialogue_lines.append(
                f"Dialogue: 0,{start_str},{end_str},TikTokStyle,,0,0,0,,{line_text}"
            )

        full_content = header + "\n".join(dialogue_lines) + "\n"

        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        return output_ass_path
