# ADR 0001 — Bundle a Python renderer instead of depending on sc-compose

**Status:** Accepted
**Date:** 2026-05-25

## Context

PrimiBlocks generalises the template-rendering pattern proven in HITL (camera
testing) and Agent-Builder (Claude Code agent crews). Both of those projects
depend on **`sc-compose`**, a Rust CLI distributed via `brew install
randlee/tap/sc-compose`, to render Jinja2 templates with YAML-frontmatter
contract enforcement.

PrimiBlocks's intent is that **anyone, on any OS, can fork the scaffold and
build their own domain kit.** A brew-installed Rust binary is a hard
portability problem: brew is a poor fit for Windows (and not the default on
Linux), and pre-built `sc-compose` binaries for non-macOS targets are not
something we publish.

## Decision

PrimiBlocks bundles its own renderer, written in Python, inside the scaffold
itself (the `primiblocks/` package). It depends only on Jinja2 and PyYAML
(both pure-Python), targets Python 3.11+, and runs natively on macOS, Linux,
and Windows.

The renderer's contract format and primitive-composition conventions match
sc-compose's where possible, so HITL/Agent-Builder templates port over with
minimal changes; the on-disk shape stays familiar to anyone coming from those
projects.

## Consequences

**Positive**

- Zero non-Python install dependencies; cross-OS portability is automatic.
- Total control of the contract grammar (rich typed frontmatter, primitive
  contract bubbling) without waiting for sc-compose upstream changes.
- Skills can call the renderer programmatically (`from primiblocks import
  render`) rather than shelling out, simplifying error reporting.

**Negative**

- We maintain a parallel implementation. If sc-compose evolves, PrimiBlocks
  may drift.
- Existing sc-compose users porting templates have to learn small grammar
  differences (mostly around the richer frontmatter).
- We give up sc-compose's Rust performance — irrelevant for the rendering
  workloads in scope, but worth naming.

## Alternatives considered

- **Hard-depend on sc-compose**: rejected; fails the cross-OS constraint.
- **Renderer-agnostic with a sc-compose adapter and pure-jinja fallback**:
  rejected; the contract enforcement *is* the value, and a fallback that
  drops it splits the product.
- **Vendor pre-built `sc-compose` binaries for all OSes in the scaffold**:
  rejected; binary distribution + signing burden, plus dependence on a
  third-party publishing pipeline we don't own.
- **Ship as an npm package (Nunjucks-based)**: rejected; introduces
  template-syntax drift from the original Jinja2 templates HITL/Agent-Builder
  produced.
