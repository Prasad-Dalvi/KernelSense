import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.live_telemetry import TelemetryCollector


class LiveTelemetryTests(unittest.TestCase):
    def test_storage_is_unavailable_when_no_volume_is_measurable(self):
        collector = TelemetryCollector()
        with patch("core.live_telemetry.psutil.disk_partitions", return_value=[]):
            storage = collector.get_storage_stats()

        self.assertIsNone(storage["usage_percent"])
        self.assertIsNone(storage["total_gb"])
        self.assertEqual(storage["partitions"], [])
        self.assertNotIn("largest_dirs", storage)

    def test_unavailable_load_average_is_not_estimated(self):
        collector = TelemetryCollector()
        with patch(
            "core.live_telemetry.os.getloadavg",
            create=True,
            side_effect=AttributeError,
        ):
            cpu = collector.get_cpu_stats()

        self.assertIsNone(cpu["load_avg"])

    def test_health_score_excludes_unavailable_storage(self):
        collector = TelemetryCollector()
        with (
            patch.object(collector, "get_cpu_stats", return_value={"cpu_usage": 20}),
            patch.object(collector, "get_memory_stats", return_value={
                "memory_percent": 30,
                "free_gb": 4,
            }),
            patch.object(collector, "get_storage_stats", return_value={
                "usage_percent": None,
                "available_gb": None,
            }),
            patch.object(collector, "get_network_stats", return_value={
                "internet_available": True,
            }),
        ):
            health = collector.get_system_health()

        storage = next(
            category for category in health["categories"]
            if category["name"] == "Storage & Filesystem"
        )
        self.assertIsNone(storage["score"])
        self.assertEqual(storage["status"], "unknown")
        self.assertEqual(health["score"], int((0.3 * 84 + 0.35 * 73 + 0.15 * 95) / 0.8))

    def test_host_information_uses_reported_windows_build(self):
        collector = TelemetryCollector()
        with (
            patch("core.live_telemetry.platform.system", return_value="Windows"),
            patch("core.live_telemetry.platform.release", return_value="10"),
            patch("core.live_telemetry.platform.version", return_value="10.0.26100"),
            patch("core.live_telemetry.psutil.boot_time", return_value=1700000000.0),
            patch("core.live_telemetry.time.time", return_value=1700001000.0),
            patch(
                "core.live_telemetry.psutil.cpu_freq",
                return_value=SimpleNamespace(current=2400.0),
            ),
        ):
            host = collector.get_host_info()

        self.assertEqual(host["os_name"], "Windows 11")
        self.assertEqual(host["os_version"], "10.0.26100")
        self.assertEqual(host["cpu_frequency_mhz"], 2400.0)
        self.assertEqual(host["uptime_seconds"], 1000.0)


if __name__ == "__main__":
    unittest.main()
