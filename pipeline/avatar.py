"""Genera el avatar (gratis) y un loop de video con movimiento sutil.

Generacion de imagen: Hugging Face Space publico (FLUX.1-schnell), gratis y sin
API key. Si falla, permite usar una imagen propia en AVATAR_IMAGE.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import hf
from .config import settings
from .ffmpeg import ffmpeg_exe

HF_SPACE = "black-forest-labs/FLUX.1-schnell"


def _generate_with_hf(prompt: str, width: int, height: int, out: Path) -> Path:
    def run() -> str:
        client = hf.client(HF_SPACE)
        result, _seed = client.predict(
            prompt=prompt,
            seed=42,
            randomize_seed=True,
            width=float(width),
            height=float(height),
            num_inference_steps=4,
            api_name="/infer",
        )
        src = result.get("path") if isinstance(result, dict) else result
        if not src:
            raise RuntimeError("El Space no devolvio ninguna imagen")
        return src

    shutil.copy2(hf.call(run), out)
    return out


def ensure_avatar_image(force: bool = False) -> Path:
    dest = settings.avatar_image
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        return dest

    prompt = settings.avatar_prompt.strip()
    if not prompt:
        raise RuntimeError("Falta AVATAR_PROMPT en .env")

    try:
        return _generate_with_hf(prompt, settings.reel_width, 960, dest)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "No se pudo generar el avatar. Opciones:\n"
            "  1) Reintenta (los Spaces gratuitos a veces estan ocupados).\n"
            f"  2) Coloca tu propia imagen en: {dest}\n"
            f"Error original: {exc}"
        ) from exc


def _loop_from_video(video: Path, out: Path) -> Path:
    w, h = settings.reel_width, 960
    scale = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},fps=25,setsar=1"
    )
    fc = (
        f"[0:v]{scale},split=2[a][b];"
        f"[b]reverse[r];[a][r]concat=n=2:v=1:a=0,format=yuv420p[v]"
    )
    subprocess.run(
        [ffmpeg_exe(), "-y", "-i", str(video), "-filter_complex", fc, "-map", "[v]",
         "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", str(out)],
        check=True, capture_output=True,
    )
    return out


def build_loop(seconds: int = 12, force: bool = False) -> Path:
    out = settings.assets_dir / "avatar" / "avatar_loop.mp4"
    if out.exists() and not force:
        return out

    motion = settings.assets_dir / "avatar" / "avatar_motion.mp4"
    if motion.exists():
        return _loop_from_video(motion, out)

    image = ensure_avatar_image()
    w, h = settings.reel_width, 960
    vf = (
        f"scale={int(w * 1.2)}:-2,"
        f"zoompan=z='min(zoom+0.0006,1.15)':d={seconds * 25}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=25,"
        "format=yuv420p"
    )
    cmd = [
        ffmpeg_exe(), "-y",
        "-loop", "1", "-i", str(image),
        "-t", str(seconds),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out
