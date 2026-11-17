import unittest
from unittest.mock import Mock, patch

from ai.llm_provider import (
    GROK_MODEL,
    SYSTEM_PROMPT,
    GeminiProvider,
    GrokProvider,
    UniversalLLMProvider,
)


class UniversalLLMProviderTests(unittest.TestCase):
    def test_selected_grok_receives_runtime_key_and_model_without_fallbacks(self):
        gateway = UniversalLLMProvider()
        gateway.grok.query = Mock(return_value={
            "intent": "GENERAL_QUERY",
            "_model_used": "grok-4.6",
        })
        gateway.gemini.query = Mock(return_value=None)
        gateway.groq.query = Mock(return_value=None)
        gateway.ollama.query = Mock(return_value=None)

        result = gateway.reason_and_plan(
            "Explain this system issue",
            provider="grok",
            api_key="runtime-key",
            model="grok-4.6",
        )

        gateway.grok.query.assert_called_once()
        user_message, runtime_key, selected_model = gateway.grok.query.call_args.args
        self.assertIn("terminal=", user_message)
        self.assertIn("working_directory=", user_message)
        self.assertIn("User Request: Explain this system issue", user_message)
        self.assertEqual(runtime_key, "runtime-key")
        self.assertEqual(selected_model, "grok-4.6")
        gateway.gemini.query.assert_not_called()
        self.assertEqual(result["provider"], "grok/grok-4.6")

    def test_prompt_identifies_the_command_shell_and_forbids_unrun_results(self):
        self.assertIn("non-interactive cmd.exe", SYSTEM_PROMPT)
        self.assertIn("Never claim a command ran", SYSTEM_PROMPT)

    @patch("ai.llm_provider.requests.post")
    def test_explicit_gemini_model_does_not_fall_back_to_another_model(self, post):
        response = Mock(status_code=404, text="model unavailable")
        post.return_value = response

        result = GeminiProvider().query("Help", "runtime-key", "selected-gemini-model")

        self.assertIsNone(result)
        post.assert_called_once()
        self.assertIn(
            "/models/selected-gemini-model:generateContent",
            post.call_args.args[0],
        )

    def test_selected_provider_failure_does_not_switch_provider(self):
        gateway = UniversalLLMProvider()
        gateway.gemini.query = Mock(return_value=None)
        gateway.grok.query = Mock(return_value={
            "intent": "GENERAL_QUERY",
            "_model_used": "grok-4.7",
        })
        gateway.groq.query = Mock(return_value=None)
        gateway.ollama.query = Mock(return_value=None)

        result = gateway.reason_and_plan("Help", provider="gemini")

        self.assertIsNone(result)
        gateway.gemini.query.assert_called_once()
        gateway.grok.query.assert_not_called()
        gateway.groq.query.assert_not_called()
        gateway.ollama.query.assert_not_called()

    @patch("ai.llm_provider.requests.post")
    def test_grok_uses_xai_api_and_runtime_key(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '{"intent":"GENERAL_QUERY"}'}}]
        }
        post.return_value = response

        result = GrokProvider().query("Help", "runtime-key")

        self.assertEqual(result["intent"], "GENERAL_QUERY")
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://api.x.ai/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer runtime-key")
        self.assertEqual(kwargs["json"]["model"], GROK_MODEL)
        self.assertEqual(kwargs["json"]["max_tokens"], 512)

    @patch("ai.llm_provider.requests.post")
    def test_grok_uses_explicitly_selected_model(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": '{"intent":"GENERAL_QUERY"}'}}]
        }
        post.return_value = response

        result = GrokProvider().query("Help", "runtime-key", "grok-4.6")

        self.assertEqual(result["_model_used"], "grok-4.6")
        self.assertEqual(post.call_args.kwargs["json"]["model"], "grok-4.6")


if __name__ == "__main__":
    unittest.main()
