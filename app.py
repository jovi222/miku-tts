"""
Kokoro TTS API + Pitch Shifting
Pitch dinaikkan otomatis agar terdengar seperti suara loli/anime
"""

import io
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf
import scipy.signal

app = FastAPI(title="Miku TTS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pipelines = {}

def get_pipeline(lang_code: str):
    if lang_code not in _pipelines:
        print(f"⏳ Memuat Kokoro lang={lang_code}...")
        from kokoro import KPipeline
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
        print(f"✅ Pipeline '{lang_code}' siap!")
    return _pipelines[lang_code]


def pitch_shift(samples: np.ndarray, sample_rate: int, semitones: float) -> np.ndarray:
    """
    Naikkan pitch suara tanpa mengubah durasi.
    semitones > 0 = lebih tinggi (lebih loli)
    semitones = 4 → terdengar jauh lebih muda & anime
    """
    factor = 2 ** (semitones / 12.0)
    # Resample ke panjang lebih pendek (pitch naik), lalu stretch kembali ke panjang asli
    original_len  = len(samples)
    resampled_len = int(np.round(original_len / factor))
    # Naikan pitch dengan resample
    pitched = scipy.signal.resample(samples, resampled_len)
    # Kembalikan ke durasi asli dengan resample lagi
    restored = scipy.signal.resample(pitched, original_len)
    return restored.astype(np.float32)


VOICES = {
    "alpha":     ("j", "jf_alpha"),
    "gongitsune":("j", "jf_gongitsune"),
    "nezumi":    ("j", "jf_nezumi"),
    "tebukuro":  ("j", "jf_tebukuro"),
    "bella":     ("a", "af_bella"),
    "sarah":     ("a", "af_sarah"),
    "sky":       ("a", "af_sky"),
}

@app.get("/tts")
async def tts(
    text:     str   = Query(...),
    voice:    str   = Query("alpha"),
    speed:    float = Query(1.1,  ge=0.5, le=2.0),
    semitones:float = Query(4.0,  ge=0.0, le=12.0),  # default +4 semitone = suara loli
):
    if not text or not text.strip():
        return JSONResponse({"error": "Teks kosong"}, status_code=400)

    text = text.strip()[:400]
    lang_code, voice_id = VOICES.get(voice.lower(), ("j", "jf_alpha"))

    try:
        pipeline  = get_pipeline(lang_code)
        all_audio = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=speed):
            if audio is not None:
                all_audio.append(audio)

        if not all_audio:
            return JSONResponse({"error": "Gagal generate audio"}, status_code=500)

        combined = np.concatenate(all_audio)

        # ── Pitch shifting: naikkan nada agar terdengar lebih loli ──
        if semitones > 0:
            combined = pitch_shift(combined, 24000, semitones)

        buf = io.BytesIO()
        sf.write(buf, combined, 24000, format="WAV")
        buf.seek(0)

        return Response(
            content=buf.read(),
            media_type="audio/wav",
            headers={"Cache-Control": "no-cache"},
        )
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"name": "Miku TTS + Loli Pitch", "semitones_default": 4}
