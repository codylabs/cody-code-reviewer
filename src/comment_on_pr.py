import os
import sys
from pathlib import Path
from github import Github

MAX_COMMENT_CHARS = 65_536
TRUNCATION_NOTICE = "\n\n_Review truncated because it exceeded GitHub's comment limit._"


def post_comment(repo_name, pr_number, github_token):
    output_path = Path(os.environ.get("REVIEW_OUTPUT", "output.txt"))
    if not output_path.is_file():
        raise FileNotFoundError(f"Review output was not found at {output_path}.")

    with output_path.open('r', encoding='utf-8') as file:
        comment_body = file.read()
    if len(comment_body) > MAX_COMMENT_CHARS:
        comment_body = (
            comment_body[:MAX_COMMENT_CHARS - len(TRUNCATION_NOTICE)]
            + TRUNCATION_NOTICE
        )
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
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
    post_comment(repo_name, pr_number, github_token)
