from unittest.mock import patch

import src.round_cap as round_cap
from src.round_cap import (
    CAP_NOTICE_MARKER,
    ROUND_MARKER_TEMPLATE,
    RoundCapDecision,
    build_cap_notice,
    cap_notice_already_posted,
    check_round_cap,
    count_review_rounds,
    decide,
    extract_marker_sha,
    has_override_label,
    is_manual_rerun,
    latest_reviewed_sha,
    parse_max_rounds,
)


def marked_review(sha: str) -> str:
    return f"AI Code Review by Cody (https://docs.codylabs.uk/)\n{ROUND_MARKER_TEMPLATE.format(sha=sha)}\n\nLooks fine."


def legacy_review() -> str:
    # Posted before the marker existed: no HTML comment, just the header.
    return "AI Code Review by Cody (https://docs.codylabs.uk/) · Model: `gpt-5.6-luna`\n\nLooks fine."


# --- parse_max_rounds ---

def test_parse_max_rounds_default_is_unlimited():
    assert parse_max_rounds(None) == 0
    assert parse_max_rounds("") == 0
    assert parse_max_rounds("0") == 0


def test_parse_max_rounds_parses_an_integer():
    assert parse_max_rounds("2") == 2


def test_parse_max_rounds_rejects_non_integers():
    import pytest

    with pytest.raises(RuntimeError, match="must be an integer"):
        parse_max_rounds("two")


# --- marker extraction and round counting ---

def test_extract_marker_sha_reads_the_embedded_sha():
    assert extract_marker_sha(marked_review("abc123")) == "abc123"


def test_extract_marker_sha_returns_none_when_absent():
    assert extract_marker_sha(legacy_review()) is None
    assert extract_marker_sha("just a regular comment") is None


def test_count_review_rounds_counts_marked_reviews():
    comments = [marked_review("sha1"), marked_review("sha2")]
    assert count_review_rounds(comments) == 2


def test_count_review_rounds_counts_legacy_unmarked_reviews_too():
    comments = [legacy_review(), legacy_review(), marked_review("sha3")]
    assert count_review_rounds(comments) == 3


def test_count_review_rounds_ignores_unrelated_comments():
    comments = ["thanks!", "lgtm", marked_review("sha1")]
    assert count_review_rounds(comments) == 1


def test_latest_reviewed_sha_returns_the_most_recent_marked_sha():
    comments = [marked_review("sha1"), "unrelated comment", marked_review("sha2")]
    assert latest_reviewed_sha(comments) == "sha2"


def test_latest_reviewed_sha_none_when_no_marked_reviews():
    assert latest_reviewed_sha([legacy_review(), "a comment"]) is None


def test_cap_notice_already_posted():
    assert cap_notice_already_posted([f"note {CAP_NOTICE_MARKER}"]) is True
    assert cap_notice_already_posted(["nothing here"]) is False


def test_has_override_label():
    assert has_override_label(["bug", "cody:force-review"]) is True
    assert has_override_label(["bug"]) is False


def test_is_manual_rerun():
    assert is_manual_rerun(None) is False
    assert is_manual_rerun("1") is False
    assert is_manual_rerun("2") is True
    assert is_manual_rerun("3") is True
    assert is_manual_rerun("not a number") is False


def test_build_cap_notice_mentions_the_cap_and_the_override():
    notice = build_cap_notice(2)
    assert "2 rounds" in notice
    assert "cody:force-review" in notice
    assert CAP_NOTICE_MARKER in notice


# --- decide(): under / at / over the cap, unlimited, override, unchanged head ---

def test_decide_under_the_cap_reviews():
    comments = [marked_review("sha1")]
    result = decide(max_rounds=2, comment_bodies=comments, labels=[], head_sha="sha2")
    assert result == RoundCapDecision(True, "under cap (1/2)")


def test_decide_at_the_cap_boundary_still_reviews():
    # One round posted, cap is 1: the boundary itself should still review;
    # it is the round *after* reaching the cap that gets skipped.
    comments = []
    result = decide(max_rounds=1, comment_bodies=comments, labels=[], head_sha="sha1")
    assert result.should_review is True


def test_decide_over_the_cap_skips():
    comments = [marked_review("sha1"), marked_review("sha2")]
    result = decide(max_rounds=2, comment_bodies=comments, labels=[], head_sha="sha3")
    assert result == RoundCapDecision(False, "cap reached (2/2)")


def test_decide_default_unlimited_always_reviews():
    comments = [marked_review(f"sha{i}") for i in range(20)]
    result = decide(max_rounds=0, comment_bodies=comments, labels=[], head_sha="sha20")
    assert result == RoundCapDecision(True, "no cap configured")


def test_decide_override_label_reviews_despite_the_cap():
    comments = [marked_review("sha1"), marked_review("sha2")]
    result = decide(max_rounds=2, comment_bodies=comments, labels=["cody:force-review"], head_sha="sha3")
    assert result == RoundCapDecision(True, "override label present")


def test_decide_manual_rerun_reviews_despite_the_cap():
    comments = [marked_review("sha1"), marked_review("sha2")]
    result = decide(max_rounds=2, comment_bodies=comments, labels=[], head_sha="sha3", run_attempt="2")
    assert result == RoundCapDecision(True, "manual workflow re-run")


def test_decide_manual_rerun_reviews_despite_an_unchanged_head_commit():
    # The scenario the override exists for: re-reviewing a PR with no new
    # commits, which the head-sha-unchanged check would otherwise skip.
    comments = [marked_review("sha1")]
    result = decide(max_rounds=0, comment_bodies=comments, labels=[], head_sha="sha1", run_attempt="2")
    assert result == RoundCapDecision(True, "manual workflow re-run")


def test_decide_first_attempt_is_not_treated_as_a_manual_rerun():
    comments = [marked_review("sha1"), marked_review("sha2")]
    result = decide(max_rounds=2, comment_bodies=comments, labels=[], head_sha="sha3", run_attempt="1")
    assert result == RoundCapDecision(False, "cap reached (2/2)")


def test_decide_skips_when_head_commit_has_not_changed_since_last_review():
    comments = [marked_review("sha1")]
    result = decide(max_rounds=0, comment_bodies=comments, labels=[], head_sha="sha1")
    assert result == RoundCapDecision(False, "head commit unchanged since the last review")


def test_decide_unchanged_head_check_runs_even_under_an_unlimited_cap():
    # Confirms this is a genuinely separate, always-on check, not something
    # that only kicks in once a cap is configured.
    comments = [marked_review("same-sha")]
    result = decide(max_rounds=0, comment_bodies=comments, labels=[], head_sha="same-sha")
    assert result.should_review is False


def test_decide_pre_existing_unmarked_reviews_count_toward_the_cap():
    # A PR that already had two unmarked (legacy) reviews before this
    # feature shipped should not get two more marked reviews for free.
    comments = [legacy_review(), legacy_review()]
    result = decide(max_rounds=2, comment_bodies=comments, labels=[], head_sha="sha1")
    assert result == RoundCapDecision(False, "cap reached (2/2)")


# --- check_round_cap(): the orchestration used by the script entrypoint ---

def test_check_round_cap_posts_the_notice_once_when_cap_is_reached(monkeypatch):
    from src.github_client import PullRequestContext

    fake_context = PullRequestContext(
        head_sha="sha3",
        labels=[],
        comment_bodies=[marked_review("sha1"), marked_review("sha2")],
    )
    monkeypatch.setattr(round_cap, "get_pull_request_context", lambda *_: fake_context)
    posted = []
    monkeypatch.setattr(round_cap, "post_issue_comment", lambda repo, pr, body: posted.append(body))

    result = check_round_cap("codylabs/cody-code-reviewer", 14, "2")

    assert result.should_review is False
    assert len(posted) == 1
    assert CAP_NOTICE_MARKER in posted[0]


def test_check_round_cap_manual_rerun_reviews_and_posts_no_notice(monkeypatch):
    from src.github_client import PullRequestContext

    fake_context = PullRequestContext(
        head_sha="sha3",
        labels=[],
        comment_bodies=[marked_review("sha1"), marked_review("sha2")],
    )
    monkeypatch.setattr(round_cap, "get_pull_request_context", lambda *_: fake_context)
    posted = []
    monkeypatch.setattr(round_cap, "post_issue_comment", lambda repo, pr, body: posted.append(body))

    result = check_round_cap("codylabs/cody-code-reviewer", 14, "2", "2")

    assert result == RoundCapDecision(True, "manual workflow re-run")
    assert posted == []


def test_check_round_cap_does_not_repost_the_notice(monkeypatch):
    from src.github_client import PullRequestContext

    fake_context = PullRequestContext(
        head_sha="sha3",
        labels=[],
        comment_bodies=[
            marked_review("sha1"),
            marked_review("sha2"),
            f"already told you {CAP_NOTICE_MARKER}",
        ],
    )
    monkeypatch.setattr(round_cap, "get_pull_request_context", lambda *_: fake_context)
    posted = []
    monkeypatch.setattr(round_cap, "post_issue_comment", lambda repo, pr, body: posted.append(body))

    result = check_round_cap("codylabs/cody-code-reviewer", 14, "2")

    assert result.should_review is False
    assert posted == []


def test_check_round_cap_does_not_post_a_notice_when_under_the_cap(monkeypatch):
    from src.github_client import PullRequestContext

    fake_context = PullRequestContext(head_sha="sha1", labels=[], comment_bodies=[])
    monkeypatch.setattr(round_cap, "get_pull_request_context", lambda *_: fake_context)
    posted = []
    monkeypatch.setattr(round_cap, "post_issue_comment", lambda repo, pr, body: posted.append(body))

    result = check_round_cap("codylabs/cody-code-reviewer", 14, "2")

    assert result.should_review is True
    assert posted == []


def test_write_output_writes_to_github_output(monkeypatch, tmp_path):
    output_path = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    round_cap.write_output(RoundCapDecision(True, "under cap (0/2)"))

    assert output_path.read_text(encoding="utf-8") == "should_review=true\n"


def test_write_output_writes_false_when_skipping(monkeypatch, tmp_path):
    output_path = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_path))

    round_cap.write_output(RoundCapDecision(False, "cap reached (2/2)"))

    assert output_path.read_text(encoding="utf-8") == "should_review=false\n"
