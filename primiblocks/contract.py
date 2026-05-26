"""Contract parsing and validation.

A contract is a list of `Var` declarations parsed from YAML frontmatter.
Each `Var` declares its name, type, description, optional default, and
optional constraints (enum, min, max, pattern, examples). `Contract.validate`
returns a dict of validated values (with defaults applied) or raises a typed
error citing the offending field and the constraint that failed.

Slice history:
- 0001 — skinny: name + required + default
- 0002 — typed validation (string/int/float/bool/list/path/enum)
- 0003 — description required + constraints (enum, min, max, pattern, examples)
"""

import re
from dataclasses import dataclass, field
from typing import Any

from primiblocks.errors import (
    MissingVariableError,
    PrimiBlocksError,
)


VALID_TYPES: frozenset[str] = frozenset(
    {"string", "int", "float", "bool", "list", "path", "enum"}
)


@dataclass
class Var:
    """A single variable declaration from a contract.

    `description` is required by the grammar (drives the fill-skill UX).
    All other optional fields default to None / empty.
    """

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None
    min: float | int | None = None
    max: float | int | None = None
    pattern: str | None = None
    examples: list[Any] = field(default_factory=list)
    hidden: bool = False  # 0.2.0 — UX hint: skills (e.g. /primi-fill) skip asking the user about hidden vars.


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
            if "description" not in v or not str(v.get("description", "")).strip():
                raise PrimiBlocksError(
                    f"variable {name!r}: missing required 'description' "
                    "field in contract"
                )
            parsed.append(
                Var(
                    name=name,
                    type=type_,
                    description=v["description"],
                    required=v.get("required", True),
                    default=v.get("default"),
                    enum=v.get("enum"),
                    min=v.get("min"),
                    max=v.get("max"),
                    pattern=v.get("pattern"),
                    examples=v.get("examples") or [],
                    hidden=bool(v.get("hidden", False)),
                )
            )
        return cls(vars=parsed)

    def validate(self, supplied: dict) -> dict:
        """Return validated vars with defaults applied. Raise on missing
        required, type mismatch, or constraint violation."""
        result: dict[str, Any] = {}
        declared_names = {v.name for v in self.vars}
        for var in self.vars:
            if var.name in supplied:
                value = supplied[var.name]
                _check_type(var.name, var.type, value)
                _check_constraints(var, value)
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


def _check_type(name: str, type_: str, value: Any) -> None:
    """Raise PrimiBlocksError if `value` does not match the declared `type_`.

    Special case: int and float explicitly reject bool, because Python's
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
        if not isinstance(value, str):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'path' (string), got {type(value).__name__}"
            )
    elif type_ == "enum":
        if not isinstance(value, str):
            raise PrimiBlocksError(
                f"variable {name!r} expected type 'enum' (string), got {type(value).__name__}"
            )


def _check_constraints(var: Var, value: Any) -> None:
    """Enforce enum / min / max / pattern constraints. `examples` is informational."""
    if var.enum is not None:
        if value not in var.enum:
            raise PrimiBlocksError(
                f"variable {var.name!r} value {value!r} not in enum {var.enum}"
            )
    if var.type in ("int", "float"):
        if var.min is not None and value < var.min:
            raise PrimiBlocksError(
                f"variable {var.name!r} value {value} below min {var.min}"
            )
        if var.max is not None and value > var.max:
            raise PrimiBlocksError(
                f"variable {var.name!r} value {value} above max {var.max}"
            )
    elif var.type == "list":
        if var.min is not None and len(value) < var.min:
            raise PrimiBlocksError(
                f"variable {var.name!r} list length {len(value)} below min {var.min}"
            )
        if var.max is not None and len(value) > var.max:
            raise PrimiBlocksError(
                f"variable {var.name!r} list length {len(value)} above max {var.max}"
            )
    if var.pattern is not None and var.type in ("string", "enum", "path"):
        if not re.match(var.pattern, value):
            raise PrimiBlocksError(
                f"variable {var.name!r} value {value!r} does not match "
                f"pattern {var.pattern!r}"
            )
