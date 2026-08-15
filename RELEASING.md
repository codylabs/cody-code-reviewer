# Releasing Cody

Checklist for every release of the GitHub Action, and the propagation surfaces that go
stale silently when skipped. Added 2026-08-03 after the context-defaults incident: the
minimal-workflow crash shipped for weeks because nothing tied releases to the places that
describe or embed the action.

## 1. Release the action (this repo)

- [ ] PR merged to master with a Cody review on it (dogfooding is the first smoke test).
- [ ] `python3 -m pytest` green.
- [ ] `gh release create vX.Y.Z --target <sha>` with honest notes.
- [ ] Move the `v1` tag: `git tag -f v1 <sha> && git push -f origin v1`.
- [ ] Bump the SHA pin (`uses: codylabs/cody-code-reviewer@<sha> # vX.Y.Z`) in:
  - [ ] This repo's own `.github/workflows/code_review.yml` (self-review dogfoods the new
        release; it deliberately pins rather than tracking `v1` so PR-controlled code
        cannot run in review context).
  - [ ] README examples (both the OpenAI and Claude blocks). SHA pinning is the
        documented default; `@v1` is mentioned only as the auto-update alternative.

## 2. Docs and marketing surfaces

- [ ] docs.codylabs.uk (repo `daviddigital/codylabs`, Docusaurus, auto-deploys on push to
      master): the GitHub Actions tutorial blog post embeds a full workflow with the
      pinned SHA; update it. `docs/intro.md` only links to the GitHub README, which is
      why the README stays the single install source: keep it that way.
- [ ] codylabs.uk (repo `~/projects/codylabs-portfolio`): links to the GitHub README, no
      embedded snippet. Nothing to do unless a release changes the pitch (model support,
      pricing). Deploy gate: `node business/check.mjs check`, push to main.

## 3. Distributions that share the review engine (separate release trains)

The GitLab and Azure DevOps products do NOT consume this action; behavior fixes here
usually need porting there:

- [ ] `codylabs/cody-pro` (GitLab MR + Azure DevOps scripts, Python, sold via Polar, one-time
      US$39: https://buy.polar.sh/polar_cl_1Gr4pDASt4UEK22UzlIFz5lruoxKEuG99gtL844iydI):
      active branch is `feat/azure-marketplace-extension`, not main. Port prompt/header/
      output-format changes; its customers install by script, so README + Polar listing
      copy may also need the same doc updates.
- [ ] `codylabs/cody-pro-azure-devops` (VS Marketplace extension, BYOL): port the same
      changes; bump `vss-extension.json` AND `task.json` versions together (Marketplace
      versions are immutable, roll forward, never re-upload); publishing to the
      Marketplace is a separate manual step after merge.
- [ ] Portfolio dogfooding repos (19 `daviddigital/*` + `codylabs/*` workflows) track
      `@v1` DELIBERATELY so every release is exercised on real PRs immediately: do not
      "fix" them to SHA pins; they are the canary, not a customer surface.

## 4. Post-release verification

- [ ] Open or re-run a review on a real PR in a repo using the MINIMAL workflow (no
      pr_number/repository/github_token inputs) and confirm the review posts with the
      correct model named in the header.
- [ ] `codylabs/cody-github-smoke-canary` run green.
