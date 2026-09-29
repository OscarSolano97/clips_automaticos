"""Corta clips y monta el reel split-screen (avatar arriba, clip abajo)."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import settings
from .ffmpeg import ffmpeg_exe
from .select_clips import Clip


def _slug(text: str, fallback: str = "clip") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40] or fallback


def cut_clip(source: Path, clip: Clip, index: int) -> Path:
    out = settings.work_dir / f"clip_{index:02d}_{_slug(clip.title)}.mp4"
    cmd = [
        ffmpeg_exe(), "-y",
        "-ss", f"{clip.start:.3f}",
        "-i", str(source),
        "-t", f"{clip.end - clip.start:.3f}",
        "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
        "-c:a", "aac", "-avoid_negative_ts", "make_zero",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def _has_audio(path: Path) -> bool:
    result = subprocess.run(
        [ffmpeg_exe(), "-i", str(path)], capture_output=True, text=True
    )
    return "Audio:" in result.stderr


def build_reel(
    clip_video: Path,
    avatar_loop: Path,
    index: int,
    title: str,
    ass_file: Path | None = None,
    voiceover: Path | None = None,
) -> Path:
    w, top_h = settings.reel_width, 960
    bottom_h = settings.reel_height - top_h
    out = settings.output_dir / f"reel_{index:02d}_{_slug(title)}.mp4"
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    bottom = (
        f"scale={w}:{bottom_h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{bottom_h},setsar=1"
    )
    if ass_file is not None:
        bottom += f",ass={ass_file.name}"

    video_chain = (
        f"[0:v]scale={w}:{top_h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{top_h},setsar=1[top];"
        f"[1:v]{bottom}[bottom];"
        f"[top][bottom]vstack=inputs=2,fps={settings.reel_fps},format=yuv420p[v]"
    )

    clip_has_audio = _has_audio(clip_video)
    cmd = [ffmpeg_exe(), "-y", "-stream_loop", "-1", "-i", str(avatar_loop), "-i", str(clip_video)]

    if voiceover is not None:
        cmd += ["-i", str(voiceover)]
        clip_vol = settings.clip_audio_volume
        if clip_has_audio:
            audio_chain = (
                f";[1:a]volume={clip_vol}[orig];"
                f"[2:a]volume={settings.voiceover_volume}[vo];"
                f"[orig][vo]amix=inputs=2:duration=first:normalize=0[a]"
            )
        else:
            audio_chain = (
                f";[2:a]volume={settings.voiceover_volume},apad[a]"
            )
        filter_complex = video_chain + audio_chain
        cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-filter_complex", video_chain, "-map", "[v]"]
        if clip_has_audio:
            cmd += ["-map", "1:a?"]

    cmd += [
        "-c:v", "libx264", "-crf", "21", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(
        cmd, check=True, capture_output=True,
        cwd=str(ass_file.parent) if ass_file is not None else None,
    )
    return out
