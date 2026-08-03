from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_composite_action_never_checks_out_pull_request_code():
    manifest = (ROOT / "action.yml").read_text(encoding="utf-8")

    assert "actions/checkout" not in manifest
    assert '"$GITHUB_ACTION_PATH/src/review_pull_request.py"' in manifest
    assert '"$GITHUB_ACTION_PATH/src/comment_on_pr.py"' in manifest
    assert "--require-hashes" in manifest


def test_secret_bearing_dogfood_workflow_uses_protected_base_definition():
    workflow = (
        ROOT / ".github" / "workflows" / "code_review.yml"
    ).read_text(encoding="utf-8")

    assert "pull_request_target:" in workflow
    assert "actions/checkout" not in workflow
    assert "pull-requests: write" in workflow
    assert "contents: read" in workflow
    assert "uses: codylabs/cody-code-reviewer@" in workflow
    assert "\n        uses: ./" not in workflow
