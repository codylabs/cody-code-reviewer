import argparse
import sys
from github_client import get_pull_request_data
from model import query_openai
from typing import Optional

def review_pull_request(repo_name: str, pull_number: int) -> None:
    try:
        pr_data = get_pull_request_data(repo_name, pull_number)
        if pr_data:
            prompt = (
                f"Review this code like a senior software engineer at Google. "
                f"Respond in a clear and concise github format with relevant headings (supports markdown) but do not start with ```markdown as it will break the github formatting. Start your reponse with 'AI Code Review by Cody (https://codylabs.io/)', a summary of the change under the heading 'Summary of Change', and then jump straight into a standard code review under the heading 'Code Review'. Be concise, focus on important aspects such as functionality and security and ignore nitpicks where possible. Provide code suggestions using markdown format."
                f"Title: {pr_data.title}\nDescription: {pr_data.description}\Changes: {pr_data.diff}"
            )
            response: Optional[str] = query_openai(prompt)
            with open('output.txt', 'w') as file:
                file.write(response or "No response from OpenAI, please try again in a few minutes.")
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
