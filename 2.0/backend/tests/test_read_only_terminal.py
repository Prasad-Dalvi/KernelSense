import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from core.read_only_terminal import run_read_only_command


class ReadOnlyTerminalTests(unittest.TestCase):
    def test_lists_a_bounded_number_of_entries_in_a_quoted_path(self):
        with tempfile.TemporaryDirectory(prefix="KernelSense terminal ") as directory:
            folder = Path(directory)
            for name in ("charlie.txt", "alpha.txt", "bravo.txt"):
                (folder / name).touch()

            result = run_read_only_command(f'dir "{folder}" --limit 2')

        self.assertTrue(result["success"])
        self.assertEqual(len(result["output"].splitlines()), 3)
        self.assertIn("alpha.txt", result["output"])
        self.assertIn("bravo.txt", result["output"])
        self.assertIn("showing 2 of 3", result["output"])

    def test_cd_returns_validated_directory_without_changing_backend_process_cwd(self):
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            child = Path(directory) / "child"
            child.mkdir()

            result = run_read_only_command(f'cd "{child}"', directory)

        self.assertEqual(result["cwd"], str(child.resolve()))
        self.assertEqual(Path.cwd(), original_cwd)

    def test_rejects_shell_chaining_and_arbitrary_commands(self):
        with patch("core.read_only_terminal.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "operators"):
                run_read_only_command("dir & whoami")
            with self.assertRaisesRegex(ValueError, "Unsupported command"):
                run_read_only_command("python -c print(1)")

        run.assert_not_called()

    def test_directory_must_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaisesRegex(ValueError, "does not exist"):
                run_read_only_command(f'dir "{missing}"')

    def test_ask_api_forwards_selected_provider_and_model(self):
        with (
            patch(
                "main.ai_agent.ask",
                return_value={"provider": "grok/grok-4.6"},
            ) as ask,
            TestClient(main.app) as client,
        ):
            response = client.post(
                "/ask",
                json={
                    "query": "Explain this",
                    "provider": "grok",
                    "model": "grok-4.6",
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        ask.assert_called_once_with(
            "Explain this",
            provider="grok",
            api_key=None,
            model="grok-4.6",
        )

    def test_terminal_api_lists_only_requested_number_of_files(self):
        with tempfile.TemporaryDirectory(prefix="KernelSense terminal ") as directory:
            folder = Path(directory)
            (folder / "one.txt").touch()
            (folder / "two.txt").touch()
            (folder / "three.txt").touch()

            with TestClient(main.app) as client:
                response = client.post(
                    "/terminal/run",
                    json={"command": 'dir --limit 2', "cwd": str(folder)},
                )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()["output"].splitlines()), 3)
        self.assertIn("showing 2 of 3", response.json()["output"])

    def test_terminal_api_rejects_arbitrary_shell_text(self):
        with TestClient(main.app) as client:
            response = client.post(
                "/terminal/run",
                json={"command": "cmd /c echo unsafe"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported command", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
