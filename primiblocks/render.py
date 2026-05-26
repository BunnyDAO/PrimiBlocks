"""End-to-end render orchestration.

`render(template_name, vars, kit_dir)` loads the named template, discovers
all primitives in the kit, computes the template's effective contract,
validates the supplied vars against it, and then renders the template's
body with a Jinja2 environment rooted at the kit directory (so the body can
`{% include "primitives/<name>.j2" %}` to compose primitives).

Validation runs *before* Jinja renders — bad vars raise a typed
`PrimiBlocksError` subclass without producing partial output.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from primiblocks.primitives import discover as discover_primitives
from primiblocks.templates import effective_contract, load_template


def render(template_name: str, vars: dict, kit_dir: Path) -> str:
    """Render a template by name with the supplied vars.

    Returns the rendered string. Raises a `PrimiBlocksError` subclass on any
    contract violation (missing required var, type mismatch, constraint
    violation) or missing template / primitive.
    """
    kit_dir = Path(kit_dir)
    template = load_template(template_name, kit_dir)
    primitives_map = discover_primitives(kit_dir)
    contract = effective_contract(template, primitives_map)
    validated = contract.validate(vars)
    env = Environment(
        loader=FileSystemLoader(str(kit_dir)),
        autoescape=False,
        keep_trailing_newline=False,
    )
    jinja_template = env.from_string(template.body)
    return jinja_template.render(**validated)
