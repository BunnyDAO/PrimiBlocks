"""Template discovery and parsing.

In 0001 (this slice) a Template is a file at `kit/templates/<name>.j2` with
optional YAML frontmatter and a Jinja2 body. Primitive composition and the
effective-contract aggregation arrive in 0005.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from primiblocks.contract import Contract
from primiblocks.errors import PrimiBlocksError, TemplateNotFoundError

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


@dataclass
class Template:
    """One template, parsed."""

    name: str
    contract: Contract
    body: str
    path: Path


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Body is the rest of the file."""
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return ({}, raw)
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        raise PrimiBlocksError(f"invalid YAML frontmatter: {e}") from e
    if not isinstance(frontmatter, dict):
        raise PrimiBlocksError(
            f"frontmatter must be a YAML mapping, got {type(frontmatter).__name__}"
        )
    return (frontmatter, match.group(2))


def load_template(name: str, kit_dir: Path) -> Template:
    """Load a template by name from `<kit_dir>/templates/<name>.j2`."""
    kit_dir = Path(kit_dir)
    path = kit_dir / "templates" / f"{name}.j2"
    if not path.exists():
        raise TemplateNotFoundError(f"template not found: {path}")
    raw = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(raw)
    return Template(
        name=name,
        contract=Contract.parse(frontmatter),
        body=body,
        path=path,
    )
