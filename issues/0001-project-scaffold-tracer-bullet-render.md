---
id: 0001
title: Project scaffold + tracer-bullet render
type: HITL
status: done
blocked_by: []
parent: docs/prd/primiblocks-v1.md
---

## What to build

A minimal end-to-end vertical slice that proves the architecture works. Includes the package skeleton, the simplest possible versions of `errors.py`, `contract.py`, `templates.py`, and `render.py`, plus ONE primitive and ONE template, plus a passing test that renders the template against a vars dict and asserts the output. No CLI, no constraints, no primitive composition — just "Jinja2 render with required-var check works on disk."

The point of this slice is the architectural commitment: by the end, the module boundaries are real (even if their internals are skinny), the test infrastructure runs, and every subsequent slice thickens an existing module rather than introducing a new one.

HITL because: module shape choices made here propagate everywhere. A reviewer should sanity-check the public interfaces before they ossify.

## Acceptance criteria

- [ ] `pyproject.toml` declares Python 3.11+, runtime deps `jinja2` and `pyyaml`, dev deps `pytest`
- [ ] `primiblocks/__init__.py`, `errors.py` (just `PrimiBlocksError` base), `contract.py` (parse + required-var check only), `templates.py` (parse frontmatter only, no primitive composition), `render.py` (Jinja2 render + validate orchestration) exist as importable modules
- [ ] `kit/primitives/hello.j2` and `kit/templates/hello.j2` exist (template's frontmatter declares one required string var `name`, no constraints)
- [ ] `tests/test_tracer.py` calls the render path against `{name: "World"}` and asserts the output contains `"Hello, World"`
- [ ] `tests/test_tracer.py` calls the render path with missing `name` and asserts a `PrimiBlocksError` (or subclass) is raised
- [ ] `pytest` runs green from a clean `pip install -e .[dev]`

## Blocked by

None — can start immediately.
