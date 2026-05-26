---
id: 0005
title: templates.py — effective contract aggregation + template-wins on collision
type: AFK
status: done
blocked_by: [0004]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`templates.discover(kit_dir)` walks `kit/templates/*.j2`, parses each file's frontmatter into a `Template` (own contract + `primitives: [...]` list). `templates.effective_contract(template, primitives_map)` computes the template's effective contract: union of own vars + every listed primitive's vars, with template declarations replacing primitive declarations on name collision (no field-level merge — full override).

Per ADR-0002. Errors when `primitives:` lists a primitive name not present in `primitives_map`.

## Acceptance criteria

- [ ] `discover()` parses templates with no primitives, with primitives, and with var overrides
- [ ] `effective_contract()` correctly unions vars when no collision
- [ ] `effective_contract()` correctly REPLACES (not merges) a primitive's declaration with the template's on name collision
- [ ] `effective_contract()` raises if `primitives:` lists an unknown primitive
- [ ] Order of primitives in the resulting contract follows the order in `primitives:` (deterministic for the fill-skill's grouping)
- [ ] Tests cover: no collision, collision with override, multi-primitive composition, missing primitive

## Blocked by

- 0004
