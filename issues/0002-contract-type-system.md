---
id: 0002
title: contract.py — type system (string/int/float/bool/list/path/enum)
type: AFK
status: open
blocked_by: [0001]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Extend `contract.py` so each variable in a contract declares a `type` (one of: `string`, `int`, `float`, `bool`, `list`, `path`, `enum`). On `Contract.validate(vars)`, supplied vars are type-checked; mismatches raise a typed error citing the variable name, expected type, and actual type. The `enum` type is a placeholder here (its allowed values land in 0003); for now, treat it as string.

`path` is validated as string-shaped — actual filesystem existence is not enforced (kits may render against paths that don't exist on the renderer machine; the artifact consumer enforces existence).

## Acceptance criteria

- [ ] Contract grammar accepts `type:` on each var; missing or unknown types are rejected at parse time with a clear error
- [ ] Validating a vars dict against the contract raises typed errors when a value's runtime type doesn't match the declared type
- [ ] Tests cover positive cases for each type (correct value passes) and negative cases (wrong type raises)
- [ ] Error messages include the variable name and the offending type information
- [ ] Tracer-bullet test from 0001 still passes (no regression)

## Blocked by

- 0001
