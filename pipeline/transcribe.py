"""Transcribe el video con faster-whisper (segmentos + palabras)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import settings


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Word:
    start: float
    end: float
    text: str


def _cache_path(video: Path) -> Path:
    return settings.work_dir / f"transcript_{video.stem}.json"


def _load_cache(video: Path) -> dict | None:
    cache = _cache_path(video)
    if not cache.exists():
        return None
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if isinstance(data, list):
        return {"segments": data, "words": []}
    return data


def transcribe(video: Path) -> list[Segment]:
    cached = _load_cache(video)
    if cached is not None:
        return [Segment(**s) for s in cached.get("segments", [])]

    from faster_whisper import WhisperModel

    model = WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type="int8",
    )
    segments, _info = model.transcribe(
        str(video), vad_filter=True, word_timestamps=True
    )

    seg_list: list[Segment] = []
    word_list: list[Word] = []
    for idx, s in enumerate(segments, 1):
        seg_list.append(Segment(start=s.start, end=s.end, text=s.text.strip()))
        for w in s.words or []:
            text = w.word.strip()
            if text:
                word_list.append(Word(start=w.start, end=w.end, text=text))
        if idx % 25 == 0:
            print(f"    ... transcritos {idx} segmentos (t={s.end:.0f}s)", flush=True)

    _cache_path(video).write_text(
        json.dumps(
            {
                "segments": [asdict(s) for s in seg_list],
                "words": [asdict(w) for w in word_list],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return seg_list


def load_words(video: Path) -> list[Word]:
    cached = _load_cache(video)
    if not cached:
        return []
    return [Word(**w) for w in cached.get("words", [])]


def format_transcript(segments: list[Segment]) -> str:
    return "\n".join(f"[{s.start:6.1f} - {s.end:6.1f}] {s.text}" for s in segments)
