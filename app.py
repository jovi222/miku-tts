import io
import numpy as np
from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import soundfile as sf

app = FastAPI(title="Miku TTS API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from kokoro import KPipeline
        _pipeline = KPipeline(lang_code='a')
    return _pipeline

VOICES = {"bella": "af_bella", "sarah": "af_sarah", "sky": "af_sky", "nicole": "af_nicole"}

@app.get("/tts")
async def tts(text: str = Query(...), voice: str = Query("bella"), speed: float = Query(1.1)):
    if not text.strip():
        return JSONResponse({"error": "Teks kosong"}, status_code=400)
    text = text.strip()[:400]
    voice_id = VOICES.get(voice.lower(), "af_bella")
    try:
        pipeline = get_pipeline()
        all_audio = []
        for _, _, audio in pipeline(text, voice=voice_id, speed=speed):
            if audio is not None:
                all_audio.append(audio)
        combined = np.concatenate(all_audio)
        buf = io.BytesIO()
        sf.write(buf, combined, 24000, format="WAV")
        buf.seek(0)
        return Response(content=buf.read(), media_type="audio/wav", headers={"Cache-Control": "no-cache"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"name": "Miku TTS API", "status": "online"}
