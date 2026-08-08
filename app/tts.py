"""Text-to-Speech module — dual-engine (edge-tts + pyttsx3) with voice selection.

edge-tts: Microsoft neural voices (online), default engine, high quality.
pyttsx3:  System SAPI voices (offline), fallback.
"""

import subprocess
import threading
import asyncio
import tempfile
import os


# ── engine / voice discovery ────────────────────────────────────

def list_engines() -> list[dict]:
    """Return available engines and their voices.

    Returns:
        [{name: "edge", label: "Edge TTS (Online)", voices: [{id, name, locale}]},
         {name: "pyttsx3", label: "System TTS (Offline)", voices: [{id, name}]}]
    """
    engines = [_edge_engine_info(), _pyttsx3_engine_info()]
    return [e for e in engines if e is not None]


def _edge_engine_info() -> dict | None:
    """Check if edge-tts is available and return its voices."""
    try:
        import edge_tts
        voices = asyncio.run(edge_tts.list_voices())
        # Filter for Chinese + English voices, deduplicate short names
        seen = set()
        result = []
        for v in voices:
            if v["Locale"].startswith(("zh-", "en-")):
                if v["ShortName"] not in seen:
                    seen.add(v["ShortName"])
                    result.append({
                        "id": v["ShortName"],
                        "name": v.get("FriendlyName", v["ShortName"]),
                        "locale": v["Locale"],
                    })
        return {
            "name": "edge",
            "label": "Edge TTS (Online)",
            "voices": result,
        }
    except (ImportError, Exception):
        return None


def _pyttsx3_engine_info() -> dict | None:
    """Check if pyttsx3 is available and return its voices."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.stop()  # clean up
        result = []
        for v in voices:
            result.append({
                "id": v.id,
                "name": v.name,
            })
        return {
            "name": "pyttsx3",
            "label": "System TTS (Offline)",
            "voices": result,
        }
    except (ImportError, Exception):
        return None


# ── speak (non-blocking) ────────────────────────────────────────

def speak(text: str, engine: str = "edge", voice: str = "", volume: int = 100):
    """Speak text in a background daemon thread. Returns immediately."""
    t = threading.Thread(target=_speak_sync, args=(text, engine, voice, volume),
                         daemon=True, name="tts-speak")
    t.start()


def _speak_sync(text: str, engine: str, voice: str, volume: int):
    """Blocking TTS call — runs in a daemon thread."""
    if engine == "edge":
        _speak_edge(text, voice, volume)
    elif engine == "pyttsx3":
        _speak_pyttsx3(text, voice, volume)


# ── edge-tts backend ────────────────────────────────────────────

def _speak_edge(text: str, voice: str, volume: int):
    """Use edge-tts CLI (edge-playback) — simplest reliable approach."""
    try:
        # Build command
        cmd = ["edge-playback", "--text", text]
        if voice:
            cmd += ["--voice", voice]
        # edge-playback handles synthesis + playback in one shot
        subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except FileNotFoundError:
        # edge-playback not in PATH, try Python API with temp file
        try:
            _speak_edge_via_api(text, voice, volume)
        except Exception:
            pass
    except Exception:
        pass


def _speak_edge_via_api(text: str, voice: str, volume: int):
    """Fallback: use edge_tts Python API + temp WAV + system player."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice or "zh-CN-XiaoxiaoNeural")
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        asyncio.run(communicate.save(tmp.name))
        # Play with system default player
        if os.name == "nt":
            subprocess.run(
                ["powershell", "-c",
                 f'(New-Object Media.SoundPlayer "{tmp.name}").PlaySync()'],
                capture_output=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            subprocess.run(["afplay", tmp.name], capture_output=True, timeout=30)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── pyttsx3 backend ─────────────────────────────────────────────

def _speak_pyttsx3(text: str, voice: str, volume: int):
    """Use pyttsx3 (offline SAPI) in this thread."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        if voice:
            engine.setProperty("voice", voice)
        if volume != 100:
            engine.setProperty("volume", max(0.0, min(1.0, volume / 100.0)))
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass
