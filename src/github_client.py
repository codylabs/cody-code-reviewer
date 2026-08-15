import os
import re
from functools import lru_cache
from github import Github
from github.GithubException import GithubException
import logging
from typing import List, Optional
from dataclasses import dataclass

try:
    from . import config
except ImportError:  # Support running this module as a script dependency.
    import config

MAX_DIFF_CHARS = config.get_positive_int("MAX_DIFF_CHARS", 200_000)
MAX_DESCRIPTION_CHARS = int(os.getenv("MAX_DESCRIPTION_CHARS", "20000"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "40000"))
MAX_CONTEXT_FILE_CHARS = 16000
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
    context: str
    state: str
    created_at: str
    updated_at: str
    head_sha: str


@dataclass
class PullRequestContext:
    head_sha: str
    labels: List[str]
    comment_bodies: List[str]


_GLOBSTAR = "**"


def _translate_path_segment(segment: str) -> str:
    """Translate one path segment (never containing '/') to a regex fragment.
    '*' and '?' are bounded to this segment; they must not match '/'."""
    pieces = []
    for char in segment:
        if char == "*":
            pieces.append("[^/]*")
        elif char == "?":
            pieces.append("[^/]")
        else:
            pieces.append(re.escape(char))
    return "".join(pieces)


@lru_cache(maxsize=None)
def _compile_glob(pattern: str) -> re.Pattern:
    """Translate a shell-style glob into a regex anchored to the full path.

    Written by hand instead of using PurePosixPath.match(): that method
    treats '**' as a non-recursive '*' on every Python version (only
    full_match() in 3.13+ does recursive '**'), and it right-anchors
    relative patterns instead of matching the whole path. Together those
    mean the default pattern 'node_modules/**' never excludes anything
    nested more than one level deep, e.g. node_modules/lodash/index.js is
    not excluded even though it obviously should be.

    Semantics: '**' is recursive, and matches zero or more path segments,
    only when it stands alone as an entire path segment: 'a/**/b' matches
    'a/b' as well as 'a/x/y/b', and 'a/**' also matches plain 'a'. Anywhere
    else, '*' and '?' behave like normal shell globbing and never cross a
    '/'.
    """
    segments = pattern.split("/")

    # Collapse a run of consecutive '**' segments (e.g. from '**/**') into
    # a single globstar node.
    nodes: list[tuple[str, str]] = []  # ("lit", regex) or ("glob", "")
    i = 0
    while i < len(segments):
        segment = segments[i]
        if segment == _GLOBSTAR:
            while i < len(segments) and segments[i] == _GLOBSTAR:
                i += 1
            nodes.append(("glob", ""))
        else:
            nodes.append(("lit", _translate_path_segment(segment)))
            i += 1

    parts = []
    for index, (kind, regex) in enumerate(nodes):
        if kind == "lit":
            if parts and nodes[index - 1][0] == "lit":
                parts.append("/")
            parts.append(regex)
            continue

        is_start = index == 0
        is_end = index == len(nodes) - 1
        if is_start and is_end:
            # The whole pattern is '**': match anything, including nothing.
            parts.append(".*")
        elif is_start:
            # '**/...': zero or more leading directories, including none.
            parts.append("(?:.*/)?")
        elif is_end:
            # '.../**': zero or more trailing directories, including none.
            parts.append("(?:/.*)?")
        else:
            # '.../**/...': zero or more directories between two literal
            # segments, including none, e.g. 'a/**/b' also matches 'a/b'.
            parts.append("(?:/.*)?/")

    return re.compile("^" + "".join(parts) + "$")


def path_is_excluded(filename: str, patterns: tuple[str, ...]) -> bool:
    """Match a repository-relative POSIX path against caller glob patterns."""
    return any(_compile_glob(pattern).match(filename) for pattern in patterns)


def get_trusted_review_context(repo, pull_request) -> str:
    """Read review guidance from the PR's base commit, never its untrusted head."""
    base_sha = getattr(getattr(pull_request, "base", None), "sha", None)
    if not base_sha:
        return ""

    context_parts = []
    total_chars = 0
    for path in config.get_context_files():
        try:
            content = repo.get_contents(path, ref=base_sha)
        except GithubException as exc:
            if exc.status != 404:
                logging.warning("Unable to read review context file %s: %s", path, exc)
            continue
        except Exception as exc:
            logging.warning("Unable to read review context file %s: %s", path, exc)
            continue

        if isinstance(content, list):
            continue
        decoded = content.decoded_content.decode("utf-8", errors="replace")
        decoded = truncate_with_notice(
            decoded,
            MAX_CONTEXT_FILE_CHARS,
            "\n[Context file truncated.]",
        )
        section = f"\n\nReview guidance from {path}:\n{decoded}"
        remaining = MAX_CONTEXT_CHARS - total_chars
        if remaining <= 0:
            break
        context_parts.append(section[:remaining])
        total_chars += min(len(section), remaining)

    return "".join(context_parts)

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
        excluded_files = []
        exclude_patterns = config.get_exclude_paths()

        for file in files:
            if path_is_excluded(file.filename, exclude_patterns):
                excluded_files.append(file.filename)
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
        if excluded_files:
            displayed_files = excluded_files[:MAX_OMITTED_FILE_NAMES]
            excluded_summary = (
                "\n\nFiles excluded by review configuration:\n- "
                + "\n- ".join(displayed_files)
            )
            remaining_count = len(excluded_files) - len(displayed_files)
            if remaining_count:
                excluded_summary += f"\n- ... and {remaining_count} more excluded files"
            complete_diff += excluded_summary
        if not complete_diff:
            raise RuntimeError("No changed files or textual patches were found for this pull request.")
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
        context = get_trusted_review_context(repo, pr)

        pr_data = PullRequest(
            title=pr.title,
            description=description,
            diff=complete_diff,
            context=context,
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
