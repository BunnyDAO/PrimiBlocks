"""Kit-wide consistency checks.

The linter inspects a kit and reports issues without raising at the first
one — useful for kit maintainers iterating on a domain kit. Issues fall in
two severities:

- `error` — something the renderer would refuse at run time
  (drift between `primitives:` frontmatter and `{% include %}` statements,
  broken includes, malformed frontmatter)
- `warning` — something the renderer tolerates but a maintainer should
  know about (e.g., primitives that aren't composed by any template)

Returns a list of `LintIssue` so callers (CLI, doctor) can format as they
wish (human text, JSON).
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from primiblocks._frontmatter import split as split_frontmatter
from primiblocks.errors import PrimiBlocksError
from primiblocks.primitives import discover as discover_primitives
from primiblocks.templates import discover as discover_templates


# Matches {% include "primitives/<name>.j2" %} (single- or double-quoted, with
# optional whitespace inside the tag).
INCLUDE_RE = re.compile(
    r"""\{%\s*include\s*['"]primitives/([a-zA-Z0-9_\-]+)\.j2['"]\s*%\}"""
)


Severity = Literal["error", "warning"]


@dataclass
class LintIssue:
    severity: Severity
    code: str
    message: str
    file: Path | None = None


def lint(kit_dir: Path) -> list[LintIssue]:
    """Walk the kit and return a list of issues. Empty list means clean."""
    kit_dir = Path(kit_dir)
    issues: list[LintIssue] = []

    # Discover primitives — collect parse errors as issues, don't raise.
    primitives_map = {}
    try:
        primitives_map = discover_primitives(kit_dir)
    except PrimiBlocksError as e:
        issues.append(LintIssue("error", "primitive-parse", str(e)))

    # Discover templates — same.
    templates_map = {}
    try:
        templates_map = discover_templates(kit_dir)
    except PrimiBlocksError as e:
        issues.append(LintIssue("error", "template-parse", str(e)))

    template_primitive_refs: set[str] = set()

    for tname, template in templates_map.items():
        declared = set(template.primitives)
        included = set(INCLUDE_RE.findall(template.body))
        template_primitive_refs |= included

        # Drift: declared but not included
        for missing_include in declared - included:
            issues.append(
                LintIssue(
                    "error",
                    "frontmatter-include-drift",
                    f"template {tname!r}: primitives lists {missing_include!r} "
                    "but body does not {% include %} it",
                    file=template.path,
                )
            )

        # Drift: included but not declared
        for missing_decl in included - declared:
            issues.append(
                LintIssue(
                    "error",
                    "frontmatter-include-drift",
                    f"template {tname!r}: body includes primitive "
                    f"{missing_decl!r} but it is not in the primitives: list",
                    file=template.path,
                )
            )

        # Broken include — references a primitive not on disk
        for referenced in declared | included:
            if referenced not in primitives_map:
                issues.append(
                    LintIssue(
                        "error",
                        "broken-include",
                        f"template {tname!r}: references primitive "
                        f"{referenced!r} which does not exist in kit/primitives/",
                        file=template.path,
                    )
                )

    # Warning: orphan primitives (no template composes them)
    for pname in primitives_map:
        if pname not in template_primitive_refs:
            issues.append(
                LintIssue(
                    "warning",
                    "orphan-primitive",
                    f"primitive {pname!r} is not composed by any template",
                    file=primitives_map[pname].path,
                )
            )

    return issues
