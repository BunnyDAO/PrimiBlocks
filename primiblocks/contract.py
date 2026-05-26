"""Contract parsing and validation.

A contract is a list of `Var` declarations parsed from YAML frontmatter.
Each `Var` declares its name, type, and (in 0003) constraints. `Contract.validate(supplied)`
returns a dict of validated values (with defaults applied) or raises a typed
error citing the offending field.

Slice history:
- 0001 — skinny: name + required + default
- 0002 — adds typed validation (string/int/float/bool/list/path/enum)
- 0003 — adds description (required) and constraints (enum, min/max, pattern, examples)
"""

from dataclasses import dataclass, field
from typing import Any

from primiblocks.errors import (
    MissingVariableError,
    PrimiBlocksError,
)


VALID_TYPES: frozenset[str] = frozenset(
    {"string", "int", "float", "bool", "list", "path", "enum"}
)


def _check_type(name: str, type_: str, value: Any) -> None:
    """Raise PrimiBlocksError if `value` does not match the declared `type_`.

    Special case: int explicitly rejects bool, because Python's
    `isinstance(True, int)` is True and that's a common silent bug.
    """
    if type_ == "string":
        if not isinstance(value, str):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'string', got {type(value).__name__}"
            )
    elif type_ == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'int', got {type(value).__name__}"
            )
    elif type_ == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'float', got {type(value).__name__}"
            )
    elif type_ == "bool":
        if not isinstance(value, bool):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'bool', got {type(value).__name__}"
            )
    elif type_ == "list":
        if not isinstance(value, list):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'list', got {type(value).__name__}"
            )
    elif type_ == "path":
        # path is string-shaped; filesystem existence is not enforced
        if not isinstance(value, str):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'path' (string), got {type(value).__name__}"
            )
    elif type_ == "enum":
        # In 0002, enum is string-shaped. Allowed-values enforcement is 0003.
        if not isinstance(value, str):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'enum' (string), got {type(value).__name__}"
            )


@dataclass
class Var:
    """A single variable declaration from a contract."""

    name: str
    type: str
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
            name = v["name"]
            if "type" not in v:
                raise PrimiBlocksError(
                    f"variable {name!r}: missing 'type' field in contract"
                )
            type_ = v["type"]
            if type_ not in VALID_TYPES:
                raise PrimiBlocksError(
                    f"variable {name!r}: unknown type {type_!r} "
                    f"(valid: {sorted(VALID_TYPES)})"
                )
            parsed.append(
                Var(
                    name=name,
                    type=type_,
                    required=v.get("required", True),
                    default=v.get("default"),
                )
            )
        return cls(vars=parsed)

    def validate(self, supplied: dict) -> dict:
        """Return validated vars with defaults applied. Raise on missing
        required or type mismatch."""
        result: dict[str, Any] = {}
        declared_names = {v.name for v in self.vars}
        for var in self.vars:
            if var.name in supplied:
                value = supplied[var.name]
                _check_type(var.name, var.type, value)
                result[var.name] = value
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
