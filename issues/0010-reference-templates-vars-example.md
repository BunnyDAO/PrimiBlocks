---
id: 0010
title: Reference kit — 3 templates + vars.example.json
type: AFK
status: in_progress
blocked_by: [0006, 0009]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Author the 3 reference templates in `kit/templates/` (per PRD's "Reference kit contract" table). Replaces the tracer-bullet `hello.j2` template.

1. **`rag-qa-prompt.j2`** — composes: `system_persona`, `retrieval_block`, `task_instruction`, `output_format_markdown`
2. **`agent-tool-using-prompt.j2`** — composes: `system_persona`, `task_instruction`, `tool_use_examples`, `output_format_json`, `guardrail_refusal`
3. **`eval-judge-prompt.j2`** — composes: `system_persona`, `task_instruction`, `few_shot_block`, `output_format_json`

Each template declares its own vars where needed (e.g., template-level overrides like a tightened `enum` on `tone`). Bodies use `{% include "primitives/X.j2" %}` to compose.

Plus `kit/vars.example.json` with a working sample vars dict for each template — top-level keyed by template name.

## Acceptance criteria

- [ ] All 3 templates exist and parse cleanly via `templates.discover()`
- [ ] Each composes the primitives listed in the PRD table
- [ ] Each renders successfully against its entry in `kit/vars.example.json`
- [ ] The rendered output of each is a recognizable, meaningful prompt (manual review)
- [ ] Tests: render each template against its `vars.example.json` entry; assert non-empty output and specific expected anchor substrings

## Blocked by

- 0006
- 0009
