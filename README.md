## Development

Clone the repo.

Note venv (virtual environment) is used so ensure that versions etc are specific to this repo.

`python -m venv venv` and
`pip install -r requirements.txt`

To activiate
`source venv/bin/activate`

To deactivate, `deactivate`

## Testing

Will use code_reivew.yml to test using cody on this repo

Create an .env

`OPENAI_API_KEY=token_here
GITHUB_TOKEN=token_here
GITLAB_TOKEN=your_gitlab_token_here`

`PYTHONPATH=src pytest -s tests/`
