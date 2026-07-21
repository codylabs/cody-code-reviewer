import argparse
import sys
from github_client import get_pull_request_data
from model import query_model
from typing import Optional

def review_pull_request(repo_name: str, pull_number: int) -> None:
    try:
        pr_data = get_pull_request_data(repo_name, pull_number)
        if pr_data:
            prompt = (
                "Review this pull request as a senior software engineer. "
                "Return concise GitHub-flavored Markdown without wrapping the response in a code fence. "
                "Start with 'AI Code Review by Cody (https://codylabs.pages.dev/)'. "
                "Include a 'Summary of Change' section followed by a 'Code Review' section. "
                "Prioritize correctness, security, reliability, and performance; omit low-value nitpicks. "
                "When useful, provide directly applicable code suggestions.\n\n"
                f"Title: {pr_data.title}\n"
                f"Description: {pr_data.description}\n"
                f"Changes:\n{pr_data.diff}"
            )
            response: Optional[str] = query_model(prompt)
            with open('output.txt', 'w') as file:
                file.write(response or "No response from the configured AI provider. Please try again in a few minutes.")
    except Exception as e:
        print(f"Error during review process: {str(e)}")
        # Fail the GitHub Action if there's an error
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Review a GitHub pull request.')
    parser.add_argument('pull_number', type=int, help='The pull request number.')
    parser.add_argument('repo_name', type=str, help='The full repository name.')
    args = parser.parse_args()

    review_pull_request(args.repo_name, args.pull_number)
