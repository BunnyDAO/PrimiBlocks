---
id: 0014
title: SOP.md + 4 diagrams (effective contract, /primi-fill flow, /primi-author flow, module dep graph)
type: HITL
status: done
blocked_by: []
parent: docs/prd/primiblocks-v1.md
---

## What to build

`SOP.md` — the full operating procedure, split into two reader paths (mirroring HITL's SOP pattern):

- **Non-developer path** — for a user running `/primi-fill` against a kit someone else built (assumes Claude Code is installed). Covers picking a template, walking the contract, previewing/writing artifacts.
- **Developer path** — for someone building a new domain kit. Covers contract grammar reference, composition model, CLI subcommand reference, both skills' UX, the linter, and the `doctor` checklist.

References 4 committed SVG diagrams (`.excalidraw` source in `docs/diagrams/src/`):

- `docs/diagrams/effective-contract-aggregation.svg` — template vars + primitive A vars + primitive B vars → effective contract, with the collision-override case explicitly called out
- `docs/diagrams/primi-fill-flow.svg` — the 7-step skill flow
- `docs/diagrams/primi-author-flow.svg` — the composition / request-filing skill flow
- `docs/diagrams/renderer-module-dep-graph.svg` — `errors` → `contract` → `{primitives, templates}` → `render` → `cli`

**Quality bar:** beautiful, professional. NO mermaid blocks. NO ASCII art.

HITL because: SOP completeness + visual quality bar.

## Acceptance criteria

- [ ] `SOP.md` renders cleanly on GitHub
- [ ] Both reader paths (non-developer + developer) are clearly delineated with a table-of-contents at the top
- [ ] All 4 diagrams render inline on GitHub
- [ ] All 4 diagrams' `.excalidraw` source files are committed under `docs/diagrams/src/`
- [ ] CLI subcommand reference covers every subcommand from 0007 + 0008
- [ ] Contract grammar reference covers every field from 0002 + 0003
- [ ] `doctor` troubleshooting checklist covers the failures `doctor` itself reports
- [ ] No mermaid code blocks anywhere
- [ ] No ASCII-art diagrams anywhere

## Blocked by

None — can start immediately.
