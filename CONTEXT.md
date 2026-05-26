# PrimiBlocks — Glossary

The canonical vocabulary for this project. Terms here are non-negotiable —
code, docs, CLI surface, and skill copy must use them consistently. If a new
term emerges, add it here before using it.

## Primitive

The atomic, parameterized, reusable unit of composition. In practice, a small
Jinja2 partial file with optional frontmatter declaring its own contract.
Primitives know how to do *one thing well* (capture an image, assert a value,
emit a prompt fragment, write a config block). They are domain-specific —
PrimiBlocks itself ships only a small reference set for illustration; real
domain primitives live in *forked* repos.

## Template

A composition of primitives, with YAML frontmatter declaring the variables
that **must** be filled before the template can be rendered. A template
encodes a *shape* (which primitives, in what order, with what wiring); a
filled template encodes a *specific instance* of that shape. Templates are
also domain-specific.

## Contract

The YAML frontmatter section of a template *or* a primitive that declares the
variables it consumes: name, type (string/int/float/bool/list/path/enum),
description, required, default, and optional constraints (enum, min/max,
pattern, examples). The contract is the deterministic guarantee — anything
unfulfilled or invalid blocks the render.

## Effective contract

The aggregate contract for a template at render time: the union of the
template's own declared variables and the variables declared by every
primitive it composes. On name collision, the template's declaration wins
(letting authors override or rename a primitive's exposed variable). The
renderer computes the effective contract before asking the user (or the
fill-skill) for any input.

## Renderer

The Python module bundled inside the PrimiBlocks scaffold that loads templates
and primitives, validates the contract against supplied variables, performs
the Jinja2 composition, and emits the artifact(s). Cross-OS, dependency-light,
script- and CLI-accessible.

## Artifact

The file or files produced by rendering a filled template. The renderer makes
no assumption about artifact language or shape — a Python test, a markdown
prompt, a YAML config, a Terraform file, or a tree of files comprising an
app are all valid artifacts.

## Scaffold

This repository itself, in its forkable form: the renderer, the two skills,
a small reference primitive set, an example template or two, the SOP, and the
CI / cross-OS plumbing. The scaffold is *domain-empty* — it ships the
machinery, not a real primitive library.

## Domain kit

What a stranger produces by forking the scaffold and filling it in: a
primitive library, a template set, and any tooling specific to their domain
(camera testing, agent crews, infra provisioning, content pipelines, etc.).
Domain kits are not part of PrimiBlocks; PrimiBlocks is the framework for
building them.

## Skill

A Claude Code (or compatible) markdown skill that drives a workflow against
the renderer. PrimiBlocks ships two:

- **`/primi-fill`** — given an existing template, walks the user through its
  effective contract one variable at a time, grouped by primitive, validating
  per-answer; previews the rendered artifact and writes it on confirmation.
  (Equivalent role to HITL's `/hitl-test` and Agent-Builder's `/crew-pick`.)
- **`/primi-author`** — composes a *new* template from existing primitives,
  or files a structured primitive-request if the right primitives don't yet
  exist. (Equivalent role to HITL's `/hitl-author` and Agent-Builder's
  `/crew-author`.)

## App

Informal: the deliverable a domain kit's user produces by running the
fill-skill against a template — e.g., a runnable test, an agent prompt, a
config file, a small application. "App" is *not* a renderer concept; the
renderer only knows about artifacts.
