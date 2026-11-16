import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import wave

import numpy as np

from core.voice_engine import MAX_DURATION_SECONDS, SAMPLE_RATE, VoiceEngine


def make_wav(channels=1, sample_width=2, sample_rate=SAMPLE_RATE, frames=4):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\0" * frames * channels * sample_width)
    return buffer.getvalue()


class VoiceEngineTests(unittest.TestCase):
    def test_rejects_audio_with_unsupported_format(self):
        engine = VoiceEngine()

        with self.assertRaisesRegex(ValueError, "mono, 16-bit, 16 kHz"):
            engine._decode_wav(make_wav(channels=2))

    def test_rejects_recordings_over_sixty_seconds(self):
        engine = VoiceEngine()
        audio = make_wav(frames=SAMPLE_RATE * MAX_DURATION_SECONDS + 1)

        with self.assertRaisesRegex(ValueError, "60 seconds or shorter"):
            engine._decode_wav(audio)

    def test_transcribes_in_memory_float_audio(self):
        model = Mock()
        model.transcribe.return_value = (
            iter([
                SimpleNamespace(text=" Open system"),
                SimpleNamespace(text=" settings "),
            ]),
            SimpleNamespace(language="en"),
        )
        engine = VoiceEngine()

        with patch.object(engine, "_get_model", return_value=model):
            transcript = engine.transcribe(make_wav())

        self.assertEqual(transcript, "Open system settings")
        model.transcribe.assert_called_once()
        samples = model.transcribe.call_args.args[0]
        self.assertIsInstance(samples, np.ndarray)
        self.assertEqual(samples.dtype, np.float32)
        self.assertEqual(samples.size, 4)

    @patch("core.voice_engine.WhisperModel")
    def test_loads_and_caches_local_model(self, whisper_model):
        engine = VoiceEngine()

        model = engine._get_model()
        self.assertIs(engine._get_model(), model)

        whisper_model.assert_called_once()
        self.assertEqual(whisper_model.call_args.args[0], "small")
        self.assertEqual(whisper_model.call_args.kwargs["device"], "cpu")
        self.assertEqual(whisper_model.call_args.kwargs["compute_type"], "int8")

    def test_surfaces_model_errors_for_in_memory_audio(self):
        model = Mock()
        model.transcribe.side_effect = RuntimeError("model unavailable")
        engine = VoiceEngine()

        with self.assertRaisesRegex(RuntimeError, "Local Whisper transcription failed"):
            with patch.object(engine, "_get_model", return_value=model):
                engine.transcribe(make_wav())

        samples = model.transcribe.call_args.args[0]
        self.assertIsInstance(samples, np.ndarray)


if __name__ == "__main__":
    unittest.main()
