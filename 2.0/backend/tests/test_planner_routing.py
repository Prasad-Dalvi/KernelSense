import unittest
from unittest.mock import patch

from ai.planner import ReActPlanner


class PlannerRoutingTests(unittest.TestCase):
    def test_recognized_request_is_handled_locally_without_provider_call(self):
        planner = ReActPlanner()
        local_result = {
            "intent": "GREETING",
            "action_type": "CHAT",
            "provider": "local_offline_engine",
        }

        with (
            patch.object(planner, "_local_rule_planner", return_value=local_result),
            patch.object(planner, "_format_greeting", return_value={"response": "Hello"}) as format_greeting,
            patch.object(planner, "_build_telemetry_context") as build_telemetry,
            patch("ai.planner.llm_gateway.reason_and_plan") as reason,
        ):
            result = planner.plan_and_execute("hello")

        self.assertEqual(result["response"], "Hello")
        format_greeting.assert_called_once()
        build_telemetry.assert_called_once()
        reason.assert_not_called()

    def test_unknown_request_goes_to_selected_provider_without_unneeded_telemetry(self):
        planner = ReActPlanner()
        ai_result = {"intent": "GENERAL_QUERY", "response_markdown": "Answer"}

        with (
            patch.object(planner, "_local_rule_planner", return_value=None),
            patch.object(planner, "_build_telemetry_context") as build_telemetry,
            patch("ai.planner.llm_gateway.reason_and_plan", return_value=ai_result) as reason,
            patch.object(planner, "_format_general", return_value={"response": "Answer"}),
        ):
            result = planner.plan_and_execute(
                "Explain how a hash table works",
                provider="grok",
                api_key="runtime-only-key",
                model="grok-4.6",
            )

        self.assertEqual(result["response"], "Answer")
        build_telemetry.assert_not_called()
        reason.assert_called_once_with(
            "Explain how a hash table works",
            {},
            "grok",
            "runtime-only-key",
            "grok-4.6",
        )

    def test_ai_command_is_preserved_and_risk_is_carried_to_approval(self):
        planner = ReActPlanner()
        command = "echo hello"
        ai_result = {
            "intent": "WINDOWS_COMMAND",
            "response_markdown": "Prepared command.",
            "proposed_commands": [{
                "command": command,
                "explanation": "Prints a message.",
                "risk_level": "MEDIUM",
                "risk_reason": "Writes to the console.",
            }],
        }

        with patch.object(planner, "_save_history"):
            result = planner._format_general(
                ai_result,
                "print hello",
                {},
                "gemini/model",
            )

        self.assertEqual(len(result["commands"]), 1)
        proposed = result["commands"][0]
        self.assertEqual(proposed["command"], command)
        self.assertNotIn("wsl.exe", proposed["command"])
        self.assertEqual(proposed["risk_level"], "MEDIUM")
        self.assertEqual(proposed["risk_reason"], "Writes to the console.")
        self.assertIn("has not run yet", result["response"])
        self.assertNotIn("Prepared command.", result["response"])

    def test_local_risk_can_raise_the_provider_risk(self):
        planner = ReActPlanner()
        ai_result = {
            "intent": "WINDOWS_COMMAND",
            "response_markdown": "Prepared command.",
            "proposed_commands": [{
                "command": "npm install example",
                "explanation": "Install a package.",
                "risk_level": "LOW",
                "risk_reason": "Provider assessment.",
            }],
        }

        with patch.object(planner, "_save_history"):
            result = planner._format_general(
                ai_result,
                "install example",
                {},
                "gemini/model",
            )

        proposed = result["commands"][0]
        self.assertEqual(proposed["risk_level"], "MEDIUM")
        self.assertIn("Provider assessment.", proposed["risk_reason"])

    def test_hard_blocked_command_is_not_offered_for_approval(self):
        planner = ReActPlanner()
        ai_result = {
            "intent": "WINDOWS_COMMAND",
            "response_markdown": "Prepared command.",
            "proposed_commands": [{
                "command": "format C:",
                "explanation": "Format the system drive.",
                "risk_level": "LOW",
            }],
        }

        with patch.object(planner, "_save_history"):
            result = planner._format_general(
                ai_result,
                "format the system drive",
                {},
                "gemini/model",
            )

        self.assertEqual(result["commands"], [])
        self.assertIn("Command blocked", result["response"])


if __name__ == "__main__":
    unittest.main()
