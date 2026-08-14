---
title: Miku TTS API
emoji: 🎙️
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: Kokoro Neural TTS API untuk Miku Virtual Assistant
---

# 🎙️ Miku TTS API

Server Text-to-Speech gratis menggunakan **Kokoro Neural TTS** untuk proyek Miku Virtual Assistant.

## Endpoints

| Endpoint | Keterangan |
|---|---|
| `GET /tts?text=Halo~&voice=bella` | Generate audio |
| `GET /voices` | Daftar suara tersedia |
| `GET /health` | Status server |

## Suara Tersedia

| Voice ID | Karakter |
|---|---|
| `bella` | Gadis ceria & energetik (default, paling anime) |
| `sarah` | Gadis santai & natural |
| `sky` | Gadis lembut & kalem |
| `nicole` | Gadis hangat & ekspresif |

## Contoh Penggunaan

```javascript
const res  = await fetch('https://USERNAME-miku-tts.hf.space/tts?text=Halo+Vi~&voice=bella');
const blob = await res.blob();
const audio = new Audio(URL.createObjectURL(blob));
audio.play();
```
