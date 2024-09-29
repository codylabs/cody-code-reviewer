## About

With no coding required to set up, Cody will automatically summarize and code review your changes on every pull request or merge request using AI.

Read more at [https://codylabs.io/](https://codylabs.io/)

## Installation

Installation is as simple as adding your open API key, and creating a Github Actions workflow file to your repo.

If you prefer you can watch these steps on YouTube:

1. Add OPENAI_API_KEY as a github repo secret via Settings > Actions > Secrets and variables > New reposity secret. The variable name should be OPENAI_API_KEY and the value should be your Open API API Key.

![alt text](add_a_secret_image.png)

Note that GITHUB_TOKEN does not need to be added as is available by default.

2. Add the following to a new folder in your repo .github/workflows/code_review.yml

```
name: Code Review by Cody

permissions:
  contents: read
  pull-requests: write

on:
  pull_request:
  pull_request_review_comment:
    types: [created]

concurrency:
  group: ${{ github.repository }}-${{ github.event.number || github.head_ref || github.sha }}-${{ github.workflow }}-${{ github.event_name == 'pull_request_review_comment' && 'pr_comment' || 'pr' }}
  cancel-in-progress: ${{ github.event_name != 'pull_request_review_comment' }}

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Use Cody AI Code Review Tool
        uses: codylabs/cody-code-reviewer@master
        with:
          pr_number: ${{ github.event.pull_request.number }}
          repository: ${{ github.repository }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

3. Commit your code and watch Cody in action!

## Development

Clone the repo.

Note venv (virtual environment) is used so ensure that versions etc are specific to this repo.

`python -m venv venv` and
`pip install -r requirements.txt`

To activiate
`source venv/bin/activate`

To deactivate, `deactivate`

### Testing

Create an .env

```
OPENAI_API_KEY=token_here
GITHUB_TOKEN=token_here
GITLAB_TOKEN=your_gitlab_token_here
```

And then run

`PYTHONPATH=src pytest -s tests/`

This will run the code review logic on an GitHub Pull Request and log the output.
