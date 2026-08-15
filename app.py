"""
Kokoro TTS API — Loli Voice Engine v3
- Voice: af_sky (paling ringan & anime-like) blend af_kore (energetik)
- Pitch shift: pyrubberband (formant-preserved = tidak chipmunk)
- Fallback: scipy jika rubberband tidak ada
"""

import io
import numpy as np
import scipy.signal
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf

app = FastAPI(title="Miku Loli TTS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy loading ──────────────────────────────────────────────────────────────
_pipeline_a = None   # American English
_pipeline_j = None   # Japanese

def get_pipeline(lang: str = 'a'):
    global _pipeline_a, _pipeline_j
    if lang == 'j':
        if _pipeline_j is None:
            from kokoro import KPipeline
            _pipeline_j = KPipeline(lang_code='j')
            print("✅ Pipeline JP siap!")
        return _pipeline_j
    else:
        if _pipeline_a is None:
            from kokoro import KPipeline
            _pipeline_a = KPipeline(lang_code='a')
            print("✅ Pipeline EN siap!")
        return _pipeline_a


# ── Pitch Shift ───────────────────────────────────────────────────────────────
def shift_pitch(samples: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    """
    Formant-preserved pitch shift pakai pyrubberband.
    Jika tidak tersedia, fallback ke scipy (ada chipmunk ringan).
    """
    if semitones == 0:
        return samples
    try:
        import pyrubberband as pyrb
        # R3 engine dengan formant preservation → tidak chipmunk
        shifted = pyrb.pitch_shift(
            samples.astype(np.float64), sr, n_steps=semitones,
            rbargs={"--formant": ""}
        )
        return shifted.astype(np.float32)
    except Exception:
        # Fallback scipy
        factor   = 2.0 ** (semitones / 12.0)
        n_short  = int(round(len(samples) / factor))
        pitched  = scipy.signal.resample(samples, n_short)
        restored = scipy.signal.resample(pitched, len(samples))
        return restored.astype(np.float32)


# ── Voice map ─────────────────────────────────────────────────────────────────
VOICES = {
    # Paling anime-like English
    "sky":    ("a", "af_sky"),           # paling ringan & airy
    "kore":   ("a", "af_kore"),          # bright & energetik
    "nova":   ("a", "af_nova"),          # modern & upbeat
    "nicole": ("a", "af_nicole"),        # breathy & ASMR
    "bella":  ("a", "af_bella"),         # energetik
    "heart":  ("a", "af_heart"),         # warm & natural
    # Japanese anime narrator
    "gongitsune": ("j", "jf_gongitsune"),  # theatrical, anime-narrator
    "tebukuro":   ("j", "jf_tebukuro"),   # ekspresif, storytelling
    "alpha":      ("j", "jf_alpha"),       # general JP female
}


@app.get("/tts")
async def tts(
    text:     str   = Query(...),
    voice:    str   = Query("sky"),
    speed:    float = Query(1.15, ge=0.5, le=2.0),
    pitch:    float = Query(5.0,  ge=0.0, le=12.0),
):
    if not text or not text.strip():
        return JSONResponse({"error": "Teks kosong"}, status_code=400)

    text = text.strip()[:400]
    lang, voice_id = VOICES.get(voice.lower(), ("a", "af_sky"))

    try:
        pipeline  = get_pipeline(lang)
        all_audio = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=speed):
            if audio is not None:
                all_audio.append(audio)

        if not all_audio:
            return JSONResponse({"error": "Gagal generate audio"}, status_code=500)

        combined = np.concatenate(all_audio)

        # Pitch shift dengan formant preservation
        combined = shift_pitch(combined, 24000, pitch)

        buf = io.BytesIO()
        sf.write(buf, combined, 24000, format="WAV")
        buf.seek(0)

        return Response(
            content=buf.read(),
            media_type="audio/wav",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        print(f"Error TTS: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/voices")
async def list_voices():
    return {
        "recommended": "sky",
        "voices": [
            {"id": "sky",        "lang": "en", "desc": "Paling ringan & anime ⭐"},
            {"id": "kore",       "lang": "en", "desc": "Bright & energetik"},
            {"id": "nova",       "lang": "en", "desc": "Modern & upbeat"},
            {"id": "nicole",     "lang": "en", "desc": "Breathy & ASMR"},
            {"id": "gongitsune", "lang": "ja", "desc": "Anime narrator JP"},
            {"id": "tebukuro",   "lang": "ja", "desc": "Ekspresif JP"},
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "ready": True}

@app.get("/")
async def root():
    return {"name": "Miku Loli TTS v3", "best_voice": "af_sky", "pitch": "+5 semitone (formant-preserved)"}
