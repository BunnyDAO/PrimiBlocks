---
name: primi-author
description: Compose a new PrimiBlocks template from existing primitives in the local kit, or file a structured primitive-request when the needed primitives don't yet exist. Use when the user types `/primi-author`, says "build a new template", "compose primitives", "I need a template that does X", or asks to extend the kit.
---

# /primi-author

You author a new template by selecting primitives from the kit, ordering them, optionally overriding their declared variables, and writing a lint-clean `.j2` file to `kit/templates/`. When the user's intent requires primitives that don't exist, you file a structured request markdown for a developer to fulfill instead of trying to fake it.

**Hard rules:**

- Use the `primiblocks` CLI with `--json` for all discovery. Do not import the Python module directly.
- The new template MUST lint clean (`primiblocks lint` exits 0) before you tell the user it's ready.
- If a needed primitive doesn't exist, write `kit/requests/<slug>.md` and tell the user — never invent a primitive in a template body that doesn't have a backing file.

---

## Step 1 — Listen to the user's intent

Get a free-text description of what the user wants the template to do. The whole point of `/primi-author` (vs. `/primi-fill`) is that the user wants a *new shape* — different primitives, different order, different overrides — not just to fill an existing template.

Restate the intent back to them in one sentence to confirm before you go shopping for primitives.

## Step 2 — Discover available primitives

Run:

```bash
primiblocks list primitives --kit-dir <KIT_DIR> --json
```

The envelope's `data` is a list of `{name, vars}` objects. Hold this list.

If the kit is empty (no primitives), this skill can't compose anything. Tell the user to first author primitives directly (or file requests for them) and stop.

## Step 3 — Match intent → primitives (pick + order)

Walk the user through *which* primitives belong in the new template and *what order* they should appear in. For each candidate primitive, fetch its full contract surface so the user can decide:

```bash
# (Optional, helpful for the user) Inspect a primitive's contract directly:
cat kit/primitives/<name>.j2 | head -50
```

Present picks to the user as an `AskUserQuestion` if there are ≤4 plausible primitives; otherwise propose an ordered list and ask the user to confirm or rearrange.

If, during this step, the user describes a primitive that doesn't exist in `kit/primitives/`, **stop and go to step 5**. Don't invent a primitive in the template body without a backing file — `primiblocks lint` will reject it and the renderer will fail.

## Step 4a — Override primitive vars (optional)

For each selected primitive, ask whether any of its declared variables should be **overridden** in the new template's frontmatter. Common reasons to override:

- Tighten a constraint (narrow an `enum`, lower a `max`)
- Change a default
- Rename a variable for clarity in this template's context
- Lock a constant value (`required: false`, `default: <fixed value>`)

If the user has no overrides, skip this — the primitives' contracts will bubble up as-is.

## Step 4b — Add template-level vars (optional)

Ask whether the new template needs any extra variables on top of what the primitives declare (e.g., a `user_question` or `criterion` slot that the template body interpolates directly).

For each, capture: `name`, `type`, `description`, `required`, `default?`, plus any constraints (enum/min/max/pattern/examples).

## Step 5 — IF a needed primitive doesn't exist: file a request

When the user's intent requires a primitive that isn't in `kit/primitives/`, write a structured request to:

```
kit/requests/<slug>.md
```

The file format:

```markdown
# Primitive request: <name>

**Filed by:** /primi-author
**Filed for:** <user-described template intent>

## Why this primitive is needed

<1–3 sentences explaining the gap — what the user wants to do that
no existing primitive supports.>

## Proposed contract

```yaml
description: <one-line summary of what this primitive emits>
vars:
  - name: <name>
    type: <string|int|float|bool|list|path|enum>
    description: <what this variable controls>
    required: true
    # plus constraints as appropriate (enum, min, max, pattern, default, examples)
```

## Suggested body (informal)

<A short prose description of the Jinja2 body, or a draft. Don't worry
about getting Jinja syntax perfect — a developer will polish.>

## Templates that would compose this primitive

- <template name> (this one)
- <any others the user mentions>
```

After writing the request, tell the user: *"I've filed `kit/requests/<slug>.md`. The new template can't be authored until a developer adds the primitive. Want me to also draft the template stub for later, or stop here?"*

If they say "draft the stub", proceed to step 6 but leave the missing primitive as a TODO comment in the body and add it to `primitives:` anyway, with a `<!-- request: kit/requests/<slug>.md -->` comment. The template won't lint clean until the primitive lands — be honest about that.

## Step 6 — Write the new template

Compose the template content:

- **Frontmatter** with `description`, `primitives:` (the ordered list), `vars:` (the overrides + new template-level vars)
- **Body** that `{% include "primitives/<name>.j2" %}`s each primitive in the order the user chose, with any template-level vars interpolated at sensible positions (typically *after* the included primitives, since primitives often set context that the template uses)

Use `primiblocks new template <name>` to scaffold first, then overwrite with the composed content. (`new` ensures the path is reserved and the file is in the right location.)

## Step 7 — Verify lint clean + offer a fill walkthrough

Run:

```bash
primiblocks lint --kit-dir <KIT_DIR> --json
```

If lint reports any errors against the new template, surface them to the user and fix together. Common issues:

- `frontmatter-include-drift` — `primitives:` and `{% include %}` don't agree → fix the body or the frontmatter
- `broken-include` — referenced primitive doesn't exist → file a request (step 5) or rename to the right primitive

Once lint is clean, tell the user:

> *"Authored `kit/templates/<name>.j2` — lint clean. Want me to run `/primi-fill` against it now to verify it renders end-to-end?"*

If they say yes, hand off to `/primi-fill` with the new template's name pre-selected.

---

## Failure modes

- **No `kit/` directory:** the user is outside a PrimiBlocks-forked repo. `cd` into their kit and retry.
- **Template name collides with an existing template:** `primiblocks new` will refuse. Ask the user for a different name or to delete the existing one first.
- **User tries to compose primitives in nonsensical order** (e.g., output-format primitive before task instruction): point it out and suggest the conventional order: *persona → context → task → examples → output format → guardrails → user input*. They can override if they have a reason.
