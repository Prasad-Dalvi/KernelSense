import unittest
from unittest.mock import Mock, patch

from ai.llm_provider import GROK_MODEL, GrokProvider, UniversalLLMProvider


class UniversalLLMProviderTests(unittest.TestCase):
    def test_selected_grok_receives_runtime_key_before_fallbacks(self):
        gateway = UniversalLLMProvider()
        gateway.grok.query = Mock(return_value={
            "intent": "GENERAL_QUERY",
            "_model_used": "grok-4.7",
        })
        gateway.gemini.query = Mock(return_value=None)
        gateway.groq.query = Mock(return_value=None)
        gateway.ollama.query = Mock(return_value=None)

        result = gateway.reason_and_plan(
            "Explain this system issue",
            provider="grok",
            api_key="runtime-key",
        )

        gateway.grok.query.assert_called_once_with(
            "User Request: Explain this system issue",
            "runtime-key",
        )
        gateway.gemini.query.assert_not_called()
        self.assertEqual(result["provider"], "grok/grok-4.7")

    def test_selected_provider_falls_back_to_grok(self):
        gateway = UniversalLLMProvider()
        gateway.gemini.query = Mock(return_value=None)
        gateway.grok.query = Mock(return_value={
            "intent": "GENERAL_QUERY",
            "_model_used": "grok-4.7",
        })
        gateway.groq.query = Mock(return_value=None)
        gateway.ollama.query = Mock(return_value=None)

        result = gateway.reason_and_plan("Help", provider="gemini")

        gateway.gemini.query.assert_called_once()
        gateway.grok.query.assert_called_once_with(
            "User Request: Help",
            None,
        )
        self.assertEqual(result["provider"], "grok/grok-4.7")

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


if __name__ == "__main__":
    unittest.main()
