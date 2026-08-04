import os
import sys
from dataclasses import dataclass
from typing import List, Optional

try:
    from . import config
    from .github_client import get_pull_request_context, post_issue_comment
except ImportError:  # Support running this module as a script dependency.
    import config
    from github_client import get_pull_request_context, post_issue_comment

# Embedded in every review comment Cody posts, right after the visible header.
# It is an HTML comment so it does not render, and it is what round counting
# reads, not the header text, which changes between versions and cannot be
# trusted as a stable counter.
ROUND_MARKER_PREFIX = "<!-- cody:review-round"
ROUND_MARKER_TEMPLATE = "<!-- cody:review-round sha={sha} -->"

# Embedded in the one-time "cap reached" note so a later push can tell the
# note was already posted and skip posting it again.
CAP_NOTICE_MARKER = "<!-- cody:round-cap-reached -->"

# Historical reviews posted before this feature shipped have no marker at
# all. They can still be told apart from a random comment because every
# review Cody has ever posted starts with this header text, so a comment
# that starts with it but has no marker is counted as one legacy round.
LEGACY_HEADER_PREFIX = "AI Code Review by Cody"

# Escape hatch: add this label to a pull request to get one more review
# despite the cap. Documented in the README next to the max_review_rounds
# input.
OVERRIDE_LABEL = "cody:force-review"


@dataclass
class RoundCapDecision:
    should_review: bool
    reason: str


def parse_max_rounds(raw: Optional[str]) -> int:
    """Parse the max_review_rounds input. Empty or 0 means unlimited, which
    is also today's behaviour, so existing workflows that do not set this
    input see no change."""
    raw = (raw or "").strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError(f"max_review_rounds must be an integer, got {raw!r}.")


def extract_marker_sha(comment_body: str) -> Optional[str]:
    for line in comment_body.splitlines():
        line = line.strip()
        if line.startswith(ROUND_MARKER_PREFIX) and "sha=" in line:
            after_sha = line.split("sha=", 1)[1]
            return after_sha.split(" ", 1)[0]
    return None


def count_review_rounds(comment_bodies: List[str]) -> int:
    """Total rounds so far: marked reviews plus legacy unmarked ones."""
    marked = 0
    legacy = 0
    for body in comment_bodies:
        if ROUND_MARKER_PREFIX in body:
            marked += 1
        elif body.lstrip().startswith(LEGACY_HEADER_PREFIX):
            legacy += 1
    return marked + legacy


def latest_reviewed_sha(comment_bodies: List[str]) -> Optional[str]:
    """The head SHA embedded in the most recently posted marked review, if
    any. Comments are returned oldest first, so the last match wins."""
    sha = None
    for body in comment_bodies:
        found = extract_marker_sha(body)
        if found:
            sha = found
    return sha


def cap_notice_already_posted(comment_bodies: List[str]) -> bool:
    return any(CAP_NOTICE_MARKER in body for body in comment_bodies)


def has_override_label(labels: List[str]) -> bool:
    return OVERRIDE_LABEL in labels


def is_manual_rerun(run_attempt: Optional[str]) -> bool:
    """github.run_attempt is "1" on a workflow's first execution and goes up
    each time a user clicks Re-run jobs on that same run. A value above 1
    means this specific execution was manually re-triggered, which is the
    override documented for pull requests that have no new commits to push
    (so the head-sha-unchanged check below would otherwise also skip it,
    on top of the cap)."""
    try:
        return int(run_attempt or "1") > 1
    except ValueError:
        return False


def build_cap_notice(max_rounds: int) -> str:
    return (
        f"Cody reached its review cap ({max_rounds} rounds) for this pull request "
        "and will not post another automatic review here.\n\n"
        f"To get one more review, add the `{OVERRIDE_LABEL}` label to this pull "
        "request, or re-run this workflow manually.\n"
        f"{CAP_NOTICE_MARKER}\n"
    )


def decide(
    max_rounds: int,
    comment_bodies: List[str],
    labels: List[str],
    head_sha: str,
    run_attempt: Optional[str] = None,
) -> RoundCapDecision:
    if has_override_label(labels):
        return RoundCapDecision(True, "override label present")

    if is_manual_rerun(run_attempt):
        return RoundCapDecision(True, "manual workflow re-run")

    latest_sha = latest_reviewed_sha(comment_bodies)
    if latest_sha is not None and latest_sha == head_sha:
        return RoundCapDecision(False, "head commit unchanged since the last review")

    if max_rounds <= 0:
        return RoundCapDecision(True, "no cap configured")

    rounds_so_far = count_review_rounds(comment_bodies)
    if rounds_so_far < max_rounds:
        return RoundCapDecision(True, f"under cap ({rounds_so_far}/{max_rounds})")

    return RoundCapDecision(False, f"cap reached ({rounds_so_far}/{max_rounds})")


def check_round_cap(
    repo_name: str,
    pull_number: int,
    max_rounds_raw: Optional[str],
    run_attempt_raw: Optional[str] = None,
) -> RoundCapDecision:
    max_rounds = parse_max_rounds(max_rounds_raw)
    context = get_pull_request_context(repo_name, pull_number)
    decision = decide(max_rounds, context.comment_bodies, context.labels, context.head_sha, run_attempt_raw)

    if not decision.should_review and decision.reason.startswith("cap reached"):
        if not cap_notice_already_posted(context.comment_bodies):
            post_issue_comment(repo_name, pull_number, build_cap_notice(max_rounds))

    return decision


def write_output(decision: RoundCapDecision) -> None:
    print(f"Cody round cap decision: should_review={decision.should_review} ({decision.reason})")
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"should_review={'true' if decision.should_review else 'false'}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Decide whether Cody should review this pull request.")
    parser.add_argument("pull_number", type=int, help="The pull request number.")
    parser.add_argument("repo_name", type=str, help="The full repository name.")
    args = parser.parse_args()

    result = check_round_cap(
        args.repo_name,
        args.pull_number,
        os.environ.get("MAX_REVIEW_ROUNDS"),
        os.environ.get("RUN_ATTEMPT"),
    )
    write_output(result)
