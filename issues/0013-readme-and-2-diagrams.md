---
id: 0013
title: README.md + 2 diagrams (3-layer arch, fork-and-customize lifecycle)
type: HITL
status: done
blocked_by: []
parent: docs/prd/primiblocks-v1.md
---

## What to build

`README.md` — the GitHub landing page:

- Hero: one-sentence elevator pitch
- Above the fold: the 3-layer architecture diagram
- "Use this template" 30-second quickstart (with the second diagram: fork-and-customize lifecycle)
- Concise feature list (5–8 bullets)
- Link to SOP for everything else
- Badges (CI status, Python version, MIT license)

And the 2 diagrams it references, both as committed SVG (with `.png` fallback for GitHub render reliability) plus the `.excalidraw` source files in `docs/diagrams/src/`:

- `docs/diagrams/3-layer-architecture.svg` (+ `.png` fallback + `src/3-layer-architecture.excalidraw`)
- `docs/diagrams/fork-and-customize-lifecycle.svg` (+ `.png` fallback + `src/fork-and-customize-lifecycle.excalidraw`)

**Quality bar:** beautiful, professional. NO mermaid blocks. NO ASCII art. Diagrams are real images.

HITL because: visual quality and branding require human judgment; this is what a stranger sees first.

## Acceptance criteria

- [ ] `README.md` renders cleanly on GitHub (preview the rendered Markdown)
- [ ] Both diagrams render inline on the GitHub README (SVG primary, PNG fallback if needed)
- [ ] Both diagrams' `.excalidraw` source files are committed under `docs/diagrams/src/`
- [ ] Hero pitch is one sentence; quickstart is ≤30 seconds to read
- [ ] No mermaid code blocks anywhere in the README
- [ ] No ASCII-art diagrams anywhere in the README

## Blocked by

None — can start immediately.
