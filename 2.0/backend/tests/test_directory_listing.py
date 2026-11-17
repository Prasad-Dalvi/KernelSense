import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.planner import ReActPlanner
from core.directory_operations import (
    list_directory_files,
    parse_directory_listing_request,
)


class DirectoryListingTests(unittest.TestCase):
    def test_parses_numeric_and_word_counts_with_quoted_windows_style_paths(self):
        with tempfile.TemporaryDirectory(prefix="KernelSense folder ") as directory:
            numeric = parse_directory_listing_request(
                f'list top 5 files in folder "{directory}"'
            )
            word = parse_directory_listing_request(
                f'list five file in folder "{directory}"'
            )

        self.assertEqual(numeric, (directory, 5))
        self.assertEqual(word, (directory, 5))

    def test_list_is_bounded_sorted_and_excludes_subdirectories(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ("echo.txt", "alpha.txt", "delta.txt", "bravo.txt", "charlie.txt", "foxtrot.txt"):
                (folder / name).touch()
            (folder / "folder-entry").mkdir()

            resolved, files = list_directory_files(directory, 5)

        self.assertEqual(resolved, folder.resolve())
        self.assertEqual(
            [file_path.name for file_path in files],
            ["alpha.txt", "bravo.txt", "charlie.txt", "delta.txt", "echo.txt"],
        )

    def test_natural_language_listing_is_local_and_never_calls_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for index in range(7):
                (folder / f"report-{index}.txt").touch()
            (folder / "subfolder").mkdir()

            planner = ReActPlanner()
            with (
                patch("ai.planner.llm_gateway.reason_and_plan") as reason,
                patch.object(planner, "_save_history"),
            ):
                result = planner.plan_and_execute(
                    f'list 5 files in folder "{directory}"',
                    provider="grok",
                )

        reason.assert_not_called()
        self.assertEqual(result["intent"], "DIRECTORY_LISTING")
        self.assertEqual(result["tools_used"], ["local_directory_listing"])
        self.assertEqual(result["commands"], [])
        self.assertEqual(result["response"].count("- `report-"), 5)
        self.assertIn("report-0.txt", result["response"])
        self.assertNotIn("report-5.txt", result["response"])
        self.assertNotIn("subfolder", result["response"])

    def test_missing_directory_returns_local_error_without_calling_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            planner = ReActPlanner()
            with (
                patch("ai.planner.llm_gateway.reason_and_plan") as reason,
                patch.object(planner, "_save_history"),
            ):
                result = planner.plan_and_execute(f"list 5 files in folder {missing}")

        reason.assert_not_called()
        self.assertEqual(result["intent"], "DIRECTORY_LISTING")
        self.assertIn("Directory does not exist", result["response"])

    def test_rejects_directory_listing_over_the_safety_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            planner = ReActPlanner()
            with (
                patch("ai.planner.llm_gateway.reason_and_plan") as reason,
                patch.object(planner, "_save_history"),
            ):
                result = planner.plan_and_execute(f"list 101 files in folder {directory}")

        reason.assert_not_called()
        self.assertIn("from 1 to 100", result["response"])


if __name__ == "__main__":
    unittest.main()
