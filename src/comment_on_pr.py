import os
import sys
from pathlib import Path
from github import Github

MAX_COMMENT_CHARS = 65_536
TRUNCATION_NOTICE = "\n\n_Review truncated because it exceeded GitHub's comment limit._"
REVIEW_MARKER = "<!-- codylabs-private-pr-review -->"


def with_review_marker(comment_body: str) -> str:
    """Add a stable invisible marker so later runs can replace this review."""
    if comment_body.startswith(REVIEW_MARKER):
        return comment_body
    return f"{REVIEW_MARKER}\n{comment_body}"


def find_existing_review_comment(pull_request):
    """Return Cody's existing bot-authored comment, if this PR has one."""
    for comment in pull_request.get_issue_comments():
        login = getattr(getattr(comment, "user", None), "login", "")
        if REVIEW_MARKER in (comment.body or "") and login.endswith("[bot]"):
            return comment
    return None


def post_comment(repo_name, pr_number, github_token, update_existing=True):
    output_path = Path(os.environ.get("REVIEW_OUTPUT", "output.txt"))
    if not output_path.is_file():
        raise FileNotFoundError(f"Review output was not found at {output_path}.")

    with output_path.open('r', encoding='utf-8') as file:
        comment_body = file.read()
    available_body_chars = MAX_COMMENT_CHARS - len(REVIEW_MARKER) - 1
    if len(comment_body) > available_body_chars:
        comment_body = (
            comment_body[:available_body_chars - len(TRUNCATION_NOTICE)]
            + TRUNCATION_NOTICE
        )
    comment_body = with_review_marker(comment_body)
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    if update_existing:
        existing_comment = find_existing_review_comment(pr)
        if existing_comment:
            existing_comment.edit(comment_body)
            return
    pr.create_issue_comment(comment_body)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python comment_on_pr.py <pr_number> <repo_name>")
        sys.exit(1)

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("GITHUB_TOKEN is required to post a pull request comment.")
        sys.exit(1)

    pr_number = int(sys.argv[1])
    repo_name = sys.argv[2]
    try:
        from .config import should_update_existing_comment
    except ImportError:
        from config import should_update_existing_comment
    post_comment(
        repo_name,
        pr_number,
        github_token,
        update_existing=should_update_existing_comment(),
    )
