"""CLI del pipeline de clips virales.

Uso:
  python cli.py avatar                         # avatar (imagen + animacion + loop)
  python cli.py auto --niche curiosidades -v 2  # TODO: buscar -> editar -> listo
  python cli.py analyze "<url-o-ruta>"
  python cli.py build   "<url-o-ruta>"
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from pipeline import (
    animate,
    avatar,
    discover,
    download,
    enhance,
    montage,
    select_clips,
    subtitles,
    transcribe,
    tts,
)
from pipeline.config import settings


def _utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def cmd_avatar(args: argparse.Namespace) -> None:
    image = avatar.ensure_avatar_image(force=True)
    print(f"Avatar imagen: {image}")
    try:
        image = enhance.enhance_avatar(force=True)
        print(f"Avatar rostro mejorado: {image}")
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] No se pudo mejorar el rostro: {exc}")
    if not args.static:
        try:
            animate.animate_avatar(force=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[aviso] No se pudo animar: {exc}")
    loop = avatar.build_loop(force=True)
    print(f"Avatar loop  : {loop}")


def cmd_animate(_args: argparse.Namespace) -> None:
    motion = animate.animate_avatar(force=True)
    loop = avatar.build_loop(force=True)
    print(f"Avatar animado: {motion}")
    print(f"Avatar loop   : {loop}")


def _process_video(source: Path, niche: str) -> list[dict]:
    print("  Transcribiendo con Whisper...")
    segments = transcribe.transcribe(source)
    words = transcribe.load_words(source)
    print(f"  Segmentos: {len(segments)} | palabras: {len(words)}")

    print(f"  Seleccionando clips con {settings.opencode_model} (nicho: {niche})...")
    clips = select_clips.select_clips(segments, niche=niche)

    avatar_loop = avatar.build_loop()
    results: list[dict] = []
    for i, clip in enumerate(clips, 1):
        print(f"\n  [{i}/{len(clips)}] {clip.title} ({clip.start:.0f}s-{clip.end:.0f}s)")
        clip_video = montage.cut_clip(source, clip, i)

        ass_file = None
        if settings.subtitle_enabled:
            ass_file = subtitles.build_ass(
                words, clip.start, clip.end, settings.work_dir / f"sub_{i:02d}.ass"
            )

        voiceover = None
        if settings.tts_enabled and clip.voiceover:
            try:
                voiceover = tts.generate(
                    clip.voiceover, settings.work_dir / f"vo_{i:02d}.wav"
                )
                print(f"      Voz: {clip.voiceover[:60]}...")
            except Exception as exc:  # noqa: BLE001
                print(f"      [aviso] TTS fallo: {str(exc)[:80]}")

        reel = montage.build_reel(
            clip_video, avatar_loop, i, clip.title, ass_file, voiceover
        )
        print(f"      Reel: {reel}")
        results.append(
            {
                "reel": str(reel),
                "title": clip.title,
                "caption": clip.caption,
                "hashtags": clip.hashtags,
                "voiceover": clip.voiceover,
                "clip": asdict(clip),
            }
        )
    return results


def _write_manifest(results: list[dict]) -> Path:
    meta = settings.output_dir / "publish_manifest.json"
    existing: list[dict] = []
    if meta.exists():
        try:
            existing = json.loads(meta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
    meta.write_text(
        json.dumps(existing + results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def cmd_analyze(args: argparse.Namespace) -> None:
    source = download.get_source(args.source)
    niche = args.niche or settings.niche
    print(f"Fuente: {source}")

    print("Transcribiendo con Whisper...")
    segments = transcribe.transcribe(source)

    print(f"Seleccionando clips con {settings.opencode_model} (nicho: {niche})...")
    clips = select_clips.select_clips(segments, niche=niche)

    out = settings.work_dir / "clips.json"
    out.write_text(
        json.dumps([asdict(c) for c in clips], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for i, c in enumerate(clips, 1):
        print(f"\n[{i}] {c.title} ({c.start:.1f}s - {c.end:.1f}s)")
        print(f"    Motivo : {c.reason}")
        print(f"    Caption: {c.caption}")
        if c.voiceover:
            print(f"    Voz    : {c.voiceover}")


def cmd_build(args: argparse.Namespace) -> None:
    source = download.get_source(args.source)
    niche = args.niche or settings.niche
    print(f"Fuente: {source} (nicho: {niche})")
    results = _process_video(source, niche)
    meta = _write_manifest(results)
    print(f"\nListo. {len(results)} reels en {settings.output_dir}")
    print(f"Manifiesto: {meta}")


def cmd_auto(args: argparse.Namespace) -> None:
    niche = args.niche or settings.niche
    print(f"Buscando videos de YouTube (Creative Commons) del nicho '{niche}'...")
    candidates = discover.search(niche, per_query=args.per_query)
    if not candidates:
        print("No se encontraron videos. Prueba otro nicho o revisa la conexion.")
        return

    print(f"Encontrados {len(candidates)} candidatos. Procesando {args.videos}...")
    all_results: list[dict] = []
    used: list[str] = []
    for k, cand in enumerate(candidates[: args.videos], 1):
        print(f"\n=== Video {k}/{args.videos}: {cand.title[:70]} ===")
        print(f"    {cand.url} ({cand.duration:.0f}s)")
        try:
            source = download.get_source(cand.url)
            results = _process_video(source, niche)
            for r in results:
                r["source_url"] = cand.url
                r["source_title"] = cand.title
            all_results.extend(results)
            used.append(cand.video_id)
        except Exception as exc:  # noqa: BLE001
            print(f"    [error] No se pudo procesar: {str(exc)[:120]}")

    write = _write_manifest(all_results)
    print(f"\n=== LISTO ===")
    print(f"{len(all_results)} reels editados en: {settings.output_dir}")
    print(f"Manifiesto (caption + hashtags): {write}")


def main() -> None:
    _utf8()
    parser = argparse.ArgumentParser(description="Pipeline de clips virales")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_avatar = sub.add_parser("avatar", help="Genera imagen + animacion + loop del avatar")
    p_avatar.add_argument("--static", action="store_true", help="Solo imagen, sin animar")
    p_avatar.set_defaults(func=cmd_avatar)

    p_animate = sub.add_parser("animate", help="Anima el avatar (image-to-video gratis)")
    p_animate.set_defaults(func=cmd_animate)

    p_auto = sub.add_parser("auto", help="TODO automatico: busca, edita y deja listos los reels")
    p_auto.add_argument("--niche", help="curiosidades | finanzas")
    p_auto.add_argument("-v", "--videos", type=int, default=1, help="Cuantos videos procesar")
    p_auto.add_argument("--per-query", type=int, default=None, help="Resultados por busqueda")
    p_auto.set_defaults(func=cmd_auto)

    p_analyze = sub.add_parser("analyze", help="Transcribe y elige clips (sin montar)")
    p_analyze.add_argument("source", help="Ruta local o URL del video largo")
    p_analyze.add_argument("--niche", help="curiosidades | finanzas")
    p_analyze.set_defaults(func=cmd_analyze)

    p_build = sub.add_parser("build", help="Pipeline completo desde un video dado")
    p_build.add_argument("source", help="Ruta local o URL del video largo")
    p_build.add_argument("--niche", help="curiosidades | finanzas")
    p_build.set_defaults(func=cmd_build)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
