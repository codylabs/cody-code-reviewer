import src.config as config


def test_default_model_is_luna(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    assert config.get_model() == "gpt-5.6-luna"


def test_openai_model_environment_variable_remains_supported(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.6-terra")

    assert config.get_model() == "gpt-5.6-terra"


def test_csv_settings_are_normalized(monkeypatch):
    monkeypatch.setenv("EXCLUDE_PATHS", " dist/**, , generated/** ")
    monkeypatch.setenv("CONTEXT_FILES", "AGENTS.md, REVIEW.md")

    assert config.get_exclude_paths() == ("dist/**", "generated/**")
    assert config.get_context_files() == ("AGENTS.md", "REVIEW.md")


def test_existing_comment_updates_by_default(monkeypatch):
    monkeypatch.delenv("UPDATE_EXISTING_COMMENT", raising=False)
    assert config.should_update_existing_comment() is True

    monkeypatch.setenv("UPDATE_EXISTING_COMMENT", "false")
    assert config.should_update_existing_comment() is False
