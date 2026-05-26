---
id: 0012
title: /primi-author skill — primitive picker + new-template + primitive-request
type: HITL
status: done
blocked_by: [0008]
parent: docs/prd/primiblocks-v1.md
---

## What to build

`.claude/skills/primi-author/SKILL.md` — a Claude Code skill that composes a new template from existing primitives:

1. User describes the template they want (free text).
2. Skill calls `primiblocks list primitives --json` and presents each primitive's name + contract surface as a picker.
3. User selects which primitives to include and in what order.
4. For each selected primitive, skill surfaces its contract; user can override defaults or add template-level var overrides.
5. Skill writes `kit/templates/<name>.j2` with `primitives: [...]` frontmatter, any var overrides, and a body that `{% include %}`s each primitive in order.
6. If the user's described need cannot be met by existing primitives, the skill writes `kit/requests/<slug>.md` — a structured primitive-request describing the missing primitive(s) (name, intended contract, why) — instead of (or in addition to) the template.

HITL because: the composition UX needs review and the request format needs to be developer-actionable.

## Acceptance criteria

- [ ] SKILL.md exists at `.claude/skills/primi-author/SKILL.md`
- [ ] Skill uses the CLI's `--json` mode for primitive discovery
- [ ] A new template authored via the skill lints clean (`primiblocks lint`)
- [ ] A new template authored via the skill renders against well-formed vars (`primiblocks render`)
- [ ] When the user's need can't be met, skill writes `kit/requests/<slug>.md` with: requested primitive name, intended contract (vars + types + constraints), why-it's-needed narrative
- [ ] Manual end-to-end test: skill authors a new template composing 2–3 reference primitives; lint + render both pass

## Blocked by

- 0008
