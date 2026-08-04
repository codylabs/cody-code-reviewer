import os
from github import Github
import logging
from typing import List, Optional
from dataclasses import dataclass

try:
    from . import config
except ImportError:  # Support running this module as a script dependency.
    import config

MAX_DIFF_CHARS = int(os.getenv("MAX_DIFF_CHARS", "200000"))
MAX_DESCRIPTION_CHARS = int(os.getenv("MAX_DESCRIPTION_CHARS", "20000"))
MAX_OMITTED_FILE_NAMES = 20


def truncate_with_notice(text: str, limit: int, notice: str) -> str:
    """Bound text to a hard limit while retaining a clear truncation notice."""
    if len(text) <= limit:
        return text
    if limit <= len(notice):
        return notice[:limit]
    return text[:limit - len(notice)] + notice

@dataclass
class PullRequest:
    title: str
    description: str
    diff: str
    state: str
    created_at: str
    updated_at: str
    head_sha: str


@dataclass
class PullRequestContext:
    head_sha: str
    labels: List[str]
    comment_bodies: List[str]

def get_pull_request_data(repo_name: str, pull_number: int) -> Optional[PullRequest]:
    if not config.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to fetch pull request data.")

    try:
        logging.info(f"Fetching PR data for repo: {repo_name}, PR number: {pull_number}")
        g = Github(config.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pull_number)

        files = pr.get_files()
        diff_parts = []
        diff_length = 0
        diff_truncated = False
        omitted_files = []
        ignored_paths = ['venv/', 'node_modules/', 'dist/']

        for file in files:
            if any(file.filename.startswith(path) for path in ignored_paths):
                continue
            if not file.patch:
                omitted_files.append(file.filename)
                continue

            file_diff = f"\n\nDiff for {file.filename}:\n{file.patch}\n"
            remaining = MAX_DIFF_CHARS - diff_length
            if remaining <= 0:
                diff_truncated = True
                break
            if len(file_diff) > remaining:
                diff_parts.append(file_diff[:remaining])
                diff_length += remaining
                diff_truncated = True
                break
            diff_parts.append(file_diff)
            diff_length += len(file_diff)

        complete_diff = "".join(diff_parts)
        if not complete_diff:
            raise RuntimeError("No reviewable textual diff was found for this pull request.")
        if omitted_files:
            displayed_files = omitted_files[:MAX_OMITTED_FILE_NAMES]
            omitted_summary = (
                "\n\nFiles omitted because GitHub did not provide a textual patch:\n- "
                + "\n- ".join(displayed_files)
            )
            remaining_count = len(omitted_files) - len(displayed_files)
            if remaining_count:
                omitted_summary += f"\n- ... and {remaining_count} more omitted files"
            complete_diff += omitted_summary
        if diff_truncated:
            complete_diff += "\n\n[Diff truncated because it exceeded the review size limit.]"
        complete_diff = truncate_with_notice(
            complete_diff,
            MAX_DIFF_CHARS,
            "\n\n[Review data truncated because it exceeded the review size limit.]",
        )

        description = pr.body or ""
        description = truncate_with_notice(
            description,
            MAX_DESCRIPTION_CHARS,
            "\n\n[Description truncated because it exceeded the review size limit.]",
        )

        pr_data = PullRequest(
            title=pr.title,
            description=description,
            diff=complete_diff,
            state=pr.state,
            created_at=pr.created_at.isoformat(),
            updated_at=pr.updated_at.isoformat(),
            head_sha=pr.head.sha,
        )
        logging.info(f"Successfully retrieved PR data for {repo_name} PR #{pull_number}")
        return pr_data
    except Exception as exc:
        logging.error("Failed to fetch repository or pull request", exc_info=True)
        raise RuntimeError(
            f"Unable to fetch pull request data for {repo_name}#{pull_number}."
        ) from exc


def get_pull_request_context(repo_name: str, pull_number: int) -> PullRequestContext:
    """Fetch the state needed to decide whether Cody should review again:
    the current head SHA, the pull request's labels (for the cap override),
    and the body of every issue comment already posted (to count rounds and
    check whether the cap notice already went out)."""
    if not config.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to fetch pull request data.")

    try:
        g = Github(config.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pull_number)
        labels = [label.name for label in pr.get_labels()]
        comment_bodies = [comment.body or "" for comment in pr.get_issue_comments()]
        return PullRequestContext(
            head_sha=pr.head.sha,
            labels=labels,
            comment_bodies=comment_bodies,
        )
    except Exception as exc:
        logging.error("Failed to fetch pull request context", exc_info=True)
        raise RuntimeError(
            f"Unable to fetch pull request context for {repo_name}#{pull_number}."
        ) from exc


def post_issue_comment(repo_name: str, pull_number: int, body: str) -> None:
    """Post a plain issue comment on the pull request, used for the one-off
    cap-reached notice. The full AI review is posted separately by
    comment_on_pr.py from the review output file."""
    if not config.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to post a pull request comment.")

    g = Github(config.GITHUB_TOKEN)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pull_number)
    pr.create_issue_comment(body)
