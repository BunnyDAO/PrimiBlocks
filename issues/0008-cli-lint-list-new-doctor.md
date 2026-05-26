---
id: 0008
title: cli.py — lint, list, new, doctor subcommands
type: AFK
status: open
blocked_by: [0007]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Four more subcommands, all supporting `--json`:

**`primiblocks lint [--json]`** — kit-wide checks:
- `primitives:` frontmatter list matches `{% include %}` statements in the template body (warn on drift either direction)
- Every contract var has a `description`
- No collisions between primitive contract vars where the template doesn't override (warning, not error)
- No broken includes (referenced primitive not in `kit/primitives/`)

**`primiblocks list templates [--json]` / `primiblocks list primitives [--json]`** — enumerate the kit contents with their descriptions.

**`primiblocks new template <name>` / `primiblocks new primitive <name>`** — scaffold a stub `.j2` file with placeholder frontmatter (description, one example var). The stub must lint clean immediately.

**`primiblocks doctor [--json]`** — diagnose common problems as a series of named checks: Python version ≥ 3.11, `jinja2` and `pyyaml` importable, `kit/` exists with `primitives/` and `templates/`, `kit/` lints clean. Each check is a separate row in the output.

## Acceptance criteria

- [ ] `lint` catches drift between `primitives:` and `{% include %}` (both directions)
- [ ] `lint` catches a contract var missing `description`
- [ ] `lint` catches a `primitives:` entry that doesn't exist in `kit/primitives/`
- [ ] `list templates` and `list primitives` emit the expected entries (with descriptions) in both human and JSON modes
- [ ] `new template` and `new primitive` write a valid stub `.j2` that lints clean
- [ ] `doctor` reports green when the system is healthy; reports specific failures (each as a separate check row) when not
- [ ] All subcommands have `--json` parity
- [ ] Tests via subprocess for each subcommand (happy path + at least one error path)

## Blocked by

- 0007
