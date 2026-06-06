"""Kit-wide consistency checks.

The linter inspects a kit and reports issues without raising at the first
one — useful for kit maintainers iterating on a domain kit. Issues fall in
two severities:

- `error` — something the renderer would refuse at run time
  (drift between `primitives:` frontmatter and `{% include %}` statements,
  broken includes, malformed frontmatter)
- `warning` — something the renderer tolerates but a maintainer should
  know about (orphan primitives, unused vars, primitive-primitive var
  collisions, recursive primitive includes)

Returns a list of `LintIssue` so callers (CLI, doctor) can format as they
wish (human text, JSON).
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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


def _var_referenced_in_body(var_name: str, body: str) -> bool:
    """Heuristic: does the body reference `var_name` anywhere a Jinja2
    expression could see it? Catches `{{ var_name }}`, `{% if var_name %}`,
    `{% for x in var_name %}`, `{% with var_name=... %}`, etc.

    Won't catch dynamic access like `{{ vars[var_name_str] }}`, but those are
    rare and not worth false-positive risk."""
    # Word-boundary match: `var_name` as a token, not as a substring of another.
    pattern = re.compile(r"\b" + re.escape(var_name) + r"\b")
    return bool(pattern.search(body))


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

        # 0.2.1 #4 — Warn on primitive-primitive var collisions where the
        # template doesn't override (template-overridden collisions are an
        # intentional and documented mechanism; primitive-primitive ones are
        # almost always an accident — the later primitive's contract is
        # silently shadowed).
        template_var_names = {v.name for v in template.contract.vars}
        # var_name -> list of primitive_names that declared it
        primitive_decls: dict[str, list[str]] = {}
        for prim_name in template.primitives:
            if prim_name not in primitives_map:
                continue
            for v in primitives_map[prim_name].contract.vars:
                primitive_decls.setdefault(v.name, []).append(prim_name)
        for var_name, prims in primitive_decls.items():
            if len(prims) > 1 and var_name not in template_var_names:
                issues.append(
                    LintIssue(
                        "warning",
                        "primitive-var-collision",
                        f"template {tname!r}: var {var_name!r} is declared by "
                        f"multiple primitives ({prims!r}); first-listed wins. "
                        f"Override at template level to make it explicit.",
                        file=template.path,
                    )
                )

    # 0.2.1 #5 — Warn on declared-but-unreferenced vars in primitives.
    for pname, primitive in primitives_map.items():
        for var in primitive.contract.vars:
            if not _var_referenced_in_body(var.name, primitive.body):
                issues.append(
                    LintIssue(
                        "warning",
                        "unused-var",
                        f"primitive {pname!r}: var {var.name!r} declared in "
                        f"contract but never referenced in body. Likely a "
                        f"stale declaration (rename, removed usage, typo).",
                        file=primitive.path,
                    )
                )

    # 0.2.1 #8 — Warn on recursive primitive includes (primitive body
    # {% include %}s another primitive). The renderer's contract-bubbling
    # only walks templates' primitives: list, not nested primitive
    # includes — so the inner primitive's contract WILL NOT bubble up.
    # This is a v0.2 architectural limit; v0.3.0 may lift it.
    for pname, primitive in primitives_map.items():
        for referenced in INCLUDE_RE.findall(primitive.body):
            issues.append(
                LintIssue(
                    "warning",
                    "recursive-primitive-include",
                    f"primitive {pname!r}: body includes another primitive "
                    f"({referenced!r}). The inner primitive's contract will "
                    f"NOT bubble up — declare it in any template that uses "
                    f"this primitive, or inline its body here.",
                    file=primitive.path,
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
