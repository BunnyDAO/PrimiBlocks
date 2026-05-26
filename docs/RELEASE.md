# PrimiBlocks v0.1.0 — release prep

This file documents the release ritual for v0.1.0. The local work (tag, release-notes draft) is done; the **GitHub UI steps** at the bottom are on you because they require account access.

---

## Status (as of this commit)

- 17 / 17 issues from `issues/` shipped
- 97+ tests green locally (pytest)
- Reference kit renders + lints clean (`primiblocks doctor` green)
- README + SOP + 6 v1 diagrams committed
- Cross-OS CI workflow at `.github/workflows/test.yml` (will run on first push)

## Release notes (paste into the GitHub Release)

```markdown
# PrimiBlocks v0.1.0 — first public release

**PrimiBlocks is a clonable, cross-OS scaffold + methodology for building domain-specific generators using a Lego kit of typed primitives.**

Two existing projects ([HITL](https://github.com/BunnyDAO/HITL) for camera testing and [Agent-Builder](https://github.com/BunnyDAO/Agent-Builder) for Claude Code agent crews) independently proved the same pattern: **constrain LLM-driven artifact generation by composing reviewed primitives into typed templates and walking the user through the contract via a skill.** v0.1.0 extracts that pattern into a forkable scaffold so every new domain doesn't reinvent the convention, and so the renderer works on **any OS** (Python 3.11+ only — no brew, no Rust).

## What ships

- **Renderer** — `primiblocks/` Python module (Jinja2 + PyYAML, nothing else) with rich typed-contract validation (`string|int|float|bool|list|path|enum` + `enum`, `min`/`max`, `pattern`, `examples`, descriptions).
- **Effective contract aggregation** — primitives carry their own contracts; templates list `primitives: [...]`; the renderer aggregates with template-level overrides winning on collision ([ADR-0002](docs/adr/0002-primitives-carry-contracts-that-bubble-up.md)).
- **CLI** — `primiblocks` with subcommands `render | validate | contract | lint | list | new | doctor`, all `--json`-capable.
- **Two Claude Code skills** — `/primi-fill` (conversational walkthrough, grouped by primitive, validated per-answer, preview before write) and `/primi-author` (compose new templates from primitives, or file a structured request when primitives are missing).
- **Reference LLM-prompt kit** — 8 primitives (`system_persona`, `task_instruction`, `retrieval_block`, `tool_use_examples`, `output_format_json`, `output_format_markdown`, `few_shot_block`, `guardrail_refusal`) + 3 templates (`rag-qa-prompt`, `agent-tool-using-prompt`, `eval-judge-prompt`).
- **Cross-OS CI** — macOS, Linux, Windows × Python 3.11 / 3.12 / 3.13.
- **Real SOP** — non-developer path + developer path, with 6 committed SVG diagrams. No mermaid, no ASCII.

## First-30-minute experience

Use the GitHub "Use this template" button (this repo is configured as a Template Repository) or `git clone`, install with `pip install -e ".[dev]"`, run `primiblocks doctor`, then in Claude Code type `/primi-fill`. The first rendered prompt is the aha.

## Decisions worth knowing about

- [ADR-0001](docs/adr/0001-bundled-python-renderer-not-sc-compose.md) — Bundled Python renderer instead of depending on sc-compose (for cross-OS portability).
- [ADR-0002](docs/adr/0002-primitives-carry-contracts-that-bubble-up.md) — Primitives carry their own contracts that bubble up into templates.

## Deferred to v1.x

- PyPI distribution (`pipx run primiblocks init`).
- Multi-kit-per-fork (`kits/<name>/` convention).
- Tree-output / Cookiecutter-style templates.
- Custom Python validators in template frontmatter.
- `watch`, `fmt`, `schema export` CLI subcommands.
- Polished Excalidraw diagrams to replace the v1 vector sketches in `docs/diagrams/`.

## Thanks

To the HITL and Agent-Builder authors for proving the pattern, and to randlee for the `sc-compose` design that PrimiBlocks's contract grammar borrows from.
```

---

## Local steps (already done by this commit)

- `git tag -a v0.1.0 -m "PrimiBlocks v0.1.0"` (run after merging this commit to `main`)
- `git push --tags`

## GitHub UI steps (your turn)

These need account-level access; I (the AI) can't toggle them. From `https://github.com/BunnyDAO/PrimiBlocks/settings`:

1. **Make it a Template Repository.** Under *General*, scroll to *Template repository* and check the box. The "Use this template" button appears on the repo page within a minute.
2. **Enable branch protection on `main`.** Under *Rules → Rulesets → New ruleset*:
   - Target branch: `main`
   - Require status checks to pass: select the `test` workflow's matrix jobs.
   - Require pull request reviews before merging: at least 1 approving review.
   - (Optional but recommended) Require linear history.
3. **Set About + topics.** From the repo's main page, click the gear next to "About". Add a description ("Clonable scaffold + methodology for building domain-specific Lego kits…") and topics: `claude-code`, `templates`, `prompt-engineering`, `scaffold`, `python`, `primitives`.
4. **Publish the v0.1.0 GitHub Release.** From *Releases → Draft a new release*:
   - Choose tag `v0.1.0` (will appear once you push the tag).
   - Title: `PrimiBlocks v0.1.0`.
   - Paste the release notes block above.
   - Publish.

That's it. Once the Template Repo toggle is on and v0.1.0 is published, strangers can click "Use this template" and be on their way.
