"""Internal: parse YAML frontmatter from a `.j2` file's raw text.

Used by both `templates` and `primitives` to split the leading `---`-fenced
YAML block from the Jinja2 body. Not part of the public API.

Heuristic (0.2.1): the leading `---`-fenced block is treated as frontmatter
ONLY if its content matches a YAML key-value shape (a non-blank line of the
form `<key>: <value>`). This prevents a body that legitimately starts with a
markdown horizontal rule (`---`) from being misinterpreted as frontmatter.
"""

import re

import yaml

from primiblocks.errors import ContractParseError

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)

# Detects "looks like YAML key-value content": at least one line starting
# with `<identifier>: ` (possibly with leading whitespace).
KEY_VALUE_RE = re.compile(r"^\s*[A-Za-z_][\w-]*\s*:", re.MULTILINE)


def split(raw: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). If no frontmatter, returns ({}, raw).

    A leading `---`-fenced block is treated as frontmatter only when its
    inner content matches a YAML key-value shape. This avoids misparsing a
    body that begins with a markdown horizontal rule.
    """
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return ({}, raw)
    inner = match.group(1)
    if not KEY_VALUE_RE.search(inner):
        # Doesn't look like YAML frontmatter — treat as body.
        return ({}, raw)
    try:
        frontmatter = yaml.safe_load(inner) or {}
    except yaml.YAMLError as e:
        raise ContractParseError(f"invalid YAML frontmatter: {e}") from e
    if not isinstance(frontmatter, dict):
        # Parsed but isn't a mapping — heuristic miss; treat as body.
        return ({}, raw)
    return (frontmatter, match.group(2))
