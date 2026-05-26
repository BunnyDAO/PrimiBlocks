"""Contract parsing and validation.

In 0001 (this slice) the contract is intentionally skinny: each variable has
a name and an optional `required` flag (default true) and `default` value.
Types, descriptions, and constraints (enum/min/max/pattern/examples) arrive
in 0002 and 0003.
"""

from dataclasses import dataclass, field
from typing import Any

from primiblocks.errors import MissingVariableError


@dataclass
class Var:
    """A single variable declaration from a contract."""

    name: str
    required: bool = True
    default: Any = None


@dataclass
class Contract:
    """Aggregated variable declarations parsed from frontmatter."""

    vars: list[Var] = field(default_factory=list)

    @classmethod
    def parse(cls, frontmatter: dict | None) -> "Contract":
        """Build a Contract from a parsed YAML frontmatter dict."""
        if not frontmatter:
            return cls(vars=[])
        raw_vars = frontmatter.get("vars") or []
        parsed: list[Var] = []
        for v in raw_vars:
            parsed.append(
                Var(
                    name=v["name"],
                    required=v.get("required", True),
                    default=v.get("default"),
                )
            )
        return cls(vars=parsed)

    def validate(self, supplied: dict) -> dict:
        """Return a dict of supplied vars with defaults applied for missing
        optional vars. Raise `MissingVariableError` for missing required vars."""
        result: dict[str, Any] = {}
        declared_names = {v.name for v in self.vars}
        for var in self.vars:
            if var.name in supplied:
                result[var.name] = supplied[var.name]
            elif not var.required:
                result[var.name] = var.default
            else:
                raise MissingVariableError(
                    f"missing required variable: {var.name!r}"
                )
        for k, v in supplied.items():
            if k not in declared_names:
                result[k] = v
        return result
