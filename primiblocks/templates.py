"""Template discovery and parsing.

In 0001 (this slice) a Template is a file at `kit/templates/<name>.j2` with
optional YAML frontmatter and a Jinja2 body. Primitive composition and the
effective-contract aggregation arrive in 0005.
"""

from dataclasses import dataclass
from pathlib import Path

from primiblocks._frontmatter import split as split_frontmatter
from primiblocks.contract import Contract
from primiblocks.errors import TemplateNotFoundError


@dataclass
class Template:
    """One template, parsed."""

    name: str
    contract: Contract
    body: str
    path: Path


def load_template(name: str, kit_dir: Path) -> Template:
    """Load a template by name from `<kit_dir>/templates/<name>.j2`."""
    kit_dir = Path(kit_dir)
    path = kit_dir / "templates" / f"{name}.j2"
    if not path.exists():
        raise TemplateNotFoundError(f"template not found: {path}")
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(raw)
    return Template(
        name=name,
        contract=Contract.parse(frontmatter),
        body=body,
        path=path,
    )
