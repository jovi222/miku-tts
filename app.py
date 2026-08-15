"""
Kokoro TTS API — Loli Voice Engine
Menggunakan WORLD Vocoder (pyworld) untuk transformasi suara profesional:
  1. Pitch shift +7 semitone (suara lebih tinggi)
  2. Formant shift ×1.25 (vocal tract lebih kecil = lebih muda/anime)
  3. Voice: jf_nezumi (karakter muda & ceria)
"""

import io
import numpy as np
import scipy.signal
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf

app = FastAPI(title="Miku Loli TTS")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pipelines = {}

def get_pipeline(lang_code: str):
    if lang_code not in _pipelines:
        from kokoro import KPipeline
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
        print(f"✅ Pipeline '{lang_code}' siap!")
    return _pipelines[lang_code]


def loli_voice_transform(samples: np.ndarray, sample_rate: int,
                          pitch_semitones: float = 7.0,
                          formant_ratio: float = 1.25) -> np.ndarray:
    """
    Transformasi suara ke efek loli/anime:
    - pitch_semitones: naikkan pitch (+7 = sangat loli)
    - formant_ratio > 1: perkecil vocal tract (suara lebih kecil & muda)
    """
    try:
        import pyworld as pw

        samples_f64 = samples.astype(np.float64)
        sr = float(sample_rate)

        # Ekstrak fitur suara dengan WORLD vocoder
        f0, sp, ap = pw.wav2world(samples_f64, sr)

        # 1. Pitch shift — naikkan frekuensi dasar
        pitch_factor = 2.0 ** (pitch_semitones / 12.0)
        f0_shifted = np.where(f0 > 0, f0 * pitch_factor, 0.0)

        # 2. Formant shift — warp spektral envelope
        #    Simulates smaller vocal tract → suara lebih kecil & muda
        freq_bins = sp.shape[1]
        sp_shifted = np.zeros_like(sp)
        x_orig = np.arange(freq_bins)
        x_src  = x_orig / formant_ratio
        for i in range(sp.shape[0]):
            sp_shifted[i] = np.interp(x_orig, x_src, sp[i],
                                      left=sp[i, 0], right=sp[i, -1])

        # Sintesis ulang dengan fitur yang sudah dimodifikasi
        y = pw.synthesize(f0_shifted, sp_shifted, ap, sr)
        return y.astype(np.float32)

    except ImportError:
        # Fallback: simple pitch shift dengan scipy jika pyworld tidak tersedia
        factor   = 2.0 ** (pitch_semitones / 12.0)
        n_out    = int(np.round(len(samples) / factor))
        pitched  = scipy.signal.resample(samples, n_out)
        restored = scipy.signal.resample(pitched, len(samples))
        return restored.astype(np.float32)


VOICES = {
    # Japanese Female — loli/anime
    "nezumi":    ("j", "jf_nezumi"),      # paling muda & ceria ← default
    "alpha":     ("j", "jf_alpha"),
    "gongitsune":("j", "jf_gongitsune"),
    "tebukuro":  ("j", "jf_tebukuro"),
    # English Female — fallback
    "bella":     ("a", "af_bella"),
    "sky":       ("a", "af_sky"),
}


@app.get("/tts")
async def tts(
    text:     str   = Query(...),
    voice:    str   = Query("nezumi"),      # jf_nezumi default
    speed:    float = Query(1.1,  ge=0.5, le=2.0),
    pitch:    float = Query(7.0,  ge=0.0, le=12.0),   # semitones
    formant:  float = Query(1.25, ge=1.0, le=2.0),    # vocal tract size
):
    if not text or not text.strip():
        return JSONResponse({"error": "Teks kosong"}, status_code=400)

    text = text.strip()[:400]
    lang_code, voice_id = VOICES.get(voice.lower(), ("j", "jf_nezumi"))

    try:
        pipeline  = get_pipeline(lang_code)
        all_audio = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=speed):
            if audio is not None:
                all_audio.append(audio)

        if not all_audio:
            return JSONResponse({"error": "Gagal generate audio"}, status_code=500)

        combined = np.concatenate(all_audio)

        # ── Transformasi suara loli ──────────────────────────────────────
        if pitch > 0 or formant > 1.0:
            combined = loli_voice_transform(combined, 24000,
                                            pitch_semitones=pitch,
                                            formant_ratio=formant)

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
    return {"name": "Miku Loli TTS", "engine": "Kokoro + WORLD Vocoder",
            "voice": "jf_nezumi", "pitch": "+7 semitone", "formant": "×1.25"}
