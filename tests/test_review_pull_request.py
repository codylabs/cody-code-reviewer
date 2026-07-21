from types import SimpleNamespace

import src.review_pull_request as reviewer


def test_review_writes_to_configured_output(monkeypatch, tmp_path):
    output_path = tmp_path / "review.md"
    pull_request = SimpleNamespace(
        title="Fix action",
        description="Make the action self-contained",
        diff="diff --git a/action.yml b/action.yml",
    )
    monkeypatch.setenv("REVIEW_OUTPUT", str(output_path))
    monkeypatch.setattr(reviewer, "get_pull_request_data", lambda *_: pull_request)
    monkeypatch.setattr(reviewer, "query_model", lambda prompt: "Looks good")

    reviewer.review_pull_request("codylabs/cody-code-reviewer", 14)

    assert output_path.read_text(encoding="utf-8") == "Looks good"
