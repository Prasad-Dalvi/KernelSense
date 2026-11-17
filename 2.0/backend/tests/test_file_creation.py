import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from ai.planner import ReActPlanner
from core.file_operations import (
    create_empty_file,
    parse_file_creation_request,
    validate_file_target,
)
import main
from main import CommandApprovalRequest, handle_approve_command


class FileCreationTests(unittest.TestCase):
    def test_parses_creation_request_with_a_quoted_windows_path(self):
        query = r'create a file "C:\Users\Example User\Desktop\notes.txt"'

        self.assertEqual(
            parse_file_creation_request(query),
            r"C:\Users\Example User\Desktop\notes.txt",
        )

    def test_recognizes_creation_request_without_a_target(self):
        self.assertEqual(parse_file_creation_request("create a file"), "")

    def test_does_not_classify_file_search_as_creation(self):
        self.assertIsNone(parse_file_creation_request("find report.txt"))

    def test_rejects_relative_paths_and_missing_parent_directories(self):
        with self.assertRaisesRegex(ValueError, "absolute path"):
            validate_file_target("notes.txt")

        with tempfile.TemporaryDirectory() as directory:
            missing_parent = Path(directory) / "missing" / "notes.txt"
            with self.assertRaisesRegex(ValueError, "parent folder does not exist"):
                validate_file_target(str(missing_parent))

    def test_file_creation_is_exclusive_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "notes.txt"

            self.assertEqual(create_empty_file(str(target)), target)
            self.assertEqual(target.read_bytes(), b"")
            target.write_text("keep this content", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                create_empty_file(str(target))

            self.assertEqual(target.read_text(encoding="utf-8"), "keep this content")

    def test_planner_routes_file_creation_without_calling_the_llm(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "notes.txt"
            planner = ReActPlanner()

            with (
                patch("ai.planner.llm_gateway.reason_and_plan") as reason,
                patch.object(planner, "_save_history"),
            ):
                result = planner.plan_and_execute(f'create file "{target}"')

            reason.assert_not_called()
            self.assertEqual(result["intent"], "FILE_CREATE")
            self.assertEqual(result["commands"][0]["action"], "create_file")
            self.assertEqual(result["commands"][0]["file_path"], str(target))
            self.assertFalse(target.exists())

    def test_missing_target_returns_a_prompt_instead_of_searching(self):
        planner = ReActPlanner()

        with (
            patch("ai.planner.llm_gateway.reason_and_plan") as reason,
            patch.object(planner, "_save_history"),
        ):
            result = planner.plan_and_execute("create a file")

        reason.assert_not_called()
        self.assertEqual(result["intent"], "FILE_CREATE")
        self.assertIn("full path and file name", result["response"])
        self.assertEqual(result["commands"], [])

    def test_approval_creates_the_saved_file_action_not_the_client_command(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "approved.txt"
            history = [{"commands": [{
                "id": "cmd-file-create",
                "action": "create_file",
                "file_path": str(target),
                "command": f"Create empty file: {target}",
            }]}]

            with patch("main.db_engine.get_history", return_value=history):
                result = handle_approve_command(CommandApprovalRequest(
                    command_id="cmd-file-create",
                    command="must not be executed",
                ))

            self.assertTrue(result["success"])
            self.assertEqual(target.read_bytes(), b"")

    def test_approval_reports_existing_file_without_changing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "already-there.txt"
            target.write_text("preserve", encoding="utf-8")
            history = [{"commands": [{
                "id": "cmd-existing-file",
                "action": "create_file",
                "file_path": str(target),
            }]}]

            with patch("main.db_engine.get_history", return_value=history):
                with self.assertRaises(HTTPException) as raised:
                    handle_approve_command(CommandApprovalRequest(
                        command_id="cmd-existing-file",
                    ))

            self.assertEqual(raised.exception.status_code, 409)
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve")

    def test_unknown_approval_is_not_reported_as_success(self):
        with (
            patch("main.db_engine.get_history", return_value=[]),
            patch("main.command_safety_engine.execute_command") as execute,
        ):
            with self.assertRaises(HTTPException) as raised:
                handle_approve_command(CommandApprovalRequest(
                    command_id="missing",
                    command="echo unauthorized",
                ))

        self.assertEqual(raised.exception.status_code, 404)
        execute.assert_not_called()

    def test_api_creates_requested_file_only_after_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "api-created.txt"
            saved_commands = []

            def save_history(**kwargs):
                saved_commands.extend(kwargs["proposed_commands"])

            with (
                patch("main.db_engine.save_history", side_effect=save_history),
                patch(
                    "main.db_engine.get_history",
                    side_effect=lambda limit=50: [{"commands": saved_commands}],
                ),
                TestClient(main.app) as client,
            ):
                ask = client.post("/ask", json={"query": f'create file "{target}"'})
                self.assertEqual(ask.status_code, 200, ask.text)
                command = ask.json()["commands"][0]
                self.assertFalse(target.exists())

                approved = client.post(
                    "/commands/approve",
                    json={"command_id": command["id"]},
                )
                self.assertEqual(approved.status_code, 200, approved.text)
                self.assertTrue(target.is_file())
                self.assertEqual(target.read_bytes(), b"")

                duplicate = client.post(
                    "/commands/approve",
                    json={"command_id": command["id"]},
                )
                self.assertEqual(duplicate.status_code, 409)


if __name__ == "__main__":
    unittest.main()
