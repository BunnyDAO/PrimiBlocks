# PrimiBlocks v1 — PRD

## Problem Statement

Two existing projects (HITL for camera testing, Agent-Builder for Claude Code agent crews) have independently proven a powerful pattern: constrain LLM-driven artifact generation by composing **reviewed primitives** into **typed templates**, then walk the user through filling the template's contract via a skill. The result is a deterministic, auditable artifact (a pytest file, an agent prompt) — no freeform code-gen, no copy-paste drift.

But the pattern is trapped in each domain instance. Every new team that wants this has to reverse-engineer the convention from a working domain example, re-implement the renderer dependency (sc-compose, a brew-only Rust CLI), and rebuild the two skills from scratch. The pattern is general; the substrate is not. Cross-OS portability is also broken (sc-compose's brew install is hostile to Linux/Windows users).

## Solution

PrimiBlocks is a **cross-OS, clonable scaffold + methodology** that ships the *machinery* of the pattern as a forkable GitHub Template Repo at `BunnyDAO/PrimiBlocks`. A stranger clicks "Use this template," gets:

- a **bundled Python renderer** (cross-OS, Jinja2 + YAML-frontmatter contract validation, real CLI)
- a **reference LLM-prompt domain kit** (~8 primitives, 3 templates) that demonstrates the pattern with an instantly-relatable example
- two **pre-wired Claude Code skills** (`/primi-fill`, `/primi-author`) that work out of the box against the bundled renderer
- a **SOP** with beautiful (non-mermaid, non-ASCII) diagrams explaining the pattern and how to build their own domain kit

They replace `kit/` with their own domain's primitives and templates and ship — without ever building the renderer or the skills.

## User Stories

1. As a **Claude Code user discovering PrimiBlocks via GitHub**, I want to land on the README and within 30 seconds understand *what this is* and *why I'd use it*, so I keep reading instead of bouncing.
2. As a **stranger forking PrimiBlocks for the first time**, I want to click "Use this template," clone my new repo, and within 5 minutes run `/primi-fill` against the bundled reference kit and produce a working artifact, so I trust the pattern works before investing in my own kit.
3. As a **stranger on macOS, Linux, or Windows**, I want the renderer to work with only Python 3.11+ installed (no brew, no Rust, no native binaries), so portability is not a blocker.
4. As a **domain expert building a custom kit**, I want to replace `kit/primitives/` and `kit/templates/` with my domain's content following the SOP, and have the bundled skills + CLI work against my kit unchanged, so I never modify the framework code.
5. As a **template author**, I want to declare a rich contract in YAML frontmatter (typed vars with descriptions, defaults, enums, ranges, patterns), so the fill-skill can ask smart questions and reject invalid input before render.
6. As a **primitive author**, I want my primitive to carry its own contract (independent of any template), so the same primitive can be reused across templates without re-declaring its variables.
7. As a **template author composing primitives**, I want to list `primitives: [foo, bar, baz]` in the template's frontmatter and have their contracts bubble up automatically into the template's effective contract, so I don't have to manually re-list every variable.
8. As a **template author**, I want to override a primitive-declared variable in my template's frontmatter (change the default, tighten the constraint, rename) when my use case demands it, so I'm never stuck forking the primitive.
9. As a **non-programmer running `/primi-fill`**, I want the skill to list available templates with their descriptions, let me pick, then walk me through the effective contract **one variable at a time, grouped by primitive** with helpful headers, validating each answer, so I never see a malformed render error and the flow feels guided.
10. As a **`/primi-fill` user**, I want to preview the rendered artifact before it's written to disk, and confirm or abort, so I never produce an unwanted file.
11. As a **template author running `/primi-author`**, I want to compose a new template by selecting primitives from a picker (each primitive showing its contract surface), arranging them in order, and optionally overriding their vars, so I never write a `.j2` file by hand.
12. As a **`/primi-author` user**, when the primitive I need doesn't exist, I want the skill to write a structured **primitive-request** markdown file describing what I need, so a developer can fulfill the request without re-interviewing me.
13. As a **CLI consumer**, I want `primiblocks render <template> --vars vars.json` to render an artifact to stdout (or `--out`), with clear errors and proper exit codes, so I can script it.
14. As a **CLI consumer**, I want `primiblocks validate <template> --vars vars.json` to validate vars against the effective contract without rendering, so I can use it in CI.
15. As a **kit maintainer**, I want `primiblocks lint` to detect drift between frontmatter-declared primitive lists and actual `{% include %}` statements in the template body, so my kit stays consistent.
16. As a **kit maintainer**, I want `primiblocks list templates` and `primiblocks list primitives` to enumerate the kit's contents with their descriptions, so I can audit my surface area.
17. As a **skill author calling the CLI**, I want a `--json` flag on every subcommand for machine-readable output, so the bundled skills can consume the renderer's output programmatically.
18. As a **new user with an unfamiliar error**, I want `primiblocks doctor` to diagnose common problems (wrong Python version, missing dependencies, malformed kit, broken contract), so I'm not stuck Googling.
19. As a **stranger reading the SOP**, I want the architecture explained with **beautiful, professional-looking diagrams** (not mermaid blocks, not ASCII art), so the doc feels like a real product, not a hobby project.
20. As a **contributor on the project**, I want CI on macOS, Linux, and Windows running the full pytest suite on every PR, so portability regressions are caught before merge.
21. As a **kit maintainer**, I want `primiblocks new template <name>` and `primiblocks new primitive <name>` to scaffold a stub `.j2` file with placeholder frontmatter, so I never start from a blank file.

## Implementation Decisions

### Modules to build

The renderer is six modules in `primiblocks/`, designed as **deep modules** with small, stable interfaces and most behavior hidden:

| Module | Responsibility | Public interface | Depends on |
|---|---|---|---|
| `errors.py` | Error catalog with file/line context; all errors raised by other modules subclass `PrimiBlocksError` | Error classes | — (independent) |
| `contract.py` | YAML frontmatter parse + a typed `Contract` dataclass; validates a vars dict against the contract (type checks, enum/min/max/pattern, defaults, required) | `Contract.parse(yaml_str) -> Contract`, `Contract.validate(vars: dict) -> ValidatedVars` | `errors.py` |
| `primitives.py` | Discover `kit/primitives/*.j2`, parse each frontmatter into a `Primitive` (`name`, `contract`, `body_path`) | `discover(kit_dir: Path) -> dict[str, Primitive]` | `contract.py` |
| `templates.py` | Discover `kit/templates/*.j2`, parse frontmatter into a `Template` (`name`, `own_contract`, `primitives: list[str]`), compute `effective_contract(template, primitives_map) -> Contract` (the bubble-up + collision-override logic) | `discover(kit_dir) -> dict[str, Template]`, `effective_contract(template, primitives) -> Contract` | `contract.py`, `primitives.py` |
| `render.py` | Configure Jinja2 environment with `kit/primitives/` as include path; orchestrate validate-then-render | `render(template_name, vars, kit_dir) -> str` | `contract.py`, `templates.py` |
| `cli.py` | argparse-based CLI exposing the subcommands. Each subcommand has a `--json` mode that emits a JSON envelope `{ok: bool, data?, error?}` to stdout (errors go to stderr in human mode) | `main(argv) -> int` | all the above |

**Module independence (drives the issue breakdown):**

- `errors.py`, `contract.py` — independent, can be built and unit-tested first
- `primitives.py`, `templates.py` — depend on `contract.py`, can be built in parallel after it
- `render.py` — depends on `templates.py` + `primitives.py`
- `cli.py` — last, wires everything
- Reference `kit/` content — independent of all code; can be authored in parallel
- Skills (`primi-fill`, `primi-author`) — depend on the CLI's `--json` mode
- README/SOP/diagrams — independent of code; can be authored in parallel
- CI workflows — independent of code, but verify everything together

### CLI subcommand surface (v1)

`primiblocks` exposes:

- `render <template> [--vars FILE] [--out FILE] [--json]` — render to stdout/file
- `validate <template> [--vars FILE] [--json]` — validate without rendering
- `lint [--json]` — kit-wide consistency checks (frontmatter↔body drift, contract collisions, broken includes, missing required descriptions)
- `list templates [--json]` / `list primitives [--json]` — enumerate kit contents
- `new template <name>` / `new primitive <name>` — scaffold stub `.j2` with placeholder frontmatter
- `doctor [--json]` — diagnose common problems (Python version, deps, kit health)

### Contract grammar

YAML frontmatter, fenced by `---`. Per-variable schema:

```yaml
---
description: One-line summary of what this primitive/template does.
primitives:        # templates only
  - retrieval_block
  - output_format_json
vars:
  - name: index_name
    type: string         # string|int|float|bool|list|path|enum
    description: Name of the retrieval index to query.
    required: true       # default true
    default: null        # ignored if required
    examples: ["prod-docs", "staging-docs"]
    # constraint slots (all optional):
    enum: ["prod-docs", "staging-docs"]   # for type: enum or string
    min: 1                                 # for int/float/list-length
    max: 50
    pattern: "^[a-z0-9-]+$"               # for string
---
```

**Effective contract aggregation:** the template's `vars` and every primitive in `primitives:`'s `vars` are unioned; on `name` collision, the template's declaration replaces the primitive's entirely (no field-level merge).

### Composition mechanism

Templates compose primitives via standard Jinja2 `{% include "primitives/foo.j2" %}` statements in the body. The `primitives:` frontmatter field is the **declarative** source of truth used by:

- the **renderer** to compute the effective contract
- the **linter** to detect drift (`primitives:` lists `foo` but body doesn't `{% include %}` it, or vice versa)
- the **`/primi-author` skill** to introspect what's composed

The render step itself uses Jinja2's native include — no PrimiBlocks-specific syntax in template bodies.

### Skills (Claude Code markdown skills under `.claude/skills/`)

**`/primi-fill`** workflow:

1. Call `primiblocks list templates --json`; present picker.
2. On selection: call `primiblocks validate <template> --json --vars /dev/null` to retrieve effective contract.
3. Walk the contract **one variable at a time, grouped by primitive** (header per primitive: "Now configuring `retrieval_block`…"). Use each var's `description` as the question prompt. Render constraints as pickers (enum → choice list; bool → yes/no; int with min/max → bounded input with hint).
4. Validate each answer against the variable's type/constraints in-skill; re-ask on failure with the renderer's error message.
5. Write `vars.json` to a working directory.
6. Call `primiblocks render <template> --vars vars.json --json` and capture the rendered artifact.
7. Show preview to user; confirm; on confirm write to the user-named output path.

**`/primi-author`** workflow:

1. User describes the template they want (free text).
2. Skill calls `primiblocks list primitives --json` and presents a picker; user selects which primitives to include and in what order.
3. For each selected primitive, skill surfaces its contract; user can override defaults / add var-level overrides.
4. Skill writes the new `kit/templates/<name>.j2` with `primitives: [...]` frontmatter, optional `vars:` overrides, and a body that `{% include %}`s each primitive in order.
5. If the user's described need can't be met by existing primitives, skill writes `kit/requests/<slug>.md` — a structured primitive-request describing the missing primitive(s) (name, intended contract, why) — for a developer to fulfill.

### Reference kit contract (the load-bearing v1 example)

**`kit/primitives/`** (8 files):

| File | Purpose |
|---|---|
| `system_persona.j2` | Sets the system/persona prompt (vars: `persona_name`, `tone`, `expertise_domain`) |
| `task_instruction.j2` | Declares the task to the model (vars: `task_summary`, `constraints[]`, `success_criteria`) |
| `retrieval_block.j2` | Inserts a retrieved-context block (vars: `index_name`, `top_k`, `chunk_separator`) |
| `tool_use_examples.j2` | Few-shot examples of tool calls (vars: `tool_name`, `examples[]`) |
| `output_format_json.j2` | Constrains output to a JSON schema (vars: `schema_path`, `strict`) |
| `output_format_markdown.j2` | Constrains output to a markdown structure (vars: `sections[]`) |
| `few_shot_block.j2` | Generic input/output exemplars (vars: `examples[]`, `separator`) |
| `guardrail_refusal.j2` | Refusal/safety policy preamble (vars: `forbidden_topics[]`, `refusal_template`) |

**`kit/templates/`** (3 files):

| File | Purpose | Composes |
|---|---|---|
| `rag-qa-prompt.j2` | A retrieval-augmented QA prompt | `system_persona`, `retrieval_block`, `task_instruction`, `output_format_markdown` |
| `agent-tool-using-prompt.j2` | An agent system prompt with tools and few-shot examples | `system_persona`, `task_instruction`, `tool_use_examples`, `output_format_json`, `guardrail_refusal` |
| `eval-judge-prompt.j2` | An LLM-as-judge eval prompt | `system_persona`, `task_instruction`, `few_shot_block`, `output_format_json` |

`vars.example.json` contains a working sample for each of the three templates.

### Documentation requirements

**README.md** (the GitHub landing page):

- Hero: one-sentence elevator pitch + a single diagram (the 3-layer architecture) above the fold
- "Use this template" button explanation + 30-second quickstart
- A second diagram (the fork-and-customize lifecycle) showing where the user replaces `kit/`
- Concise feature list, link to SOP for everything else
- Badges (CI status, Python version, license)

**SOP.md** (the operating procedure):

- Walkthrough of building a domain kit from empty, with diagrams at each conceptual hand-off
- Reference for: contract grammar, composition model, CLI subcommand reference, both skills' UX, troubleshooting (the `doctor` checklist)
- Splits the audience into two paths: *non-developer using a kit someone else built* vs. *developer building a new kit* (mirroring HITL's SOP pattern)

**Diagram inventory** — each delivered as committed SVG (with PNG fallbacks for GitHub README rendering reliability), authored in Excalidraw (or equivalent), source `.excalidraw` files committed to `docs/diagrams/src/`:

1. **3-layer architecture** — primitives → templates → skills → rendered artifact (overview, appears in README and SOP)
2. **Effective contract aggregation** — visual showing template vars + primitive A vars + primitive B vars → effective contract, with the collision-override case called out
3. **`/primi-fill` flow** — from "user runs skill" through to "artifact written," with the per-primitive grouped walkthrough as the center
4. **`/primi-author` flow** — from "user describes need" through to either new-template-written or primitive-request-filed
5. **Fork-and-customize lifecycle** — landing on GitHub → "Use this template" → clone → replace `kit/` → first `/primi-fill` against own kit
6. **Renderer module dependency graph** — `errors` → `contract` → `{primitives, templates}` → `render` → `cli`, for contributor docs

**Non-negotiable on diagrams:** no mermaid code blocks, no ASCII art. Real images, committed.

### First-30-minute experience (the load-bearing UX)

A stranger lands on `github.com/BunnyDAO/PrimiBlocks`. Their experience, on the clock:

- **0:00–0:30** — Reads README hero + sees 3-layer architecture diagram. Understands what PrimiBlocks is.
- **0:30–2:00** — Clicks "Use this template" → creates own repo → clones locally.
- **2:00–4:00** — Runs `python3 -m pip install -e .` (or equivalent), then `primiblocks doctor` — sees a green check.
- **4:00–8:00** — Runs `primiblocks list templates`, picks `rag-qa-prompt`, reads SOP "First Render" section.
- **8:00–15:00** — In Claude Code, runs `/primi-fill`, picks `rag-qa-prompt`, walks the grouped contract, sees the rendered prompt. **First aha.**
- **15:00–30:00** — Reads SOP "Building Your Own Kit" section, sees the diagram, understands `kit/` is the only thing they replace.

If any step here is > 2× its budget, the v1 fails on the load-bearing UX requirement.

## Testing Decisions

Test external behavior, not internals. The renderer and contract modules are highly testable units — most coverage is concentrated there. The skills are tested via integration tests (script the `/primi-fill` walk against a fixture kit and snapshot the result) plus manual cross-OS smoke. Diagrams and docs are reviewed by humans.

**Per-module test plan:**

- `contract.py` — unit tests covering: parse valid frontmatter, reject malformed YAML, reject unknown types, validate each type's positive + negative cases, apply defaults correctly, enforce required, enforce enum/min/max/pattern, error messages cite the offending field.
- `primitives.py` — unit tests: discover from a fixture kit, parse each primitive's frontmatter, surface a missing/malformed primitive as a clear error.
- `templates.py` — unit tests: discover templates, parse frontmatter, compute effective contract with no collisions / with collisions / with override / with unknown primitive in `primitives:` list (error).
- `render.py` — integration tests: render each reference template with the example vars; render with missing required var (error); render with invalid constraint (error); render with primitive include path resolved correctly.
- `cli.py` — integration tests: each subcommand happy-path + one error-path; `--json` envelope shape validated.
- `errors.py` — covered transitively by negative-path tests in other modules.
- **Cross-OS** — full pytest suite runs on macOS-latest, ubuntu-latest, windows-latest via GitHub Actions matrix.
- **Reference kit smoke test** — every template in `kit/templates/` renders cleanly against `vars.example.json`; included in CI.
- **Lint test** — `primiblocks lint` exits 0 against the reference kit.

Prior art: HITL's pytest suite (62 tests / 6 skipped) gives us a reasonable shape and density to aim for; PrimiBlocks should land in the 50–100 test range for v1.

## Out of Scope

- **PyPI distribution.** GitHub template repo only for v1. `pipx run primiblocks init` is deferred to v1.x.
- **Multi-kit-per-fork.** A fork hosts exactly one kit at `kit/`. The renderer's kit-resolution is structured as a function so a `kits/<name>/` extension is possible later, but it's not in v1.
- **Tree-output / Cookiecutter-style templates.** One template = one file. Multi-file outputs are composed at the kit layer by rendering N templates.
- **Custom validators (Python functions in template frontmatter).** Considered and rejected for v1 — adds a code-execution surface. Constraint slots (`enum`/`min`/`max`/`pattern`) cover the realistic v1 needs.
- **`watch` mode, `fmt`, `schema export`, `docs` subcommand.** Deferred to v1.x.
- **Non-Claude-Code skill runtimes** (Cursor skills, OpenAI custom GPTs, etc.). v1 ships `.claude/skills/` only; the skill markdown is portable enough to adapt but we don't certify other runtimes.
- **A primitive marketplace / registry.** Not in v1.
- **The actual diagram artwork.** The PRD names the inventory; producing the SVGs is an ISSUES/TDD-time task.

## Non-functional requirements

- **Cross-OS.** Must work on macOS 13+, Ubuntu 22.04+, Windows 11. CI matrix enforces this.
- **Runtime dependencies.** Python 3.11+, Jinja2, PyYAML — nothing else (no native binaries, no Node, no Rust).
- **Render performance.** A reference template should render in < 100ms on a typical laptop. Not a tight SLA — but pathological perf (multi-second renders) is a bug.
- **Install time.** From `git clone` to a passing `primiblocks doctor`: < 2 minutes on any CI runner.
- **Documentation quality bar.** The README and SOP must feel like a real product — beautiful committed SVG/PNG diagrams, no mermaid blocks, no ASCII art.

## Success metrics

- A user unfamiliar with PrimiBlocks can complete the **first-30-minute experience** end-to-end without contacting the maintainer.
- CI passes on all three OSes for the v1 tag.
- The reference kit produces three valid rendered prompts (one per template) with `vars.example.json`.
- `primiblocks lint` reports zero issues against the reference kit.
- A second domain kit (e.g., the user's Iron testing primitives) can be authored *without modifying anything in `primiblocks/`* — proves the framework/kit boundary holds.

## Rollout

- v1 ships as a tagged release of the `BunnyDAO/PrimiBlocks` repo, with the GitHub repo settings configured as a **Template Repository**.
- Announcement post explains the pattern (linking HITL + Agent-Builder as proof) and walks the first-30-minute experience with screenshots.
- v1.x backlog: PyPI publish (`pipx run primiblocks init`), multi-kit support, deferred CLI subcommands.

## Open questions

- **Versioning of primitives.** Should a primitive's frontmatter declare a `version:` and templates pin to it? Probably yes eventually (so kits can evolve primitives without breaking templates), but v1 can ship without it — kits are forked, not shared, so the drift surface is small. Decide before v1.x.
- **Where does the `vars.json` from `/primi-fill` live by default?** Recommend `.primiblocks/runs/<timestamp>/vars.json` for traceability (mirrors `.sc-compose/logs/`) — but this is a UX detail to lock during the skill issue.
- **Should the SOP's "non-developer path" assume Claude Code is installed?** Almost certainly yes — but worth flagging explicitly in the SOP intro.

## Further notes

- ADRs already locked: `docs/adr/0001-bundled-python-renderer-not-sc-compose.md`, `docs/adr/0002-primitives-carry-contracts-that-bubble-up.md`. Glossary at `CONTEXT.md`. New terms or schema additions must land there before code uses them.
- Domain bounds: PrimiBlocks does NOT own any specific domain's primitives. If a contributor proposes adding camera or agent-crew primitives, redirect them to a fork — those belong in `HITL` or `Agent-Builder`.
- The reference kit (`kit/`) is the *only* domain content shipped with PrimiBlocks. Even small additions should be questioned ("does this help the prompt-composition example or just add noise?").
