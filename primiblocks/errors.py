"""All PrimiBlocks errors. Anything raised by the renderer subclasses
`PrimiBlocksError` so callers (skills, CLI) can catch one type.

Each subclass declares a stable `.code` string attribute. The CLI's
`--json` envelope uses `.code` as `error.kind`, *never* the Python class
name — so renaming or restructuring the error hierarchy doesn't break
downstream consumers (skills, scripts, dashboards) that branch on the kind.
"""


class PrimiBlocksError(Exception):
    """Base class for all PrimiBlocks errors."""

    code: str = "error"


class MissingVariableError(PrimiBlocksError):
    """A required variable was not supplied to the renderer."""

    code = "missing_variable"


class UnknownVariableError(PrimiBlocksError):
    """A supplied variable is not declared in the effective contract.

    Only raised under `--strict`. By default, unknown vars are silently
    passed through (legacy behavior; will flip in v0.3.0).
    """

    code = "unknown_variable"


class TemplateNotFoundError(PrimiBlocksError):
    """The named template was not found in the kit."""

    code = "template_not_found"


class ContractParseError(PrimiBlocksError):
    """A contract's YAML frontmatter is malformed or violates the schema."""

    code = "contract_parse"


class TypeMismatchError(PrimiBlocksError):
    """A supplied value's runtime type doesn't match the declared type."""

    code = "type_mismatch"


class ConstraintViolationError(PrimiBlocksError):
    """A supplied value violates a declared constraint (enum/min/max/pattern)."""

    code = "constraint_violation"


class DefaultTypeError(PrimiBlocksError):
    """A contract var's `default` value doesn't satisfy its declared `type`.

    Raised at parse time so author bugs surface at the offending file, not
    at render time inside a confusing Jinja stack trace.
    """

    code = "default_type"
