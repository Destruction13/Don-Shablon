import tempfile
import difflib
import logging

import sounddevice as sd
import soundfile as sf
from PySide6.QtWidgets import QApplication
from faster_whisper import WhisperModel

from constants import rooms_by_bz


class WhisperRecognizer:
    """Simple wrapper around faster-whisper for offline speech recognition."""

    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self.model: WhisperModel | None = None

    def _load_model(self) -> WhisperModel:
        if self.model is None:
            logging.debug("[Whisper] Loading model %s", self.model_size)
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self.model

    def recognize(self, duration: float = 4.0, language: str = "ru") -> str:
        """Record audio from the microphone and return recognized text."""
        fs = 16_000
        QApplication.beep()
        logging.debug("[Whisper] Recording %s seconds", duration)
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sd.wait()
        QApplication.beep()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, fs)
            path = tmp.name
        model = self._load_model()
        segments, _ = model.transcribe(path, language=language)
        text = "".join(seg.text for seg in segments).strip()
        logging.debug("[Whisper] Result: %s", text)
        return text


def match_room(text: str, cutoff: float = 0.6) -> tuple[str, str] | tuple[None, None]:
    """Return the closest room name and its business center."""
    mapping: dict[str, str] = {}
    for bz, rooms in rooms_by_bz.items():
        for r in rooms:
            mapping[r] = bz
    rooms = list(mapping.keys())
    matches = difflib.get_close_matches(text, rooms, n=1, cutoff=cutoff)
    if not matches:
        return None, None
    room = matches[0]
    return room, mapping.get(room)
