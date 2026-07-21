from github import Github
import logging
from typing import Optional
from dataclasses import dataclass

try:
    from . import config
except ImportError:  # Support running this module as a script dependency.
    import config

@dataclass
class PullRequest:
    title: str
    description: str
    diff: str
    state: str
    created_at: str
    updated_at: str

def get_pull_request_data(repo_name: str, pull_number: int) -> Optional[PullRequest]:
    if not config.GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required to fetch pull request data.")

    try:
        logging.info(f"Fetching PR data for repo: {repo_name}, PR number: {pull_number}")
        g = Github(config.GITHUB_TOKEN)
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pull_number)

        files = pr.get_files()
        complete_diff = ""
        omitted_files = []
        ignored_paths = ['venv/', 'node_modules/', 'dist/']

        for file in files:
            if any(file.filename.startswith(path) for path in ignored_paths):
                continue
            if not file.patch:
                omitted_files.append(file.filename)
                continue

            file_diff = f"\n\nDiff for {file.filename}:\n{file.patch}\n"
            complete_diff += file_diff

        if not complete_diff:
            raise RuntimeError("No reviewable textual diff was found for this pull request.")
        if omitted_files:
            complete_diff += (
                "\n\nFiles omitted because GitHub did not provide a textual patch:\n- "
                + "\n- ".join(omitted_files)
            )

        pr_data = PullRequest(
            title=pr.title,
            description=pr.body,
            diff=complete_diff,
            state=pr.state,
            created_at=pr.created_at.isoformat(),
            updated_at=pr.updated_at.isoformat()
        )
        logging.info(f"Successfully retrieved PR data for {repo_name} PR #{pull_number}")
        return pr_data
    except Exception as exc:
        logging.error("Failed to fetch repository or pull request", exc_info=True)
        raise RuntimeError(
            f"Unable to fetch pull request data for {repo_name}#{pull_number}."
        ) from exc
