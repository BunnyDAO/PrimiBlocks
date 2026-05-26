# ADR 0002 — Primitives carry their own contracts, which bubble up into templates

**Status:** Accepted
**Date:** 2026-05-25

## Context

In HITL and Agent-Builder, **only templates** declare a contract (the YAML
frontmatter listing required variables). Primitives are dumb Jinja2 partials —
text fragments with no contract of their own. If ten templates compose the same
primitive that consumes a variable `index_name`, all ten templates must
re-declare `index_name` in their own frontmatter. This is redundant,
drift-prone, and conceals which primitive actually consumed the variable.

PrimiBlocks intends primitives to be **truly reusable units** — atomic,
parameterised, and authored independently of any template that composes them.
For the author-skill (`/primi-author`) to compose new templates by picking
primitives off a shelf, it needs to know each primitive's surface area without
inspecting the body.

## Decision

Primitives have their own YAML-frontmatter contracts, using the same grammar
as templates. When a template declares `primitives: [foo, bar, baz]` in its
frontmatter, the renderer computes the template's **effective contract**: the
union of the template's own declared variables and the variables declared by
every listed primitive.

On name collision between a template variable and a primitive variable, the
template's declaration wins. This lets template authors override a primitive's
default, rename a variable, or tighten a constraint, without forking the
primitive.

The fill-skill asks for the *effective contract* in primitive order; the
renderer validates against the effective contract before emitting the
artifact.

## Consequences

**Positive**

- Primitives are DRY — a variable consumed by a primitive is declared once,
  in the primitive itself.
- The author-skill can introspect any primitive and present its surface as a
  picker, without parsing template bodies.
- The fill-skill can group its questions by primitive ("now configuring
  retrieval…"), giving the user a mental scaffold that maps onto the template's
  structure.
- Lintable: the renderer can detect "template lists primitive `foo` but never
  includes it" and vice versa.

**Negative**

- The renderer needs a contract-merging step with collision detection (~150
  extra LOC), versus the single-pass parser HITL/Agent-Builder use.
- A subtle gotcha: the rendered template body must still actually `{% include
  "primitives/foo.j2" %}` for the primitive's text to appear — listing it in
  frontmatter alone doesn't include it. We mitigate via the linter (warns
  when a frontmatter-listed primitive isn't included, and vice versa).

## Alternatives considered

- **Templates own all variables, primitives are dumb fragments**: rejected;
  matches HITL/Agent-Builder but violates DRY and prevents the author-skill
  from being a real composition tool.
- **Primitives have contracts; template explicitly re-exposes vars it wants**:
  rejected; adds a mapping layer and more docs to learn, with marginal
  ergonomic gain over the bubble-up + collision-override model.
- **Pure Jinja includes with no `primitives:` listing**: rejected; the
  author-skill and linter both need an explicit declaration to reason about
  composition.
