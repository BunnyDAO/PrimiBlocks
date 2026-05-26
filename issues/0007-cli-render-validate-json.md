---
id: 0007
title: cli.py — render + validate subcommands with --json envelope
type: AFK
status: done
blocked_by: [0006]
parent: docs/prd/primiblocks-v1.md
---

## What to build

argparse-based CLI exposing two subcommands:

- `primiblocks render <template> [--vars FILE] [--out FILE] [--json]` — render to stdout or `--out` path
- `primiblocks validate <template> [--vars FILE] [--json]` — validate without rendering

The `--json` flag emits a `{"ok": bool, "data"?: ..., "error"?: {...}}` envelope to stdout. In human mode, errors go to stderr; in JSON mode, errors go inside the envelope. Exit code 0 on success, 1 on validation/contract error, 2 on usage error.

The CLI is the integration surface the two skills consume — this is the load-bearing bit.

## Acceptance criteria

- [ ] `primiblocks render <template> --vars vars.json` writes the artifact to stdout (or `--out`)
- [ ] `primiblocks render` exits non-zero on missing template, missing required var, type mismatch — with a clear error message
- [ ] `primiblocks validate` returns 0 on valid vars, non-zero with a clear error on invalid
- [ ] `--json` mode emits a valid JSON envelope on both success and error paths
- [ ] Exit codes follow the spec (0 / 1 / 2)
- [ ] Tests run the CLI via `subprocess.run` and verify stdout / stderr / exit code per case
- [ ] Tests verify the `--json` envelope shape on both success and error

## Blocked by

- 0006
