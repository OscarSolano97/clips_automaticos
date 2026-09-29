"""Genera subtitulos tipo viral (karaoke) en formato ASS para quemarlos con FFmpeg."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import settings
from .transcribe import Word


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _clean(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\\", "/")


@dataclass
class _Chunk:
    start: float
    end: float
    words: list[Word]


def _group(words: list[Word]) -> list[_Chunk]:
    max_words = settings.subtitle_max_words
    max_gap = settings.subtitle_max_gap
    max_dur = settings.subtitle_max_duration

    chunks: list[_Chunk] = []
    current: list[Word] = []
    for w in words:
        if current:
            gap = w.start - current[-1].end
            dur = w.end - current[0].start
            if len(current) >= max_words or gap > max_gap or dur > max_dur:
                chunks.append(_Chunk(current[0].start, current[-1].end, current))
                current = []
        current.append(w)
    if current:
        chunks.append(_Chunk(current[0].start, current[-1].end, current))
    return chunks


def _header() -> str:
    w, h = settings.reel_width, 960
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {w}\n"
        f"PlayResY: {h}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Base,{settings.subtitle_font},{settings.subtitle_fontsize},"
        "&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,"
        f"1,{settings.subtitle_outline},2,2,60,60,{settings.subtitle_margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def build_ass(
    words: list[Word], clip_start: float, clip_end: float, out_path: Path
) -> Path | None:
    if not settings.subtitle_enabled:
        return None

    inside = [
        Word(start=w.start - clip_start, end=w.end - clip_start, text=w.text)
        for w in words
        if w.end > clip_start and w.start < clip_end
    ]
    if not inside:
        return None

    lines = [_header()]
    for chunk in _group(inside):
        parts = []
        for i, w in enumerate(chunk.words):
            if i + 1 < len(chunk.words):
                dur = chunk.words[i + 1].start - w.start
            else:
                dur = w.end - w.start
            k = max(1, int(round(dur * 100)))
            parts.append(f"{{\\k{k}}}{_clean(w.text.upper())} ")
        text = "".join(parts).strip()
        lines.append(
            f"Dialogue: 0,{_fmt_time(chunk.start)},{_fmt_time(chunk.end)},"
            f"Base,,0,0,0,,{{\\fad(60,60)}}{text}\n"
        )

    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path
