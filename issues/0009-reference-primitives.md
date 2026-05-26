---
id: 0009
title: Reference kit — 8 LLM-prompt primitives
type: AFK
status: done
blocked_by: [0004]
parent: docs/prd/primiblocks-v1.md
---

## What to build

Author the 8 reference primitives in `kit/primitives/`, each with a proper frontmatter contract (typed vars, descriptions, defaults, constraints where natural). Replaces the tracer-bullet `hello.j2` primitive.

1. **`system_persona.j2`** — vars: `persona_name` (string), `tone` (enum: `professional`|`casual`|`playful`), `expertise_domain` (string)
2. **`task_instruction.j2`** — vars: `task_summary` (string), `constraints` (list, optional), `success_criteria` (string)
3. **`retrieval_block.j2`** — vars: `index_name` (string, pattern: `^[a-z0-9-]+$`), `top_k` (int, min 1, max 50, default 5), `chunk_separator` (string, default `\n---\n`)
4. **`tool_use_examples.j2`** — vars: `tool_name` (string), `examples` (list)
5. **`output_format_json.j2`** — vars: `schema_path` (path), `strict` (bool, default true)
6. **`output_format_markdown.j2`** — vars: `sections` (list)
7. **`few_shot_block.j2`** — vars: `examples` (list), `separator` (string, default `\n\n`)
8. **`guardrail_refusal.j2`** — vars: `forbidden_topics` (list), `refusal_template` (string)

Each primitive's body is real, useful prompt text — not placeholder lorem.

## Acceptance criteria

- [ ] All 8 primitives exist in `kit/primitives/`
- [ ] Each frontmatter parses cleanly via `primitives.discover()`
- [ ] Each has a meaningful `description` and meaningful body text
- [ ] Constraints (enum, pattern, min/max, defaults) are exercised where the PRD specifies
- [ ] Tests: `primitives.discover()` on the live `kit/` returns all 8

## Blocked by

- 0004
