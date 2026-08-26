# Private AI PR Reviewer by Cody Labs

High-signal pull request reviews using your choice of OpenAI or Anthropic model.
Cody runs inside your GitHub Actions job and sends the diff directly to the model
provider using your API key. The inspected, unmodified Action contains no Cody Labs
review-service integration, account requirement, or per-seat subscription. Like any
third-party Action, its code and installed dependencies run with access to the
environment values and token you provide.

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Private_AI_PR_Reviewer-0969da?logo=github)](https://github.com/marketplace/actions/cody-ai-code-reviewer)
[![Test](https://github.com/codylabs/cody-code-reviewer/actions/workflows/test.yml/badge.svg)](https://github.com/codylabs/cody-code-reviewer/actions/workflows/test.yml)
[![Latest release](https://img.shields.io/github/v/release/codylabs/cody-code-reviewer)](https://github.com/codylabs/cody-code-reviewer/releases/latest)

## Why this reviewer

- **Private execution:** your code goes from your GitHub runner to the model provider
  you select. Cody Labs does not receive or store it.
- **Bring your own key:** pay the provider's API price instead of another per-developer
  subscription.
- **Repository-aware:** Cody reads `AGENTS.md`, `REVIEW.md`, `CLAUDE.md`, and
  `.github/copilot-instructions.md` from the trusted base commit when present.
- **High signal by default:** findings prioritize correctness, security, reliability,
  and performance, with severity, impact, and a concrete fix.
- **No timeline spam:** later pushes update Cody's existing review comment.
- **Cost control:** exclude generated paths and cap the amount of diff sent for review.

This project dogfoods its own Action. In
[this real review](https://github.com/codylabs/cody-code-reviewer/pull/24#issuecomment-5157065670),
Cody caught a workflow change that could have exposed repository secrets to
pull-request-controlled code.

## Install

1. Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` under
   **Settings → Secrets and variables → Actions**.
2. Create `.github/workflows/cody-review.yml`:

```yaml
name: Private AI PR Review

on:
  # This event runs the workflow definition from the protected base branch.
  # Cody never checks out or executes pull-request code.
  pull_request_target:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Review pull request
        uses: codylabs/cody-code-reviewer@5ec18da9b75541f5ce2b33edcfb8a7c666551b31 # v1.7.0
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          model: gpt-5.6-luna
```

Commit the workflow and open a pull request. Cody posts a review and updates that same
comment whenever the pull request changes.

The example pins an immutable release commit so the Action cannot change underneath
you. New release SHAs are published on the
[releases page](https://github.com/codylabs/cody-code-reviewer/releases). You can use
`codylabs/cody-code-reviewer@v1` instead if you prefer automatic compatible updates.

## Use Claude

Replace the provider inputs in the install example:

```yaml
      - name: Review pull request
        uses: codylabs/cody-code-reviewer@5ec18da9b75541f5ce2b33edcfb8a7c666551b31 # v1.7.0
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-opus-4-8
```

Model names beginning with `claude` use Anthropic. Other model names use OpenAI.

## Tailor reviews to your repository

Cody automatically reads these files from the pull request's **base commit**, so a pull
request cannot alter its own review rules:

- `AGENTS.md`
- `REVIEW.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`

You can also set priorities directly in the workflow:

```yaml
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          model: gpt-5.6-luna
          review_instructions: |
            Treat authorization and tenant isolation as release blockers.
            Ignore formatting unless it changes behavior.
          exclude_paths: "dist/**,**/dist/**,docs/generated/**,**/*.min.js"
          max_diff_chars: "120000"
```

## Capping review rounds

Cody reviews again on every push to a pull request. That is usually productive, but a
fix-push-review loop has no natural stopping point on its own, and on a long back-and-forth
it can run for hours. Set `max_review_rounds` to stop it after a fixed number of reviews:

```yaml
      - name: Review pull request
        uses: codylabs/cody-code-reviewer@5ec18da9b75541f5ce2b33edcfb8a7c666551b31 # v1.7.0
        with:
          openai_api_key: ${{ secrets.OPENAI_API_KEY }}
          model: gpt-5.6-luna
          max_review_rounds: 2
```

`max_review_rounds` defaults to `0`, which means unlimited: today's behavior, unchanged for
any workflow that does not set it. Once Cody has posted that many reviews on a pull request,
it skips the review on the next push, exits successfully (a skipped review is not a failed
check), and posts a short note once explaining the cap was reached and how to get another
review. It does not repeat that note on every push after.

Round counting reads a hidden marker Cody embeds in each review it posts (an HTML comment,
invisible when rendered), not the visible header text, since that text can change between
versions or be edited. A pull request with reviews from before this feature shipped, which
predate the marker, still counts each of those older reviews toward the cap; Cody says so in
the cap note when that applies.

Cody also skips a review outright, cap or no cap, when the pull request's head commit has
not changed since its last review: nothing new to look at. Reviews from before this feature
shipped do not record a head sha, so this check only takes effect once at least one review
carrying the marker has been posted.

To get one more review despite the cap, add the `cody:force-review` label to the pull
request, or re-run the workflow manually. Either one grants exactly one more review, even
if the head commit has not changed; it is not a standing bypass, so a label left on the
pull request stops helping once that one extra review has been posted, and repeated manual
re-runs of the same workflow run do not stack.

## Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `openai_api_key` | — | Required for OpenAI models |
| `anthropic_api_key` | — | Required for Claude models |
| `model` | `gpt-5.6-luna` | Provider model ID |
| `max_review_rounds` | `0` (unlimited) | Stop reviewing a pull request after this many reviews |
| `review_instructions` | empty | Extra priorities supplied by the workflow owner |
| `exclude_paths` | dependency/build directories | Comma-separated path globs |
| `context_files` | common instruction files | Comma-separated trusted guidance files |
| `max_diff_chars` | `200000` | Hard cap on diff characters sent to the model |
| `update_existing_comment` | `true` | Update the previous Cody review instead of adding another |
| `pr_number` | current PR | Override for non-standard workflows |
| `repository` | current repository | Override target as `owner/name` |
| `github_token` | workflow token | Token used to read and comment on the PR |

## Security and privacy

Cody Labs does not operate a review backend. The Action runs on the selected GitHub
runner and calls OpenAI or Anthropic directly. Your chosen provider's API terms and data
handling apply.

For supply-chain-sensitive repositories:

- keep the Action pinned to a full release SHA;
- use `pull_request_target` and never add a checkout or execute pull-request-controlled
  code in the secret-bearing review job;
- keep `contents: read` and `pull-requests: write` as the only job permissions;
- keep review guidance on the protected base branch.
- protect the default branch and require owner/CODEOWNERS review for changes to the
  secret-bearing workflow and dependency pins; collaborators who can modify the base
  workflow can modify what executes with its secrets.

See [SECURITY.md](SECURITY.md) for reporting and supported-version details.

## GitLab and Azure DevOps

[Cody Pro](https://buy.polar.sh/polar_cl_W4b0Q17WmOuaYMK74997DoQmQa7P8K7o0jppV18t1f0) packages
the same private, BYOK workflow for GitLab merge requests and Azure DevOps pull requests. It is
a one-time US$39 purchase, not a subscription.

## Development

```sh
python -m venv venv
source venv/bin/activate
pip install --require-hashes -r requirements-dev.lock
python -m pytest -m "not integration"
```

When dependencies change, regenerate `requirements.lock` and
`requirements-dev.lock` with the commands documented in [RELEASING.md](RELEASING.md).

## Licence and contributions

Cody is **source-available and free to use**, but it is not OSI open source. The current
licence permits personal, internal business, and commercial use while restricting
redistribution. See [LICENSE.md](LICENSE.md).

Bug reports and focused improvements are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
