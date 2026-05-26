# Changelog

All notable changes to PrimiBlocks are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/BunnyDAO/PrimiBlocks/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/BunnyDAO/PrimiBlocks/releases/tag/v0.2.0
[0.1.1]: https://github.com/BunnyDAO/PrimiBlocks/releases/tag/v0.1.1
[0.1.0]: https://github.com/BunnyDAO/PrimiBlocks/releases/tag/v0.1.0
