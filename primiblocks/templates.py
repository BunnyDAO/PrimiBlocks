"""Template discovery + effective-contract aggregation.

A Template is a `.j2` file under `kit/templates/`. Its YAML frontmatter
declares its own variable contract and an optional `primitives: [...]` list
naming which primitives it composes. The renderer computes the template's
**effective contract** — the union of the template's own vars and each
listed primitive's vars — before validating supplied vars.

ADR-0002: on name collision between a template var and a primitive var, the
template's declaration replaces the primitive's (full override, no
field-level merge). This lets template authors tighten constraints or
rename without forking the primitive.
"""

from dataclasses import dataclass, field
from pathlib import Path

from primiblocks._frontmatter import split as split_frontmatter
from primiblocks.contract import Contract
from primiblocks.errors import PrimiBlocksError, TemplateNotFoundError
from primiblocks.primitives import Primitive


@dataclass
class Template:
    """One template, parsed."""

    name: str
    contract: Contract
    body: str
    path: Path
    primitives: list[str] = field(default_factory=list)


def load_template(name: str, kit_dir: Path) -> Template:
    """Load a template by name from `<kit_dir>/templates/<name>.j2`."""
    kit_dir = Path(kit_dir)
    path = kit_dir / "templates" / f"{name}.j2"
    if not path.exists():
        raise TemplateNotFoundError(f"template not found: {path}")
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(raw)
    primitives_list = list(frontmatter.get("primitives") or [])
    return Template(
        name=name,
        contract=Contract.parse(frontmatter),
        body=body,
        path=path,
        primitives=primitives_list,
    )


def discover(kit_dir: Path) -> dict[str, Template]:
    """Walk `<kit_dir>/templates/*.j2` and return a name-keyed dict.

    Order is deterministic (sorted). Missing `templates/` dir returns empty
    (not an error). Per-template parse failures are surfaced with the
    offending filename.
    """
    kit_dir = Path(kit_dir)
    templates_dir = kit_dir / "templates"
    if not templates_dir.exists():
        return {}
    result: dict[str, Template] = {}
    for path in sorted(templates_dir.glob("*.j2")):
        name = path.stem
        try:
            result[name] = load_template(name, kit_dir)
        except PrimiBlocksError as e:
            raise PrimiBlocksError(f"template {name!r} ({path}): {e}") from e
    return result


def effective_contract(
    template: Template,
    primitives_map: dict[str, Primitive],
) -> Contract:
    """Compute the template's effective contract.

    Aggregates the contracts of every primitive listed in `template.primitives`
    plus the template's own contract. On name collision between a template
    var and a primitive var, the template's declaration replaces the
    primitive's entirely. For collisions between two primitives, the earlier
    primitive in the list wins.

    Raises `PrimiBlocksError` if `template.primitives` lists a primitive that
    is not in `primitives_map`.
    """
    template_var_names = {v.name for v in template.contract.vars}
    aggregated: list = []
    seen: set[str] = set()

    for prim_name in template.primitives:
        if prim_name not in primitives_map:
            raise PrimiBlocksError(
                f"template {template.name!r}: primitives lists unknown "
                f"primitive {prim_name!r}"
            )
        for var in primitives_map[prim_name].contract.vars:
            if var.name in template_var_names:
                # Template's declaration will replace this primitive's var.
                continue
            if var.name not in seen:
                aggregated.append(var)
                seen.add(var.name)

    for var in template.contract.vars:
        if var.name not in seen:
            aggregated.append(var)
            seen.add(var.name)

    return Contract(vars=aggregated)
