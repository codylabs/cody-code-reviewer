# Security policy

## Supported versions

Security fixes are released on the latest `v1` release line. Consumers that pin an
immutable commit SHA should update to the SHA published with the latest release.

## Report a vulnerability

Please use GitHub's private vulnerability reporting for this repository:

https://github.com/codylabs/cody-code-reviewer/security/advisories/new

Do not open a public issue for suspected credential exposure, prompt-injection bypasses,
unsafe pull-request workflow examples, or dependency vulnerabilities.

Include the affected version or commit, impact, reproduction steps, and any proposed
mitigation. Cody Labs will acknowledge a report within three business days and will
coordinate disclosure after a fix is available.

## Deployment boundary

The Action runs inside the consumer's GitHub Actions job. It reads the pull request
through GitHub's API, sends review material directly to the selected OpenAI or Anthropic
API, and posts the resulting review through GitHub's API. The inspected, unmodified
Action contains no integration that intentionally sends repository code, API keys, or
review output to a Cody Labs-operated service. The Action code and all installed
dependencies necessarily run with process-level access to the supplied secrets.

Consumers are responsible for selecting a model provider, configuring that provider's
data controls, choosing an appropriate runner, and limiting the workflow token's
permissions. Protect the base branch and require owner or CODEOWNERS review for changes
to the secret-bearing workflow and dependency pins.
