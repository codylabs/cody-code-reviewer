import src.config as config


def test_default_model_is_current_openai_flagship(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    assert config.get_model() == "gpt-5.6-sol"


def test_openai_model_environment_variable_remains_supported(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-terra")

    assert config.get_model() == "gpt-5.6-terra"
