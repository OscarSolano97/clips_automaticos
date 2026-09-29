"""Selecciona los mejores clips usando el LLM de opencode-go, por nicho."""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from openai import OpenAI

from .config import settings
from .transcribe import Segment


@dataclass
class Clip:
    start: float
    end: float
    title: str
    reason: str
    caption: str = ""
    hashtags: str = ""
    voiceover: str = ""


NICHE_HINTS: dict[str, str] = {
    "curiosidades": (
        "Nicho: DATOS/CURIOSIDADES IMPACTANTES. Prioriza datos sorprendentes, "
        "cifras que impactan, revelaciones, 'no sabias que...', hechos que "
        "rompen creencias. Hook inmediato que provoque asombro."
    ),
    "finanzas": (
        "Nicho: FINANZAS/DINERO. Prioriza errores financieros comunes, consejos "
        "de dinero concretos y accionables, habitos que ahorran o multiplican, "
        "mentiras sobre el dinero. Debe dar valor practico."
    ),
}

SYSTEM_PROMPT = (
    "Eres un editor experto de contenido viral en espanol para TikTok y Reels. "
    "Analizas transcripciones con timestamps y eliges los fragmentos con mayor "
    "potencial de retencion y enganche. "
    "CRITICO: el primer segundo del clip debe ser un hook fuerte. "
    "Respondes SIEMPRE con JSON valido, sin texto adicional."
)


def _build_user_prompt(segments: list[Segment], n: int, niche: str) -> str:
    transcript = "\n".join(f"[{s.start:.1f}-{s.end:.1f}] {s.text}" for s in segments)
    hint = NICHE_HINTS.get(niche, "")
    return f"""{hint}

Transcripcion del video:

{transcript}

Elige los {n} mejores clips. Cada clip debe durar entre {settings.clip_min_seconds} y {settings.clip_max_seconds} segundos y cortar en frases completas.

Ademas, para cada clip escribe un "voiceover": lo que diria una mujer joven frente a la camara reaccionando/aportando a ese clip. Debe ser en espanol, 1-2 frases (max 200 caracteres), en primera persona, con gancho y valor (esto se convierte en VOZ, no se muestra como texto).

Devuelve EXACTAMENTE este JSON:
{{
  "clips": [
    {{
      "start": 12.5,
      "end": 45.0,
      "title": "titulo corto del clip",
      "reason": "por que este clip es viral",
      "caption": "texto para la publicacion, gancho en la primera linea",
      "hashtags": "#tag1 #tag2 #tag3",
      "voiceover": "frase que dira la voz del avatar"
    }}
  ]
}}"""


def _client() -> OpenAI:
    if not settings.opencode_api_key:
        raise RuntimeError("Falta OPENCODE_API_KEY en .env")
    return OpenAI(
        api_key=settings.opencode_api_key,
        base_url=settings.opencode_base_url,
        default_headers={"x-opencode-session": str(uuid.uuid4())},
    )


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.S)
        if brace:
            text = brace.group(0)
    return json.loads(text)


def select_clips(
    segments: list[Segment], n: int | None = None, niche: str | None = None
) -> list[Clip]:
    n = n or settings.max_clips
    niche = niche or settings.niche
    client = _client()
    resp = client.chat.completions.create(
        model=settings.opencode_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(segments, n, niche)},
        ],
        temperature=0.7,
    )
    data = _extract_json(resp.choices[0].message.content or "")

    clips: list[Clip] = []
    for c in data.get("clips", []):
        start = float(c["start"])
        end = float(c["end"])
        if end <= start:
            continue
        clips.append(
            Clip(
                start=start,
                end=end,
                title=str(c.get("title", "clip")),
                reason=str(c.get("reason", "")),
                caption=str(c.get("caption", "")),
                hashtags=str(c.get("hashtags", "")),
                voiceover=str(c.get("voiceover", "")),
            )
        )
    return clips
