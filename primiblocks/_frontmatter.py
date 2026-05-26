"""Internal: parse YAML frontmatter from a `.j2` file's raw text.

Used by both `templates` and `primitives` to split the leading `---`-fenced
YAML block from the Jinja2 body. Not part of the public API.
"""

import re

import yaml

from primiblocks.errors import PrimiBlocksError

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


def split(raw: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). If no frontmatter, returns ({}, raw)."""
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
