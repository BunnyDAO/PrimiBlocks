# Changelog

All notable changes to PrimiBlocks are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-06-06

### Added

- **`--strict` flag** on `render` and `validate`. When set, raises
  `UnknownVariableError` (code: `unknown_variable`) on supplied vars that
  aren't declared in the effective contract. Default off for backward
  compat; planned default-on in 0.3.0.
- **`DefaultTypeError`** raised at `Contract.parse` time when a var's
  declared `type` and `default` don't match (e.g. `type: int, default: "5"`).
  Catches author bugs at the offending file, not in a confusing Jinja stack.
- **Lint warnings:**
  - `primitive-var-collision` — two primitives declare the same var name
    and the template doesn't override (silent first-wins shadowing).
  - `unused-var` — primitive declares a var that never appears in its body.
  - `recursive-primitive-include` — a primitive body `{% include %}`s
    another primitive (contract bubbling doesn't walk recursively in v0.2).
- **`.github/CODEOWNERS`** routes PR reviews to `@BunnyDAO`.
- **CI lint job** runs `ruff check` + `mypy` against `primiblocks/`.
- **Python 3.14** added to the CI pytest matrix (now 4 versions × 3 OSes).

### Changed

- **Stable error codes** — every `PrimiBlocksError` subclass declares a
  `.code` string attribute (e.g. `missing_variable`, `unknown_variable`,
  `template_not_found`). The CLI's `--json` envelope's `error.kind` is
  renamed to `error.code` and uses these stable strings instead of the
  Python class name. Skills should branch on `code`, not message text.
- **Uniform `--json` envelope shape:**
  - All commands return `{ok, data?, error?}`.
  - `list templates|primitives --json` now returns `data: {kind, items}`
    instead of a bare list.
  - `lint --json` includes `data: {errors, warnings}` regardless of `ok`.
  - `doctor --json` includes `data: {checks}` regardless of `ok`.
- **Skill markdown updated** to consume the normalized envelope shape.
- **Frontmatter heuristic:** leading `---`-fenced blocks are treated as
  frontmatter only when their content matches a YAML key-value shape.
  Bodies that legitimately begin with a markdown horizontal rule no
  longer get misparsed.

### Fixed

- **`Contract.validate` previously silently accepted unknown supplied
  vars.** Still does by default (for backward compat), but `--strict`
  rejects them with `unknown_variable`. Will flip to default-on in 0.3.0.

## [0.2.0] — 2026-05-25

### Added

- **`hidden: true` flag on contract vars.** UX hint for skills: when a template
  author marks a var hidden (typically because the var is set per-include via
  Jinja `{% with %}` blocks and isn't a user-facing input), the fill-skill
  skips asking about it. Validation behavior is unchanged — `hidden` is purely
  a surface-area hint, not a security boundary. Drives the camera-testing-kit
  pattern where templates have ~12 internal primitive overrides and only a
  handful of user-facing inputs (`measurement_points`, etc).

### Changed

- `primiblocks contract <template> --json` envelope now includes a `hidden`
  field on every var entry so skills can branch on it.
- `/primi-fill` SKILL.md updated to skip hidden vars during the walkthrough.

### Fixed

- (none — additive release)

## [0.1.1] — 2026-05-25

Windows portability fix + README aha-example for non-LLM domains. See PR #1.

## [0.1.0] — 2026-05-25

First public release. See [`docs/RELEASE.md`](docs/RELEASE.md) for the full
notes.

### Added

- Python renderer module (`primiblocks/`) with rich typed-contract validation
  (Jinja2 + PyYAML, cross-OS, Python 3.11+).
- `primiblocks` CLI: `render | validate | contract | lint | list | new | doctor`,
  all `--json`-capable.
- Two Claude Code skills: `/primi-fill` (conversational walkthrough) and
  `/primi-author` (compose new templates from primitives).
- Reference LLM-prompt kit: 8 primitives + 3 templates + sample vars.
- Cross-OS CI: macOS / Linux / Windows × Python 3.11 / 3.12 / 3.13.
- SOP and README with 6 v1 SVG diagrams.

[Unreleased]: https://github.com/BunnyDAO/PrimiBlocks/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/BunnyDAO/PrimiBlocks/tree/v0.2.1
[0.2.0]: https://github.com/BunnyDAO/PrimiBlocks/tree/v0.2.0
[0.1.1]: https://github.com/BunnyDAO/PrimiBlocks/tree/v0.1.1
[0.1.0]: https://github.com/BunnyDAO/PrimiBlocks/tree/v0.1.0
