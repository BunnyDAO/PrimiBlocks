---
id: 0017
title: tests/ — reference kit smoke test in CI
type: AFK
status: open
blocked_by: [0010]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`tests/test_reference_kit.py` — an integration test that:

- Iterates every template in `kit/templates/`
- For each, looks up the corresponding vars in `kit/vars.example.json`
- Calls `render.render()` and asserts the output is non-empty and contains specific expected anchor substrings (per template)
- Calls `primiblocks lint` on the live kit and asserts exit 0

Runs in the standard `pytest` invocation; picked up automatically by the cross-OS matrix from 0015.

## Acceptance criteria

- [ ] `tests/test_reference_kit.py` exists
- [ ] All 3 reference templates render against `vars.example.json` and produce non-empty output
- [ ] Per-template assertions confirm the rendered output contains expected anchor substrings (proves primitives composed correctly)
- [ ] `primiblocks lint` on the live `kit/` exits 0
- [ ] Runs as part of the cross-OS CI matrix without changes to the workflow file

## Blocked by

- 0010
