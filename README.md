## About

Cody will automatically summarize and code review your changes on every pull request using OpenAI or Anthropic Claude models.

Note that an OpenAI or Anthropic API key is required, depending on the model you choose.

Read more at [https://codylabs.pages.dev/](https://codylabs.pages.dev/)

## Installation

Installation is as simple as adding your AI provider API key, and adding a Github Actions workflow file to your repo.

1. Add your OPENAI_API_KEY (or ANTHROPIC_API_KEY for Claude models) as a GitHub repo secret via Settings > Actions > Secrets and variables > New repository secret.

<img src="openai.png" alt="Open API Api Key" width="500px">

<img src="repo_secrets.png" alt="Add secrets" width="800px">

Note that GITHUB_TOKEN does not need to be added as it is available by default.

2. Create a new folder and file in your repo **.github/workflows/code_review.yml**

Copy the file from here: [cody_review.yml](https://github.com/codylabs/cody-code-reviewer/blob/master/.github/workflows/code_review.yml)

Or available below:

```
name: Automated Code Review by Cody

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  code_review:
    if: ${{ github.event.pull_request.head.repo.fork == false }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8

      - name: Clone cody-code-reviewer repository
        run: |
          git clone https://github.com/codylabs/cody-code-reviewer.git
          cd cody-code-reviewer
          # Pin to a specific release commit to ensure stability https://github.com/codylabs/cody-code-reviewer/releases/tag/v1.3.0
          git checkout 42800f56034b775ea5dedfcdf44882213e17a70c

      - name: Set up Python 3.9
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Code Review Model
        run: |
          python src/review_pull_request.py ${{ github.event.pull_request.number }} ${{ github.repository }} > ${{ github.workspace }}/output.txt
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          # Pick your model: claude-* models use your ANTHROPIC_API_KEY, anything
          # else uses your OPENAI_API_KEY. You only need the secret for the
          # provider you choose.
          # Claude models: https://platform.claude.com/docs/en/about-claude/models/overview
          # OpenAI models: https://platform.openai.com/docs/models
          MODEL: "gpt-5"

      - name: Comment on Pull Request
        run: |
          python src/comment_on_pr.py ${{ github.event.pull_request.number }} "${{ secrets.GITHUB_TOKEN }}" ${{ github.repository }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

```

3. Commit your code, create a pull request and watch Cody in action!

## Using Claude models

Cody works with Anthropic's Claude models as well as OpenAI's. To review with Claude:

1. Add ANTHROPIC_API_KEY as a repo secret (create a key at https://platform.claude.com/).
2. Set MODEL to a Claude model in the "Run Code Review Model" step of your workflow:

```
      - name: Run Code Review Model
        run: |
          python src/review_pull_request.py ${{ github.event.pull_request.number }} ${{ github.repository }} > ${{ github.workspace }}/output.txt
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          MODEL: "claude-opus-4-8"
```

Any model name starting with claude- is sent to Anthropic; anything else goes to OpenAI, so you only need the API key for the provider you pick.

| Model | Best for |
| --- | --- |
| claude-opus-4-8 | The most capable reviews — recommended |
| claude-sonnet-5 | Near-Opus quality at lower cost |
| claude-haiku-4-5 | Fastest and cheapest |

The full model list is at https://platform.claude.com/docs/en/about-claude/models/overview.

## GitLab & Azure DevOps (Cody Pro)

Cody Pro brings the same AI code reviews to GitLab merge requests and Azure DevOps pull requests, with ready-made pipeline templates for both platforms and support for the same OpenAI and Claude models. It's a one-time purchase:

**[Get Cody Pro on Gumroad](https://codylabs.gumroad.com/l/cody-pro)**

<img src="cody_review_2.png" alt="PR Code Review Image" width="640px">

<img src="cody_review_1.png" alt="PR Code Review Image" width="640px">

## Development

Clone the repo.

Note venv (virtual environment) is used to ensure that versions etc are specific to this repo.

`python -m venv venv` and
`pip install -r requirements.txt`

To activiate:
`source venv/bin/activate`

To deactivate:
`deactivate`

### Testing

Create an .env:

```
OPENAI_API_KEY=token_here
GITHUB_TOKEN=token_here
GITLAB_TOKEN=your_gitlab_token_here
```

And then run:

`PYTHONPATH=src pytest -s tests/`

## License

See the LICENSE.md file for details.

## Contributing

Contributions are welcome! Whether it's submitting issues, suggesting improvements, or contributing code, we appreciate your input.

Please note that while this project is currently open for contributions, it is not open source. There may be an enterprise plan available in the future that will include additional features and support.

Feel free to reach out by [opening an issue](https://github.com/codylabs/cody-code-reviewer/issues) if you have any questions or ideas.
