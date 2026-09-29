"""Configuracion central del pipeline."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _abs(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (ROOT / p)


@dataclass
class Settings:
    hf_token: str = os.getenv("HF_TOKEN", "")

    opencode_api_key: str = os.getenv("OPENCODE_API_KEY", "")
    opencode_base_url: str = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
    opencode_model: str = os.getenv("OPENCODE_MODEL", "deepseek-v4-flash")

    avatar_prompt: str = os.getenv("AVATAR_PROMPT", "")
    avatar_image: Path = _abs(os.getenv("AVATAR_IMAGE", "assets/avatar/avatar.jpg"))
    avatar_i2v_space: str = os.getenv("AVATAR_I2V_SPACE", "Lightricks/ltx-video-distilled")
    avatar_i2v_fallback: str = os.getenv(
        "AVATAR_I2V_FALLBACK", "multimodalart/stable-video-diffusion"
    )
    avatar_motion_prompt: str = os.getenv("AVATAR_MOTION_PROMPT", "")
    avatar_negative_prompt: str = os.getenv("AVATAR_NEGATIVE_PROMPT", "")
    avatar_i2v_duration: int = int(os.getenv("AVATAR_I2V_DURATION", "3"))
    avatar_i2v_width: int = int(os.getenv("AVATAR_I2V_WIDTH", "640"))
    avatar_i2v_height: int = int(os.getenv("AVATAR_I2V_HEIGHT", "576"))
    enhance_enabled: bool = os.getenv("ENHANCE_ENABLED", "true").lower() in ("1", "true", "yes")
    enhance_space: str = os.getenv("ENHANCE_SPACE", "sczhou/CodeFormer")
    enhance_fidelity: float = float(os.getenv("ENHANCE_FIDELITY", "0.7"))

    subtitle_enabled: bool = os.getenv("SUBTITLE_ENABLED", "true").lower() in ("1", "true", "yes")
    subtitle_font: str = os.getenv("SUBTITLE_FONT", "Arial")
    subtitle_fontsize: int = int(os.getenv("SUBTITLE_FONTSIZE", "62"))
    subtitle_outline: int = int(os.getenv("SUBTITLE_OUTLINE", "5"))
    subtitle_margin_v: int = int(os.getenv("SUBTITLE_MARGIN_V", "60"))
    subtitle_max_words: int = int(os.getenv("SUBTITLE_MAX_WORDS", "3"))
    subtitle_max_gap: float = float(os.getenv("SUBTITLE_MAX_GAP", "0.6"))
    subtitle_max_duration: float = float(os.getenv("SUBTITLE_MAX_DURATION", "1.8"))

    niche: str = os.getenv("NICHE", "curiosidades")
    discover_per_query: int = int(os.getenv("DISCOVER_PER_QUERY", "5"))
    discover_min_duration: int = int(os.getenv("DISCOVER_MIN_DURATION", "120"))
    discover_max_duration: int = int(os.getenv("DISCOVER_MAX_DURATION", "5400"))

    tts_enabled: bool = os.getenv("TTS_ENABLED", "true").lower() in ("1", "true", "yes")
    tts_space: str = os.getenv("TTS_SPACE", "leonelhs/kokoro-tts-spanish")
    tts_voice: str = os.getenv("TTS_VOICE", "ef_dora")
    tts_speed: float = float(os.getenv("TTS_SPEED", "0.95"))
    clip_audio_volume: float = float(os.getenv("CLIP_AUDIO_VOLUME", "0.35"))
    voiceover_volume: float = float(os.getenv("VOICEOVER_VOLUME", "1.0"))

    whisper_model: str = os.getenv("WHISPER_MODEL", "small")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")

    reel_width: int = int(os.getenv("REEL_WIDTH", "1080"))
    reel_height: int = int(os.getenv("REEL_HEIGHT", "1920"))
    reel_fps: int = int(os.getenv("REEL_FPS", "30"))
    clip_min_seconds: int = int(os.getenv("CLIP_MIN_SECONDS", "20"))
    clip_max_seconds: int = int(os.getenv("CLIP_MAX_SECONDS", "60"))
    max_clips: int = int(os.getenv("MAX_CLIPS", "3"))

    work_dir: Path = ROOT / "work"
    output_dir: Path = ROOT / "output"
    assets_dir: Path = ROOT / "assets"


settings = Settings()
