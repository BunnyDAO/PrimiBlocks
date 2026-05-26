"""Stub generators for `primiblocks new template|primitive`."""

from pathlib import Path
from textwrap import dedent

from primiblocks.errors import PrimiBlocksError


TEMPLATE_STUB = dedent(
    """\
    ---
    description: TODO — one-line summary of what this template generates.
    primitives: []
    vars:
      - name: example
        type: string
        description: TODO — describe this variable.
        required: true
    ---
    TODO — Jinja2 body. Use {% include "primitives/X.j2" %} to compose primitives.

    Example: {{ example }}
    """
)


PRIMITIVE_STUB = dedent(
    """\
    ---
    description: TODO — one-line summary of what this primitive emits.
    vars:
      - name: example
        type: string
        description: TODO — describe this variable.
        required: true
    ---
    TODO — Jinja2 body referencing {{ example }} (and any other declared vars).
    """
)


def scaffold(kind: str, name: str, kit_dir: Path) -> Path:
    """Write a stub `<kind>/<name>.j2` under `<kit_dir>/`. Returns the path."""
    kit_dir = Path(kit_dir)
    if kind not in ("template", "primitive"):
        raise PrimiBlocksError(f"unknown kind {kind!r} (expected 'template' or 'primitive')")
    subdir = "templates" if kind == "template" else "primitives"
    target_dir = kit_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.j2"
    if path.exists():
        raise PrimiBlocksError(f"{kind} {name!r} already exists at {path}")
    body = TEMPLATE_STUB if kind == "template" else PRIMITIVE_STUB
    path.write_text(body, encoding="utf-8")
    return path
