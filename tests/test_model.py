import time
from types import SimpleNamespace
from unittest.mock import patch

import src.model as model


def _claude_response(text):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason="end_turn",
    )


def test_query_model_routes_claude_models_to_anthropic(monkeypatch):
    monkeypatch.setattr(model, "MODEL", "claude-opus-4-8")
    with patch("anthropic.Anthropic") as anthropic_cls:
        anthropic_cls.return_value.messages.create.return_value = _claude_response("Looks good.")

        assert model.query_model("review this") == "Looks good."

        kwargs = anthropic_cls.return_value.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-opus-4-8"
        assert kwargs["messages"] == [{"role": "user", "content": "review this"}]
        assert kwargs["system"] == model.SYSTEM_PROMPT


def test_query_model_routes_other_models_to_openai(monkeypatch):
    monkeypatch.setattr(model, "MODEL", "gpt-5")
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="LGTM"))]
    )
    with patch("openai.OpenAI") as openai_cls:
        openai_cls.return_value.chat.completions.create.return_value = completion

        assert model.query_model("review this") == "LGTM"

        kwargs = openai_cls.return_value.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "gpt-5"


def test_query_claude_returns_error_message_after_retries(monkeypatch):
    monkeypatch.setattr(model, "MODEL", "claude-opus-4-8")
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    with patch("anthropic.Anthropic") as anthropic_cls:
        anthropic_cls.return_value.messages.create.side_effect = Exception("boom")

        result = model.query_claude("review this", retries=2, base_delay=0)

        assert result == "Failed to query the Anthropic API after several attempts."
        assert anthropic_cls.return_value.messages.create.call_count == 2
