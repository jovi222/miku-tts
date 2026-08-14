"""
Kokoro-TTS API Server untuk Miku Virtual Assistant
Dijalankan di Hugging Face Spaces - 100% Gratis!
Suara: Gadis remaja Indonesia yang natural & ekspresif
"""

import io
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf

# ── Inisialisasi Kokoro ──────────────────────────────────────────────────
from kokoro import KPipeline

app = FastAPI(title="Miku TTS API", description="Kokoro Neural TTS untuk Miku Virtual Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pipeline sekali saja saat startup (hemat memori)
# 'a' = American English base (paling kompatibel untuk multilingual)
print("⏳ Memuat model Kokoro... tunggu sebentar~")
pipeline = KPipeline(lang_code='a')
print("✅ Model Kokoro siap!")

# ── Suara yang tersedia ──────────────────────────────────────────────────
# af_bella  = gadis ceria, energetik (paling loli)
# af_sarah  = gadis santai, natural
# af_sky    = gadis lembut, kalem
VOICES = {
    "bella":  "af_bella",   # default - suara loli paling bagus
    "sarah":  "af_sarah",
    "sky":    "af_sky",
    "nicole": "af_nicole",
}

@app.get("/tts", summary="Text-to-Speech")
async def tts(
    text:  str = Query(..., description="Teks yang akan diucapkan"),
    voice: str = Query("bella", description="Nama suara: bella, sarah, sky, nicole"),
    speed: float = Query(1.1, ge=0.5, le=2.0, description="Kecepatan bicara (1.0 = normal)"),
):
    """
    Menghasilkan audio MP3 dari teks menggunakan Kokoro Neural TTS.
    Suara default 'bella' terdengar seperti gadis remaja yang ceria dan natural.
    """
    if not text or not text.strip():
        return JSONResponse({"error": "Teks tidak boleh kosong"}, status_code=400)

    # Batasi panjang teks
    text = text.strip()[:400]

    voice_id = VOICES.get(voice.lower(), "af_bella")

    try:
        # Generate audio
        generator = pipeline(text, voice=voice_id, speed=speed, split_pattern=r'\n+')

        all_audio = []
        for _, _, audio in generator:
            if audio is not None:
                all_audio.append(audio)

        if not all_audio:
            return JSONResponse({"error": "Gagal generate audio"}, status_code=500)

        # Gabungkan semua chunk audio
        combined = np.concatenate(all_audio)

        # Konversi ke MP3 via buffer
        buf = io.BytesIO()
        sf.write(buf, combined, 24000, format='WAV')
        buf.seek(0)

        return Response(
            content=buf.read(),
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-cache",
                "X-Voice": voice_id,
            }
        )

    except Exception as e:
        print(f"Error TTS: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/voices", summary="Daftar suara tersedia")
async def list_voices():
    return {
        "voices": [
            {"id": "bella",  "description": "Gadis ceria & energetik - paling anime/loli"},
            {"id": "sarah",  "description": "Gadis santai & natural"},
            {"id": "sky",    "description": "Gadis lembut & kalem"},
            {"id": "nicole", "description": "Gadis hangat & ekspresif"},
        ],
        "default": "bella"
    }


@app.get("/health")
async def health():
    return {"status": "ok", "model": "kokoro-v1.0", "ready": True}


@app.get("/")
async def root():
    return {
        "name": "Miku TTS API",
        "description": "Kokoro Neural TTS untuk Miku Virtual Assistant",
        "endpoints": {
            "/tts?text=Halo Vi~&voice=bella": "Generate audio",
            "/voices": "Daftar suara",
            "/health": "Cek status server"
        }
    }
