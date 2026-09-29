# Clip Studio

Pipeline automatizado para convertir un video largo en reels verticales (9:16)
con formato **split-screen** (avatar arriba, clip abajo) listos para TikTok y
Facebook Reels.

## Arquitectura

```
[BUSQUEDA]  discover.py -> YouTube (filtro Creative Commons) por nicho
        |
        v
[VIDEO]     yt-dlp -> descarga
        |
        v
[1] Whisper (local)  -> transcripcion con timestamps por palabra
        |
        v
[2] opencode-go LLM  -> elige clips + caption + hashtags + guion de VOZ
        |
        v
[3] Kokoro (HF)      -> voz en espanol del avatar (voiceover)
        |
        v
[4] FFmpeg           -> corta clip + subtitulos karaoke + monta split-screen
        |
        v
[REEL LISTO]  output/reel_XX.mp4 (9:16, 1080x1920) listo para subir
        |
        v
[5] Playwright       -> publicacion en TikTok / Facebook  (Fase 3)
```

## Requisitos

- Python 3.11+
- Conexion a internet la primera vez (descarga modelos Whisper y genera el avatar)
- FFmpeg: **no hace falta instalarlo**, se usa el binario incluido en `imageio-ffmpeg`

## Instalacion

```bash
cd C:\Users\HP\clip-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuracion

Las claves y ajustes viven en `.env` (ya creado):

| Variable            | Descripcion                                        |
| ------------------- | -------------------------------------------------- |
| `OPENCODE_API_KEY`  | API key de opencode-go (ya configurada)            |
| `OPENCODE_BASE_URL` | `https://opencode.ai/zen/go/v1`                    |
| `OPENCODE_MODEL`    | Modelo que elige los clips (`deepseek-v4-flash`)   |
| `HF_TOKEN`          | Token gratis de Hugging Face (quota de los Spaces) |
| `AVATAR_PROMPT`     | Descripcion del avatar a generar                   |
| `NICHE`             | `curiosidades` / `finanzas` (nicho por defecto)    |
| `TTS_ENABLED`       | Genera la voz del avatar (`true`/`false`)          |
| `TTS_VOICE`         | Voz de Kokoro (`ef_dora` femenina, `em_alex`...)    |
| `CLIP_AUDIO_VOLUME` | Volumen del audio original bajo la voz (0-1)       |
| `WHISPER_MODEL`     | `tiny` / `base` / `small` / `medium`               |
| `CLIP_MIN_SECONDS`  | Duracion minima de cada clip                       |
| `CLIP_MAX_SECONDS`  | Duracion maxima de cada clip                       |
| `MAX_CLIPS`         | Cuantos clips extraer por video                    |

> Modelos gratis disponibles en opencode-go: `longcat-2.5-preview-free`,
> `space-bunny-free`. Para mejor calidad usa `deepseek-v4-flash` (muy barato).

## Uso

### Flujo 100% automatico (recomendado)

Busca, descarga, edita y deja los reels listos para subir:

```bash
# 1. Generar el avatar una sola vez
python cli.py avatar

# 2. TODO automatico: busca en YouTube CC, edita y deja listos los reels
python cli.py auto --niche curiosidades -v 1
python cli.py auto --niche finanzas -v 2
```

Esto hace: buscar videos CC del nicho -> descargar -> transcribir -> elegir
clips + caption/hashtags + guion de voz -> generar la voz (Kokoro) -> montar los
reels con avatar animado + subtitulos karaoke -> dejarlos en `output/`.

Nichos disponibles: **`curiosidades`** y **`finanzas`** (se definen en
`pipeline/discover.py` -> `NICHE_QUERIES`).

### Desde un video concreto

```bash
python cli.py analyze "https://youtube.com/watch?v=XXXX"   # solo analiza
python cli.py build   "https://youtube.com/watch?v=XXXX"   # edita ese video
python cli.py build   "C:\ruta\video.mp4"
```

Los reels quedan en `output/` y el manifiesto de publicacion (caption +
hashtags + guion de voz) en `output/publish_manifest.json`.

## Avatar (gratis)

El avatar es una mujer realista sentada en un setup, **animada** (parpadeo,
movimiento de cabeza, respiracion) y en loop.

1. **Imagen**: FLUX.1-schnell (Hugging Face Space publico, sin costo).
2. **Animacion**: image-to-video con
   - `Lightricks/ltx-video-distilled` (movimiento llamativo), y si falla
   - `multimodalart/stable-video-diffusion` (micro-movimiento natural).
3. **Loop**: el clip se reproduce en **ping-pong** (adelante + reversa) para
   repetir sin salto.

```bash
python cli.py avatar          # imagen + animacion + loop
python cli.py avatar --static # solo imagen (sin animar)
python cli.py animate         # solo la animacion (usa la imagen existente)
```

### Token de Hugging Face (necesario para animar)

Los Spaces usan **ZeroGPU**, que da quota gratis pero limitada por IP. Para
tener quota suficiente crea un token gratis:

1. Cuenta gratis en <https://huggingface.co/join>
2. Token tipo **Read** en <https://huggingface.co/settings/tokens>
3. Pegalo en `.env`: `HF_TOKEN=hf_...`

Si no hay token o los Spaces fallan, el pipeline cae automaticamente al avatar
**estatico con zoom** (sigue funcionando).

- Edita `AVATAR_PROMPT` / `AVATAR_MOTION_PROMPT` en `.env` y repite.
- Tambien puedes poner tu propia imagen en `assets/avatar/avatar.jpg`.

> Nota: los proveedores `opencode-go` y `opencode` (Zen) **solo ofrecen modelos
> de texto**, no de imagen/video. Por eso el avatar usa los Spaces gratuitos de
> Hugging Face.

## Subtitulos automaticos

- Whisper transcribe con **timestamps por palabra**.
- `pipeline/subtitles.py` genera un `.ass` estilo viral (mayusculas, negrita,
  contorno negro) con **karaoke**: la palabra activa se resalta en amarillo.
- Se queman solo en la **mitad inferior** (el clip), con la libreria `libass`
  incluida en el FFmpeg de `imageio-ffmpeg`.

Ajustes en `.env`:

| Variable | Descripcion |
| --- | --- |
| `SUBTITLE_ENABLED` | `true` / `false` |
| `SUBTITLE_FONT` | Fuente (por defecto `Arial`) |
| `SUBTITLE_FONTSIZE` | Tamano |
| `SUBTITLE_OUTLINE` | Grosor del contorno |
| `SUBTITLE_MARGIN_V` | Margen inferior |
| `SUBTITLE_MAX_WORDS` | Palabras por grupo |
| `SUBTITLE_MAX_GAP` / `SUBTITLE_MAX_DURATION` | Corte de grupos |

## Mejora de rostro del avatar

- Se aplica **CodeFormer** (`sczhou/CodeFormer`, gratis) a la imagen del avatar
  antes de animarla: rostro mas nitido y realista + upscale 2x.
- Se guarda un respaldo en `assets/avatar/avatar_original.jpg`.

| Variable | Descripcion |
| --- | --- |
| `ENHANCE_ENABLED` | `true` / `false` |
| `ENHANCE_SPACE` | Space a usar (`sczhou/CodeFormer`) |
| `ENHANCE_FIDELITY` | 0 = mas realista, 1 = mas fiel al original |

## Fase 3 - Publicacion con Playwright

Pendiente. Plan:

1. `pip install playwright && playwright install chromium`
2. Guardar la sesion iniciada de TikTok y Facebook una vez
   (`playwright codegen` -> estado `storage_state.json`).
3. `pipeline/publish.py` automatiza:
   - TikTok: subir a `tiktok.com/upload` o TikTok Studio, escribir caption, publicar.
   - Facebook: Page -> Reels -> subir video -> publicar.
4. Publicar max **2-3 reels/dia** por red para evitar marcas de spam.

## Estructura

```
clip-studio/
  cli.py                 # entrada principal
  .env                   # claves y ajustes
  pipeline/
    config.py            # settings
    download.py          # yt-dlp / archivo local
    transcribe.py        # faster-whisper
    select_clips.py      # LLM opencode-go
    avatar.py            # generacion del avatar (Pollinations)
    montage.py           # FFmpeg split-screen
    ffmpeg.py            # localiza el binario de FFmpeg
    publish.py           # Fase 3 (Playwright)
  assets/avatar/         # avatar.jpg + avatar_loop.mp4
  work/                  # temporales (source, clips, transcript)
  output/                # reels finales
```
