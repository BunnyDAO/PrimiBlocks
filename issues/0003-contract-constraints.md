---
id: 0003
title: contract.py — constraints (description, default, required, enum, min/max, pattern, examples)
type: AFK
status: done
blocked_by: [0002]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Round out the contract grammar with the full set of optional constraint slots from the PRD: `description` (required for each var, drives the fill-skill UX), `default` (any), `required` (bool, default true), `enum` (list of allowed values), `min` and `max` (for int/float and list-length), `pattern` (regex for strings), `examples` (list, informational).

Validation enforces each constraint and raises errors that cite the offending field and the constraint that failed. Defaults are applied to omitted optional vars before type-checking.

## Acceptance criteria

- [ ] Every constraint slot is parseable in YAML frontmatter
- [ ] `required: false` allows the var to be omitted (default applied if present, `None` if not)
- [ ] `required: true` (default) raises if the var is missing
- [ ] `enum` raises if the supplied value is not in the list
- [ ] `min`/`max` raise on out-of-range int/float and on list length out of range
- [ ] `pattern` raises if the supplied string doesn't match the regex
- [ ] `description` is required on every var (kits that omit it fail contract parsing)
- [ ] `examples` is informational only (does not affect validation)
- [ ] Tests cover positive and negative cases for each constraint
- [ ] Tracer-bullet test from 0001 still passes

## Blocked by

- 0002
