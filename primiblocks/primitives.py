"""Primitive discovery + contract loading.

A Primitive is a `.j2` file under `kit/primitives/`. It optionally carries
YAML frontmatter declaring its own contract (the vars it consumes). When a
template composes a primitive, the primitive's contract bubbles up into the
template's effective contract (see `templates.effective_contract`, 0005).

Primitives without frontmatter are allowed: their contract is empty and any
variables their body references come from the enclosing template's contract.
"""

from dataclasses import dataclass
from pathlib import Path

from primiblocks._frontmatter import split as split_frontmatter
from primiblocks.contract import Contract
from primiblocks.errors import PrimiBlocksError


@dataclass
class Primitive:
    """One primitive, parsed."""

    name: str
    contract: Contract
    body: str
    path: Path


def discover(kit_dir: Path) -> dict[str, Primitive]:
    """Walk `<kit_dir>/primitives/*.j2` and return a name-keyed dict.

    Order is deterministic (sorted) so the fill-skill can iterate primitives
    in a stable order when grouping its questions. Missing `primitives/` dir
    returns an empty dict (not an error).

    Raises `PrimiBlocksError` (with the offending filename) on any parse
    failure, so the renderer fails fast at discovery rather than at render.
    """
    kit_dir = Path(kit_dir)
    primitives_dir = kit_dir / "primitives"
    if not primitives_dir.exists():
        return {}
    result: dict[str, Primitive] = {}
    for path in sorted(primitives_dir.glob("*.j2")):
        name = path.stem
        raw = path.read_text(encoding="utf-8")
        try:
            frontmatter, body = split_frontmatter(raw)
            contract = Contract.parse(frontmatter)
        except PrimiBlocksError as e:
            raise PrimiBlocksError(
                f"primitive {name!r} ({path}): {e}"
            ) from e
        result[name] = Primitive(
            name=name,
            contract=contract,
            body=body,
            path=path,
        )
    return result
