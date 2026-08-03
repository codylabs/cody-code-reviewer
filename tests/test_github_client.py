import pytest
import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from github.GithubException import GithubException

import src.github_client as github_client
from src.github_client import (
    get_pull_request_context,
    get_pull_request_data,
    path_is_excluded,
    post_issue_comment,
)
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
        head=SimpleNamespace(sha="abc123"),
        base=SimpleNamespace(sha="base-sha"),
        get_files=lambda: [
            SimpleNamespace(filename="screenshot.png", patch=None),
            SimpleNamespace(filename="src/app.py", patch="@@ -1 +1 @@"),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        repo = github_cls.return_value.get_repo.return_value
        repo.get_pull.return_value = pull_request
        repo.get_contents.side_effect = GithubException(status=404, data={}, headers={})

        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    assert "Diff for src/app.py" in result.diff
    assert "screenshot.png" in result.diff
    assert "None" not in result.diff
    assert result.head_sha == "abc123"


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
        head=SimpleNamespace(sha="def456"),
        base=SimpleNamespace(sha="base-sha"),
        get_files=lambda: [
            SimpleNamespace(filename="src/app.py", patch="x" * 100),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        repo = github_cls.return_value.get_repo.return_value
        repo.get_pull.return_value = pull_request
        repo.get_contents.side_effect = GithubException(status=404, data={}, headers={})

        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    assert len(result.diff) == 40
    assert "truncated" in result.diff
    assert len(result.description) == 20
    assert "trunc" in result.description

def test_get_pull_request_context_missing_token_raises_clear_error(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", None)

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN is required"):
        get_pull_request_context("octocat/Hello-World", 6)


def test_get_pull_request_context_returns_head_sha_labels_and_comments(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")
    pull_request = SimpleNamespace(
        head=SimpleNamespace(sha="abc123"),
        get_labels=lambda: [SimpleNamespace(name="bug"), SimpleNamespace(name="cody:force-review")],
        get_issue_comments=lambda: [
            SimpleNamespace(body="AI Code Review by Cody (https://docs.codylabs.uk/)"),
            SimpleNamespace(body=None),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        github_cls.return_value.get_repo.return_value.get_pull.return_value = pull_request

        context = get_pull_request_context("codylabs/cody-code-reviewer", 14)

    assert context.head_sha == "abc123"
    assert context.labels == ["bug", "cody:force-review"]
    assert context.comment_bodies == ["AI Code Review by Cody (https://docs.codylabs.uk/)", ""]


def test_post_issue_comment_missing_token_raises_clear_error(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", None)

    with pytest.raises(RuntimeError, match="GITHUB_TOKEN is required"):
        post_issue_comment("octocat/Hello-World", 6, "note")


def test_post_issue_comment_posts_the_given_body(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")

    with patch("src.github_client.Github") as github_cls:
        pull_request = MagicMock()
        github_cls.return_value.get_repo.return_value.get_pull.return_value = pull_request

        post_issue_comment("codylabs/cody-code-reviewer", 14, "Cap reached")

        pull_request.create_issue_comment.assert_called_once_with("Cap reached")


def test_excluded_paths_are_not_sent_to_the_model(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")
    monkeypatch.setenv("EXCLUDE_PATHS", "generated/**,**/*.min.js")
    monkeypatch.setenv("CONTEXT_FILES", "")
    now = datetime.now(timezone.utc)
    pull_request = SimpleNamespace(
        title="Update generated assets",
        body="",
        state="open",
        created_at=now,
        updated_at=now,
        head=SimpleNamespace(sha="head-sha"),
        base=SimpleNamespace(sha="base-sha"),
        get_files=lambda: [
            SimpleNamespace(filename="generated/client.py", patch="generated patch"),
            SimpleNamespace(filename="web/app.min.js", patch="minified patch"),
            SimpleNamespace(filename="src/app.py", patch="reviewable patch"),
        ],
    )

    with patch("src.github_client.Github") as github_cls:
        repo = github_cls.return_value.get_repo.return_value
        repo.get_pull.return_value = pull_request
        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    assert "reviewable patch" in result.diff
    assert "generated patch" not in result.diff
    assert "minified patch" not in result.diff
    assert "generated/client.py" in result.diff
    assert "web/app.min.js" in result.diff


def test_context_is_read_from_trusted_base_commit(monkeypatch):
    monkeypatch.setattr(github_client.config, "GITHUB_TOKEN", "token")
    monkeypatch.setenv("CONTEXT_FILES", "AGENTS.md")
    now = datetime.now(timezone.utc)
    pull_request = SimpleNamespace(
        title="Feature",
        body="",
        state="open",
        created_at=now,
        updated_at=now,
        head=SimpleNamespace(sha="head-sha"),
        base=SimpleNamespace(sha="trusted-base"),
        get_files=lambda: [
            SimpleNamespace(filename="src/app.py", patch="reviewable patch"),
        ],
    )
    content = SimpleNamespace(decoded_content=b"Focus on authorization boundaries.")

    with patch("src.github_client.Github") as github_cls:
        repo = github_cls.return_value.get_repo.return_value
        repo.get_pull.return_value = pull_request
        repo.get_contents.return_value = content
        result = get_pull_request_data("codylabs/cody-code-reviewer", 14)

    repo.get_contents.assert_called_once_with("AGENTS.md", ref="trusted-base")
    assert "Focus on authorization boundaries." in result.context


def test_path_exclusions_use_glob_patterns():
    patterns = ("generated/**", "**/*.min.js")
    assert path_is_excluded("generated/client.py", patterns)
    assert path_is_excluded("web/app.min.js", patterns)
    assert not path_is_excluded("src/app.py", patterns)


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
