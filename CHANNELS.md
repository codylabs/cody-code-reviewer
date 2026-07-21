# Cody channel ownership

This repository is the canonical source for Cody's GitHub installation and
model-selection instructions. Other public channels should describe the
product and link here instead of copying workflow YAML or model tables.

| Channel | Canonical responsibility |
| --- | --- |
| [GitHub README](https://github.com/codylabs/cody-code-reviewer#installation) | Installation, provider selection, current inputs, and model examples |
| [GitHub Marketplace](https://github.com/marketplace/actions/cody-ai-code-reviewer) | Discoverability and the latest published release |
| [Cody documentation](https://docs.codylabs.uk/) | Product overview, privacy, and links to GitHub setup |
| [Cody Labs marketing site](https://codylabs.uk/) | Short product positioning and links to GitHub, Marketplace, docs, and Gumroad |
| [Cody Pro on Gumroad](https://codylabs.gumroad.com/l/cody-pro) | GitLab/Azure DevOps sales page; detailed setup ships with the product |

## Release checklist

1. Merge a tested change to `master`.
2. Publish a semantic release such as `v1.3.2`.
3. Confirm the `v1` tag moved to that release; the release workflow maintains it automatically.
4. In GitHub's release editor, select **Publish this Action to the GitHub Marketplace**.
5. Run the **Channel health** workflow and confirm the public sites resolve and Marketplace shows the release.

The public installation examples use `codylabs/cody-code-reviewer@v1`, so patch
and minor releases do not require copies of workflow YAML to be updated across
the website and documentation.
