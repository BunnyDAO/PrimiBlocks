---
name: primi-fill
description: Walk the user through filling out a PrimiBlocks template's effective contract one variable at a time (grouped by primitive), preview the rendered artifact, and write it on confirmation. Use when the user types `/primi-fill`, says "fill a template", "render a prompt from the kit", or otherwise wants to drive a template-driven render against the local `kit/` without writing the vars JSON by hand.
---

# /primi-fill

You drive a conversational walkthrough of a PrimiBlocks template, asking the user one question per variable (grouped by primitive), validating each answer, then showing a preview of the rendered artifact before writing it to disk.

**Hard rules:**

- Use the bundled `primiblocks` CLI with `--json` for all renderer interactions. Do NOT import the Python module directly.
- Validate each answer against the variable's type and constraints before moving on. Re-ask on failure with the validator's message.
- Show a preview of the rendered artifact before writing. Do not write without explicit confirmation.

---

## Step 1 — Discover the kit's templates

Run:

```bash
primiblocks list templates --kit-dir <KIT_DIR> --json
```

`<KIT_DIR>` defaults to `./kit` if the user doesn't specify one. The JSON envelope's `data` is a list of `{name, primitives, vars}` objects.

If the list is empty, tell the user: *"No templates found in `<KIT_DIR>/templates/`. Run `primiblocks new template <name>` to scaffold one."* Then stop.

Otherwise, present the templates to the user using `AskUserQuestion`. If there are ≤4 templates, list them as options directly. If there are more, pick the most likely candidates based on the user's stated intent (or ask "which template do you want to fill?" as free text).

## Step 2 — Fetch the template's effective contract

Once the user picks a template `<T>`, run:

```bash
primiblocks contract <T> --kit-dir <KIT_DIR> --json
```

The `data` field gives you `{template, primitives, vars}`. Each var is `{name, type, description, required, default, enum, min, max, pattern, examples, source}`.

`source` is the name of the primitive the var came from, or `"template"` if it was declared at the template level. You will use `source` to group the walkthrough.

## Step 3 — Walk the vars, one at a time, grouped by primitive

Iterate `data.vars` in order (the renderer already sorted them by primitive). **Skip any var where `hidden: true`** — those are intentionally not user-facing (the template author set them via internal `{% with %}` blocks or sensible defaults). When `source` changes (and the next non-hidden var is from a new source), print a short header to anchor the user:

> *"Now configuring the `<source>` block…"*

For each variable, ask the user a single question using the variable's `description` as the prompt and the type/constraints to shape the answer affordance:

| Type / constraint              | Question affordance                                                                          |
|--------------------------------|----------------------------------------------------------------------------------------------|
| `enum` with ≤4 values          | `AskUserQuestion` picker, options = `enum` values (label each with `examples[i]` if useful)  |
| `bool`                         | `AskUserQuestion` picker with `Yes` / `No`                                                   |
| `int` or `float` with min/max  | Plain text question, mention the range: "*(integer, 1–50)*"                                  |
| `string` with `enum`           | `AskUserQuestion` picker if ≤4 values; otherwise plain text + list the allowed values        |
| `string` with `pattern`        | Plain text question, mention the pattern: "*(must match `^[a-z0-9-]+$`)*"                    |
| `list`                         | Plain text question; ask the user to provide a JSON array, or one item per line              |
| Optional var (`required:false`)| Always offer to use the default. Show what the default is: "*(default: `5`)*"                |
| With `examples`                | Show 1–2 examples in the question text: "*(e.g., `prod-docs`, `staging-docs`)*"              |

After each answer:

1. Parse the answer to the declared type (e.g., string → int via `int()` for `type: int`).
2. Validate constraints in-skill: enum membership, min/max bounds, pattern match. If invalid, tell the user *why* and re-ask.
3. Store the validated value in your in-flight `vars` dict.

If the user truly can't answer a non-required var, accept the default (use the var's `default` field, or `null` if no default).

## Step 4 — Persist the vars and render

Once every variable has a value, write the vars dict to:

```
.primiblocks/runs/<timestamp>/vars.json
```

where `<timestamp>` is `YYYYMMDD-HHMMSS` (UTC). Create the directory if it doesn't exist.

Then run:

```bash
primiblocks render <T> --kit-dir <KIT_DIR> --vars .primiblocks/runs/<timestamp>/vars.json --json
```

If the envelope's `ok` is `false`, surface `error.message` to the user. If they can identify a wrong answer, loop back to step 3 for the affected variable. Otherwise abort.

## Step 5 — Preview and confirm before writing

Show the rendered artifact (envelope's `data` field) to the user in a code block. Then ask, via `AskUserQuestion`:

> *"Write this to disk?"*

Options:

- **`Write to <user-chosen path>`** — primary action
- **`Show preview again`** — re-displays without re-rendering
- **`Cancel`** — discard

If the user picks **Write**, ask them for the output path (or suggest a sensible default like `out/<template>-<timestamp>.txt`). Write the rendered content to that path. Print:

> *"Wrote `<path>`. The vars used are persisted at `.primiblocks/runs/<timestamp>/vars.json` for reproducibility."*

If the user picks **Cancel**, tell them the vars JSON is still on disk in case they want to retry: *"Cancelled. Your answers are saved at `.primiblocks/runs/<timestamp>/vars.json`. Re-run `/primi-fill` or call `primiblocks render` directly with that file to retry."*

---

## Failure modes — handle gracefully

- **`primiblocks` not on PATH:** tell the user to `pip install -e .` from the repo root, then retry.
- **No `kit/` directory:** the user is probably outside a PrimiBlocks-forked repo. Tell them to `cd` into their kit.
- **A primitive's `description` is missing (contract parse error):** the kit is malformed. Tell the user to run `primiblocks doctor` and `primiblocks lint` to diagnose.
- **User wants to skip a required var:** refuse politely. Required vars are required — that's the contract. Suggest making the var optional by editing its `required: false` in the template / primitive frontmatter if it shouldn't be required.
