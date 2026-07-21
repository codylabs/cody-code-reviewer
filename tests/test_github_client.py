import pytest
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import src.github_client as github_client
from src.github_client import get_pull_request_data
from src.model import query_openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_missing_github_token_raises_clear_error(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", None)

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN is required"):
        get_pull_request_data("octocat/Hello-World", 6)


def test_files_without_textual_patches_are_omitted(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")
    now = datetime.now(timezone.utc)
    pull_request = SimpleNamespace(
        title="Update assets",
        body="Updates an image and code",
        state="open",
        created_at=now,
        updated_at=now,
        get_files=lambda: [
            SimpleNamespace(filename="screenshot.png", patch=None),
            SimpleNamespace(filename="src/app.py", patch="@@ -1 +1 @@"),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        github_cls.return_value.get_repo.return_value.get_pull.return_value = pull_request

        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    assert "Diff for src/app.py" in result.diff
    assert "screenshot.png" in result.diff
    assert "None" not in result.diff


def test_pull_request_payload_is_bounded(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")
    monkeypatch.setattr(github_client, "MAX_DIFF_CHARS", 40)
    monkeypatch.setattr(github_client, "MAX_DESCRIPTION_CHARS", 20)
    now = datetime.now(timezone.utc)
    pull_request = SimpleNamespace(
        title="Large update",
        body="d" * 100,
        state="open",
        created_at=now,
        updated_at=now,
        get_files=lambda: [
            SimpleNamespace(filename="src/app.py", patch="x" * 100),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        github_cls.return_value.get_repo.return_value.get_pull.return_value = pull_request

        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    assert result.diff.endswith("[Diff truncated because it exceeded the review size limit.]")
    assert result.description.endswith(
        "[Description truncated because it exceeded the review size limit.]"
    )

# This test should be run sparingly due to its impact on API rate limits and potential costs.

@pytest.mark.integration
def test_integration_with_real_endpoints():
    repo_name = "octocat/Hello-World"
    pull_number = 6 

    # Fetch pull request data and diff from GitHub
    pr = get_pull_request_data(repo_name, pull_number)
    assert pr is not None, "Failed to fetch PR data"

    # Construct the prompt for OpenAI based on the fetched data
    prompt = f"Please review the following pull request:\nTitle: {pr.title}\nDescription: {pr.description}\nDiff: {pr.diff}\n"
    logging.info(f"Sending the following prompt to OpenAI: {prompt}")

    # Send the prompt to OpenAI and get a response
    response = query_openai(prompt)
    logging.info(f"Received the following response from OpenAI: {response}")

    assert response is not None and response != "", "No response received from OpenAI"
