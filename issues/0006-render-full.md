---
id: 0006
title: render.py — full render with effective contract + Jinja primitive includes
type: AFK
status: open
blocked_by: [0005]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`render.render(template_name, vars, kit_dir)` orchestrates: discover primitives + templates, compute effective contract, validate vars against the effective contract, configure a Jinja2 `Environment` with `kit/primitives/` as an include path (so `{% include "primitives/foo.j2" %}` resolves natively), render the template, return the string.

Replace the tracer-bullet's minimal render with this. Tracer test from 0001 still passes.

## Acceptance criteria

- [ ] `render()` renders a template that composes multiple primitives via `{% include %}`
- [ ] Validation runs BEFORE Jinja render; bad vars raise before any template processing
- [ ] Effective contract is computed correctly and used for validation
- [ ] `kit/templates/hello.j2` still renders correctly (no regression on 0001 tracer)
- [ ] Tests cover: render with primitives, render with missing required (error), render with type mismatch (error), render with constraint violation (error)

## Blocked by

- 0005
