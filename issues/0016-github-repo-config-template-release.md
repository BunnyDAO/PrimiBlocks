---
id: 0016
title: GitHub repo configuration — Template Repo + branch protection + v0.1.0 release
type: HITL
status: open
blocked_by: [0015]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Configure `BunnyDAO/PrimiBlocks` on GitHub:

- Enable the **"Template Repository"** setting (so the "Use this template" button appears on the repo page)
- Set up `main` branch protection: require passing CI before merge, require at least one approving review for PRs
- Tag `v0.1.0` and create a GitHub Release with release notes (link to the PRD + first-30-minute-experience summary + announcement-friendly hook)
- Update the repo's About section + topics for discoverability

HITL because: settings on shared infrastructure, irreversible-ish (especially the release tag), and require account-level access.

## Acceptance criteria

- [ ] Repository's "Template Repository" toggle is enabled (verified by the "Use this template" button visible on the repo page)
- [ ] `main` branch protection: CI must pass, ≥1 approving review required
- [ ] `v0.1.0` tag exists, points at the v1 commit
- [ ] GitHub Release for `v0.1.0` exists with release notes summarizing the PRD's solution + first-30-min experience
- [ ] About section + topics set (suggested topics: `claude-code`, `templates`, `prompt-engineering`, `scaffold`, `python`)

## Blocked by

- 0015
