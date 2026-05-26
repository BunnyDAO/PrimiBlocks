---
id: 0011
title: /primi-fill skill — grouped-by-primitive walkthrough + preview
type: HITL
status: done
blocked_by: [0008, 0010]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`.claude/skills/primi-fill/SKILL.md` — a Claude Code skill that drives the fill workflow against the bundled CLI's `--json` mode:

1. Call `primiblocks list templates --json`, present the user with a picker.
2. On selection, retrieve the template's effective contract (via `primiblocks validate` with an empty vars or a dedicated subcommand if added).
3. Walk the contract **one variable at a time, grouped by primitive** with a header per primitive ("Now configuring `retrieval_block`…"). Use each var's `description` as the prompt; render constraints as appropriate UI (enum → choice list, bool → yes/no, int with min/max → bounded input hint).
4. Validate each answer against the contract; re-ask on failure with a clear reason.
5. Write `.primiblocks/runs/<timestamp>/vars.json`.
6. Call `primiblocks render <template> --vars <path> --json`.
7. Show the rendered artifact to the user as a preview; confirm; on confirm, write to the user-specified output path. On reject, abort without writing.

HITL because: this is the user-facing UX promise of the entire product; the SKILL.md needs review against the PRD's stated flow before it's merged.

## Acceptance criteria

- [ ] SKILL.md exists at `.claude/skills/primi-fill/SKILL.md`
- [ ] The skill workflow follows the 7-step PRD-specified flow
- [ ] The skill uses the CLI's `--json` mode for all renderer interactions (no direct module imports)
- [ ] Manual end-to-end test against the reference kit: skill renders `rag-qa-prompt` from a user walk-through, producing the same artifact as `primiblocks render rag-qa-prompt --vars vars.example.json` (within the user's choices)
- [ ] Skill handles validation errors per-answer, re-asking with the renderer's error message
- [ ] Skill shows a preview and aborts cleanly if the user rejects

## Blocked by

- 0008
- 0010
