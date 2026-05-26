---
id: 0015
title: CI — cross-OS pytest matrix (mac/linux/win × Python 3.11/3.12)
type: AFK
status: done
blocked_by: [0001]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`.github/workflows/test.yml` — GitHub Actions workflow that:

- Runs on push and pull_request
- Matrix: `os: [macos-latest, ubuntu-latest, windows-latest]` × `python-version: [3.11, 3.12]`
- Steps: checkout → setup-python → `pip install -e .[dev]` → `pytest` → upload junit XML on failure
- All 6 matrix cells must pass for the workflow to succeed

Plus a smoke-test step (separate job within the same workflow, or a second workflow file) that runs `primiblocks doctor` against the freshly-installed package on each matrix cell, asserting green.

## Acceptance criteria

- [ ] `.github/workflows/test.yml` exists and is syntactically valid
- [ ] All 6 matrix cells (3 OSes × 2 Python versions) run successfully against the current codebase
- [ ] Install time from `pip install -e .[dev]` to first `pytest` invocation is < 2 minutes on each OS
- [ ] `primiblocks doctor` reports green on each matrix cell

## Blocked by

- 0001
