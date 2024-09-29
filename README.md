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
name: Automated Code Review by Cody

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  code_review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python 3.9
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Clone Cody Code Reviewer Repository
        run: |
          git clone https://github.com/codylabs/cody-code-reviewer.git cody-code-reviewer

      - name: Run Code Review Model
        run: |
          python cody-code-reviewer/src/review_pull_request.py ${{ github.event.pull_request.number }} ${{ github.repository }} > ${{ github.workspace }}/output.txt
        env:
          # This is provided by default, you do not need to add this this
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Update the below in your GitHub repo actions secrets to use your OpenAI API key
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          # Update the below to use the model of your choice
          OPENAI_MODEL: "gpt-4o"

      - name: Display Review Result
        run: |
          printf "Review result:\n%s" "${{ env.REVIEW_RESULT }}"

      - name: Comment on Pull Request
        if: failure() # Runs if any of the previous steps failed
        run: |
          python cody-code-reviewer/src/comment_on_pr.py ${{ github.event.pull_request.number }} "${{ secrets.GITHUB_TOKEN }}" ${{ github.repository }}

        env:
          # This is provided by default, you do not need to add this this
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

permissions:
  contents: read
  pull-requests: write
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
