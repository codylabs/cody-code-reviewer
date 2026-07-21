from unittest.mock import MagicMock, patch

import pytest

from src.comment_on_pr import post_comment


def test_post_comment_reads_configured_output_file(monkeypatch, tmp_path):
    output_path = tmp_path / "review.md"
    output_path.write_text("Review body", encoding="utf-8")
    monkeypatch.setenv("REVIEW_OUTPUT", str(output_path))

    with patch("src.comment_on_pr.Github") as github_cls:
        pull_request = MagicMock()
        github_cls.return_value.get_repo.return_value.get_pull.return_value = pull_request

        post_comment("codylabs/cody-code-reviewer", 14, "token")

        github_cls.return_value.get_repo.return_value.get_pull.assert_called_once_with(14)
        pull_request.create_issue_comment.assert_called_once_with("Review body")


def test_post_comment_rejects_missing_output_file(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing.md"
    monkeypatch.setenv("REVIEW_OUTPUT", str(missing_path))

    with pytest.raises(FileNotFoundError, match="Review output was not found"):
        post_comment("codylabs/cody-code-reviewer", 14, "token")
