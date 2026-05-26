---
id: 0004
title: primitives.py — discovery + contract loading
type: AFK
status: done
blocked_by: [0003]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`primitives.discover(kit_dir)` walks `kit/primitives/*.j2`, parses each file's YAML frontmatter into a `Contract`, and returns a `dict[str, Primitive]` keyed by primitive name (derived from filename without extension). Each `Primitive` carries its name, its parsed contract, and a reference to its body content (path or string, whatever the Jinja env consumes downstream).

Malformed primitives (bad YAML, unknown types, missing descriptions) surface as parse errors at discovery time — the renderer fails fast, not at render time.

## Acceptance criteria

- [ ] `discover()` returns a `dict[str, Primitive]` from a fixture kit with multiple primitives
- [ ] Each `Primitive` exposes name, contract, and body (or a path to it)
- [ ] Malformed frontmatter surfaces a clear error citing the file
- [ ] An empty `kit/primitives/` returns an empty dict (not an error)
- [ ] Tests use a fixture kit with at least one valid primitive, one malformed primitive (in a separate test), and one with constraints

## Blocked by

- 0003
