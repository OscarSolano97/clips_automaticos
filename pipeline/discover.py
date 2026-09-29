"""Descubre videos de YouTube con licencia Creative Commons por nicho."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from .config import settings

CC_FILTER = "EgIwAQ%3D%3D"

NICHE_QUERIES: dict[str, list[str]] = {
    "curiosidades": [
        "datos curiosos impactantes",
        "cosas que no sabias curiosidades",
        "curiosidades sorprendentes del mundo",
        "datos increibles ciencia",
    ],
    "finanzas": [
        "errores financieros que cometes",
        "educacion financiera dinero",
        "habitos para ahorrar dinero",
        "como salir de deudas",
    ],
}


@dataclass
class Candidate:
    url: str
    video_id: str
    title: str
    duration: float
    uploader: str


def _entry_to_candidate(entry: dict) -> Candidate | None:
    vid = entry.get("id")
    if not vid:
        return None
    return Candidate(
        url=f"https://www.youtube.com/watch?v={vid}",
        video_id=vid,
        title=entry.get("title") or "",
        duration=float(entry.get("duration") or 0),
        uploader=entry.get("uploader") or "",
    )


def search(
    niche: str,
    per_query: int | None = None,
    min_duration: int | None = None,
    max_duration: int | None = None,
    exclude: set[str] | None = None,
) -> list[Candidate]:
    from yt_dlp import YoutubeDL

    per_query = per_query or settings.discover_per_query
    min_duration = min_duration or settings.discover_min_duration
    max_duration = max_duration or settings.discover_max_duration
    exclude = exclude or set()

    queries = NICHE_QUERIES.get(niche, [niche])
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    results: list[Candidate] = []
    seen: set[str] = set()
    for query in queries:
        url = (
            "https://www.youtube.com/results?"
            f"search_query={quote_plus(query)}&sp={CC_FILTER}"
        )
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:  # noqa: BLE001
            continue
        for entry in (info.get("entries") or [])[:per_query]:
            cand = _entry_to_candidate(entry)
            if cand is None or cand.video_id in seen or cand.video_id in exclude:
                continue
            seen.add(cand.video_id)
            if cand.duration and not (min_duration <= cand.duration <= max_duration):
                continue
            results.append(cand)
    return results
