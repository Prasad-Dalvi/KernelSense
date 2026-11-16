import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.log_engine import LogEngine


class LogEngineTests(unittest.TestCase):
    @patch(
        "core.log_engine.ml_engine.predict_log",
        return_value={"category": "NORMAL_INFO", "confidence": 0.97},
    )
    @patch("core.log_engine.subprocess.run")
    def test_returns_and_caches_actual_event_records(self, run, _predict_log):
        run.return_value = SimpleNamespace(
            returncode=0,
            stdout=json.dumps([
                {
                    "id": "System-12",
                    "timestamp": "2025-01-02T03:04:05.0000000-08:00",
                    "service": "Service Control Manager",
                    "message": "A real event message.",
                    "level": "Error",
                    "level_number": 2,
                    "pid": 42,
                }
            ]),
            stderr="",
        )
        engine = LogEngine()

        events = engine.get_logs()
        again = engine.get_logs()

        self.assertEqual(events[0]["id"], "System-12")
        self.assertEqual(events[0]["message"], "A real event message.")
        self.assertEqual(events[0]["severity"], "critical")
        self.assertEqual(again, events)
        run.assert_called_once()

    @patch("core.log_engine.subprocess.run")
    def test_event_log_read_failure_is_not_replaced_with_sample_data(self, run):
        run.return_value = SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Access is denied.",
        )
        engine = LogEngine()

        with self.assertRaisesRegex(RuntimeError, "Access is denied"):
            engine.get_logs()

        self.assertEqual(engine.cached_logs, [])


if __name__ == "__main__":
    unittest.main()
