"""End-to-end render orchestration.

`render(template_name, vars, kit_dir)` loads the named template, discovers
all primitives in the kit, computes the template's effective contract,
validates the supplied vars against it, and then renders the template's
body with a Jinja2 environment rooted at the kit directory (so the body can
`{% include "primitives/<name>.j2" %}` to compose primitives).

Validation runs *before* Jinja renders — bad vars raise a typed
`PrimiBlocksError` subclass without producing partial output.

The Jinja2 loader is a `FrontmatterAwareLoader` that strips YAML
frontmatter from every included file before handing it to Jinja, so a
primitive's contract block never leaks into rendered output.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from primiblocks._frontmatter import split as split_frontmatter
from primiblocks.primitives import discover as discover_primitives
from primiblocks.templates import effective_contract, load_template


class FrontmatterAwareLoader(FileSystemLoader):
    """A Jinja2 loader that strips YAML frontmatter from files it loads.

    Without this, `{% include "primitives/foo.j2" %}` would emit the
    primitive's contract block (the YAML between `---` fences) into the
    rendered output. We split frontmatter from body at load time so Jinja
    only ever sees the body.
    """

    def get_source(self, environment, template):
        source, filename, uptodate = super().get_source(environment, template)
        _, body = split_frontmatter(source)
        return body, filename, uptodate


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
        loader=FrontmatterAwareLoader(str(kit_dir)),
        autoescape=False,
        keep_trailing_newline=False,
    )
    jinja_template = env.from_string(template.body)
    return jinja_template.render(**validated)
