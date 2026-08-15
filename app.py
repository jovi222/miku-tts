"""
Kokoro TTS API - Support English + Japanese Female voices
Japanese voices lebih cocok untuk anime/loli style
"""

import io
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf

app = FastAPI(title="Miku TTS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Lazy load pipelines — dimuat saat request pertama
_pipelines = {}

def get_pipeline(lang_code: str):
    if lang_code not in _pipelines:
        print(f"⏳ Memuat pipeline Kokoro lang={lang_code}...")
        from kokoro import KPipeline
        _pipelines[lang_code] = KPipeline(lang_code=lang_code)
        print(f"✅ Pipeline '{lang_code}' siap!")
    return _pipelines[lang_code]

# Daftar suara: prefix menentukan lang_code
VOICES = {
    # Japanese Female — lebih anime/loli, fonetik mirip Indonesia
    "alpha":     ("j", "jf_alpha"),
    "gongitsune":("j", "jf_gongitsune"),
    "nezumi":    ("j", "jf_nezumi"),
    "tebukuro":  ("j", "jf_tebukuro"),
    # American Female — fallback
    "bella":     ("a", "af_bella"),
    "sarah":     ("a", "af_sarah"),
    "sky":       ("a", "af_sky"),
}

@app.get("/tts")
async def tts(
    text:  str   = Query(...),
    voice: str   = Query("alpha"),   # default: Japanese female
    speed: float = Query(1.15, ge=0.5, le=2.0),
):
    if not text or not text.strip():
        return JSONResponse({"error": "Teks kosong"}, status_code=400)

    text = text.strip()[:400]
    voice_info = VOICES.get(voice.lower(), ("j", "jf_alpha"))
    lang_code, voice_id = voice_info

    try:
        pipeline = get_pipeline(lang_code)
        all_audio = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=speed):
            if audio is not None:
                all_audio.append(audio)

        if not all_audio:
            return JSONResponse({"error": "Gagal generate audio"}, status_code=500)

        combined = np.concatenate(all_audio)
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
        "voices": [
            {"id": "alpha",      "type": "Japanese Female", "desc": "Anime natural — RECOMMENDED"},
            {"id": "gongitsune", "type": "Japanese Female", "desc": "Lembut & ekspresif"},
            {"id": "nezumi",     "type": "Japanese Female", "desc": "Ceria & muda"},
            {"id": "tebukuro",   "type": "Japanese Female", "desc": "Kalem & manis"},
            {"id": "bella",      "type": "American Female", "desc": "Energetik (English)"},
        ],
        "default": "alpha"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "ready": True}

@app.get("/")
async def root():
    return {"name": "Miku TTS API", "engine": "Kokoro", "default_voice": "jf_alpha"}
