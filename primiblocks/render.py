"""End-to-end render orchestration.

`render(template_name, vars, kit_dir)` loads the named template, validates
the supplied vars against the template's contract, and renders the template's
body with a Jinja2 environment rooted at the kit directory (so the body can
`{% include "primitives/<name>.j2" %}` to compose primitives).

In 0001 (this slice) the primitive include path is configured but no
primitive-contract aggregation happens; that's 0005's job.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from primiblocks.templates import load_template


def render(template_name: str, vars: dict, kit_dir: Path) -> str:
    """Render a template by name with the supplied vars.

    Returns the rendered string. Raises a `PrimiBlocksError` subclass on any
    contract violation (missing required var, etc.) or missing template.
    """
    kit_dir = Path(kit_dir)
    template = load_template(template_name, kit_dir)
    validated = template.contract.validate(vars)
    env = Environment(
        loader=FileSystemLoader(str(kit_dir)),
        autoescape=False,
        keep_trailing_newline=False,
    )
    jinja_template = env.from_string(template.body)
    return jinja_template.render(**validated)
