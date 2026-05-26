# Diagrams

This directory holds the diagrams referenced from the project's top-level
`README.md` and `SOP.md`.

## Format policy

- **Rendered images** (the ones `README.md` and `SOP.md` reference): `.svg`
  (primary) and `.png` (fallback, for GitHub renderers that occasionally
  cache SVG poorly).
- **Sources** (editable originals): in `src/`, one `.excalidraw` per
  diagram. The `.excalidraw` file is JSON — you open it in
  [Excalidraw](https://excalidraw.com/) (web or VS Code extension), edit,
  and export the result as `.svg` (and optionally `.png`) back into this
  directory.

**No mermaid blocks. No ASCII art. Real images, committed.**

## Current state — v1 vector sketches

The `.svg` files currently in this directory are **functional v1 vector
sketches** authored programmatically — they show the right shapes,
relationships, and labels, but they don't have the polished
hand-drawn Excalidraw aesthetic the SOP/README ultimately aim for.

To upgrade a diagram to the polished aesthetic:

1. Open or create `src/<diagram>.excalidraw` in Excalidraw.
2. Rebuild the diagram in Excalidraw, matching the v1 SVG's structure
   (or improving it).
3. Export as `<diagram>.svg` (and `<diagram>.png` if desired) into this
   directory, replacing the v1 file.
4. Commit both the updated `.svg` and the `.excalidraw` source.

## Diagram inventory

| File                                            | Used by    | What it shows                                                                                |
|-------------------------------------------------|------------|----------------------------------------------------------------------------------------------|
| `3-layer-architecture.svg`                      | README     | Primitives → Templates → Skills → Renderer → Artifact: the conceptual stack at a glance.     |
| `any-artifact-format.svg`                       | README     | Same framework, three radically different domains: LLM prompt vs camera `.seqx` vs camera pytest `.py`. |
| `fork-and-customize-lifecycle.svg`              | README     | The 6-step "Use this template → fork → replace `kit/` → first `/primi-fill`" experience.      |
| `effective-contract-aggregation.svg`            | SOP        | How a template's `primitives: [...]` list aggregates into the effective contract.            |
| `primi-fill-flow.svg`                           | SOP        | The 7-step fill-skill walkthrough.                                                            |
| `primi-author-flow.svg`                         | SOP        | The author-skill flow (pick primitives → override → write template, or file a request).      |
| `renderer-module-dep-graph.svg`                 | SOP        | `errors` → `contract` → `{primitives, templates}` → `render` → `cli` — contributor reference. |
