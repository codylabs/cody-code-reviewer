import sys
from github import Github

def post_comment(repo_name, pr_number, github_token):
    with open('output.txt', 'r') as file:
        comment_body = file.read()
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(comment_body)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python comment_on_pr.py <pr_number> <github_token> <repo_name>")
        sys.exit(1)

    pr_number = int(sys.argv[1])
    github_token = sys.argv[2]
    repo_name = sys.argv[3]
    post_comment(repo_name, pr_number, github_token)
