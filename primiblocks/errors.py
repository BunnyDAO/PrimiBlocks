"""All PrimiBlocks errors. Anything raised by the renderer subclasses
`PrimiBlocksError` so callers (skills, CLI) can catch one type."""


class PrimiBlocksError(Exception):
    """Base class for all PrimiBlocks errors."""


class MissingVariableError(PrimiBlocksError):
    """A required variable was not supplied to the renderer."""


class TemplateNotFoundError(PrimiBlocksError):
    """The named template was not found in the kit."""
