"""Transcribe short WAV recordings with a local Whisper model."""

from __future__ import annotations

import io
import os
import threading
import wave

import numpy as np
import requests
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000
MAX_DURATION_SECONDS = 60
MODEL_SIZE = "small"


class VoiceEngine:
    def __init__(self) -> None:
        self._model: WhisperModel | None = None
        self._model_lock = threading.Lock()
        self._transcription_lock = threading.Lock()

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._model = WhisperModel(
                        MODEL_SIZE,
                        device="cpu",
                        compute_type="int8",
                        cpu_threads=min(4, os.cpu_count() or 1),
                    )
        return self._model

    def _decode_wav(self, audio: bytes) -> np.ndarray:
        try:
            with wave.open(io.BytesIO(audio), "rb") as wav:
                if (
                    wav.getnchannels() != 1
                    or wav.getsampwidth() != 2
                    or wav.getframerate() != SAMPLE_RATE
                ):
                    raise ValueError("Audio must be mono, 16-bit, 16 kHz WAV.")
                if wav.getnframes() == 0:
                    raise ValueError("The recording is empty.")
                if wav.getnframes() > SAMPLE_RATE * MAX_DURATION_SECONDS:
                    raise ValueError("Recordings must be 60 seconds or shorter.")
                samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
        except (wave.Error, EOFError, OSError) as exc:
            raise ValueError("The recording is not a valid WAV file.") from exc
        return samples.astype(np.float32) / 32768.0

    def transcribe(self, audio: bytes) -> str:
        samples = self._decode_wav(audio)
        try:
            with self._transcription_lock:
                model = self._get_model()
                segments, _ = model.transcribe(
                    samples,
                    beam_size=5,
                    vad_filter=True,
                    condition_on_previous_text=False,
                )
                return " ".join(segment.text.strip() for segment in segments).strip()
        except (OSError, RuntimeError, requests.exceptions.RequestException) as exc:
            raise RuntimeError(f"Local Whisper transcription failed: {exc}") from exc


voice_engine = VoiceEngine()
