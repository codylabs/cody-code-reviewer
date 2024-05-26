import sys
from github import Github
import logging
import config
from typing import Optional
from dataclasses import dataclass

# Configure detailed logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler("debug.log"),
                        logging.StreamHandler()
                    ])

# Load the GitHub token from an environment variable
GITHUB_TOKEN = config.GITHUB_TOKEN
if not GITHUB_TOKEN:
    logging.error("GitHub token is not set. Please configure GITHUB_TOKEN environment variable.")
    sys.exit(1)

g = Github(GITHUB_TOKEN)

@dataclass
class PullRequest:
    title: str
    description: str
    diff: str
    state: str
    created_at: str
    updated_at: str

def get_pull_request_data(repo_name: str, pull_number: int) -> Optional[PullRequest]:
    try:
        logging.info(f"Fetching PR data for repo: {repo_name}, PR number: {pull_number}")
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pull_number)

        files = pr.get_files()
        complete_diff = ""
        ignored_paths = ['venv/', 'node_modules/', 'dist/']

        for file in files:
            if any(file.filename.startswith(path) for path in ignored_paths):
                continue

            file_diff = f"\n\nDiff for {file.filename}:\n{file.patch}\n"
            complete_diff += file_diff

        if not complete_diff: 
            return None

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
    except Exception as e:
        logging.error("Failed to fetch repository or pull request", exc_info=True)
        return None
