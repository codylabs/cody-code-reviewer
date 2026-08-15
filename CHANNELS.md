# Cody channel ownership

This repository is the canonical source for Cody's GitHub installation and
model-selection instructions. Other public channels should describe the
product and link here instead of copying workflow YAML or model tables.

| Channel | Canonical responsibility |
| --- | --- |
| [GitHub README](https://github.com/codylabs/cody-code-reviewer#installation) | Installation, provider selection, current inputs, and model examples |
| [GitHub Marketplace](https://github.com/marketplace/actions/cody-ai-code-reviewer) | Discoverability and the latest published release |
| [Cody documentation](https://docs.codylabs.uk/) | Product overview, privacy, and links to GitHub setup |
| [Cody Labs product page](https://codylabs.uk/private-ai-pr-reviewer/) | Positioning, real-review proof, privacy, terms, and high-intent guides |
| [Cody Pro on Polar](https://buy.polar.sh/polar_cl_1Gr4pDASt4UEK22UzlIFz5lruoxKEuG99gtL844iydI) | GitLab/Azure DevOps sales page; detailed setup ships with the product |

## Release checklist

1. Get the product, docs, and marketing PRs approved before merging any of them.
2. Merge the tested product change to `master`.
3. Publish a semantic release such as `v1.6.0`.
4. Confirm the `v1` tag moved to that release; the release workflow maintains it automatically.
5. In GitHub's release editor, select **Publish this Action to the GitHub Marketplace**.
6. Replace old release SHA pins in the README and tutorial through follow-up PRs.
7. Merge the approved docs and marketing PRs, then run the **Channel health** workflow.
8. Confirm the public sites resolve and Marketplace shows the new release.

Customer installation examples use an immutable release SHA. Portfolio
dogfooding workflows deliberately use `codylabs/cody-code-reviewer@v1` as
release canaries.

## Metadata to apply only after review

These settings cannot be changed through a repository PR. Apply them only after
the rescue PR set is approved:

- Repository description: `Private, repository-aware AI pull-request reviews in GitHub Actions. BYOK; no Cody-hosted service.`
- Repository topics: `ai-code-review`, `pull-request-review`, `github-actions`,
  `openai`, `anthropic`, `byok`, `developer-tools`
- Marketplace name: `Private AI PR Reviewer by Cody Labs`
- Marketplace description: `High-signal BYOK pull-request reviews that run privately in GitHub Actions.`
