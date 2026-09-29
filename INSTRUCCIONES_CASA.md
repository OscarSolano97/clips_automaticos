# INSTRUCCIONES — Instalar clip-studio en la PC de casa

Guia paso a paso para dejar el proyecto funcionando en una PC nueva.
Todos los comandos se escriben en una **terminal de Windows** y se ejecuta
cada uno con **Enter** (uno a la vez, esperando a que termine).

---

## PARTE 0 — Cosas a tener antes

1. **Python 3.11 o superior** instalado.
   - Verificar: abrir terminal y escribir `python --version`
   - Si no lo tenes: descargar de https://www.python.org/downloads/
     e instalar marcando la casilla **"Add Python to PATH"**.

2. **Git** instalado.
   - Verificar: `git --version`
   - Si no lo tenes: descargar de https://git-scm.com/download/win

3. Tus claves a mano (te las podes pasar desde la otra PC):
   - `OPENCODE_API_KEY`
   - `HF_TOKEN` (opcional)

---

## PARTE 1 — Abrir la terminal

Podes usar **CMD (Simbolo del sistema)** o **PowerShell**.

- **Opcion facil:** clic derecho sobre la carpeta del proyecto -> "Abrir en Terminal"
  (o "Open in Terminal").
- **O manual:** abrir "Simbolo del sistema" desde el menu Inicio y luego navegar
  a la carpeta con `cd`.

> Los comandos `.venv\Scripts\activate` de mas abajo funcionan en **CMD**.
> Si usas **PowerShell**, usa `.venv\Scripts\Activate.ps1` en su lugar.

---

## PARTE 2 — Descargar el proyecto (clonar)

Si todavia NO tenes la carpeta del proyecto en esta PC:

```
git clone https://github.com/TU_USUARIO/clip-studio.git
```

Luego entras a la carpeta:

```
cd clip-studio
```

(Si ya te pasaste la carpeta por USB, solo hace falta el `cd clip-studio`.)

---

## PARTE 3 — Los 3 comandos de instalacion

Ejecutar **en orden**, uno por uno:

**Comando 1** — crear el entorno virtual (una sola vez):

```
python -m venv .venv
```

**Comando 2** — activar el entorno virtual:

```
.venv\Scripts\activate
```
> Sabras que funciono porque al inicio de la linea aparece `(.venv)`.

**Comando 3** — instalar las librerias:

```
pip install -r requirements.txt
```
> Tarda unos minutos. Es normal.

---

## PARTE 4 — Configurar las claves (.env)

El archivo `.env` NO viene en Git (por seguridad). Crearlo desde la plantilla:

```
copy .env.example .env
```

Luego **abrir `.env` con el Bloc de notas** y completar:

| Variable             | Que poner                                        |
| -------------------- | ------------------------------------------------ |
| `OPENCODE_API_KEY`   | tu API key de opencode-go                        |
| `HF_TOKEN`           | tu token de Hugging Face (opcional)              |
| `HF_SSL_VERIFY`      | **`true`**  (en casa la red es normal)           |

> `HF_SSL_VERIFY=true` porque en casa NO hay proxy MITM. Si por algo fallara,
> se puede dejar en `false` y funciona igual.

---

## PARTE 5 — Preparar el avatar

El avatar (imagen + video) NO viene en Git. Tenes 2 opciones:

- **Opción A — Generarlo de nuevo** (necesita internet):
  ```
  python cli.py avatar
  ```

- **Opción B — Copiarlo** desde la otra PC:
  copiar manualmente estos archivos a `assets/avatar/`:
  - `avatar.jpg`
  - `avatar_loop.mp4`

---

## PARTE 6 — Probar que todo funciona

```
python cli.py auto --niche curiosidades -v 1
```

- La **primera vez** descarga el modelo Whisper (~150 MB). Es normal que tarde.
- Los reels finales quedan en la carpeta `output/`.
- La info de publicacion (caption + hashtags) en `output/publish_manifest.json`.

---

## Resumen rapido (los comandos en orden)

```
git clone https://github.com/TU_USUARIO/clip-studio.git
cd clip-studio
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
(editar .env -> poner OPENCODE_API_KEY, HF_TOKEN, HF_SSL_VERIFY=true)
python cli.py avatar
python cli.py auto --niche curiosidades -v 1
```

---

## Problemas comunes

| Sintoma | Solucion |
| ------- | -------- |
| `python no se reconoce como comando` | Reinstalar Python marcando "Add to PATH" |
| `activate no se reconoce` (en PowerShell) | Usar `.venv\Scripts\Activate.ps1` |
| Error de SSL en casa | Revisar que `HF_SSL_VERIFY=true` en `.env` |
| No encuentra ffmpeg | No hace falta instalarlo: viene con `imageio-ffmpeg` |
| Quota agotada en Hugging Face | Configurar `HF_TOKEN` en `.env` |
