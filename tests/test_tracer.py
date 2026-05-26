"""Tracer-bullet smoke tests for the renderer.

Uses a temporary fixture kit (not the real `kit/` reference kit) so these
tests remain stable as the reference kit evolves. The integration tests in
`test_render.py` exercise the same paths more exhaustively; these are the
minimal smoke for the architectural seed (issue 0001).
"""

from pathlib import Path
from textwrap import dedent

import pytest

from primiblocks.errors import MissingVariableError
from primiblocks.render import render


def _build_tracer_kit(tmp_path: Path) -> Path:
    (tmp_path / "primitives").mkdir(parents=True)
    (tmp_path / "templates").mkdir(parents=True)
    (tmp_path / "primitives" / "hello.j2").write_text("Hello, {{ name }}\n")
    (tmp_path / "templates" / "hello.j2").write_text(
        dedent(
            """\
            ---
            description: Tracer-bullet template. Says hello to someone.
            primitives:
              - hello
            vars:
              - name: name
                type: string
                description: Who to greet.
                required: true
            ---
            {% include "primitives/hello.j2" %}
            """
        )
    )
    return tmp_path


def test_tracer_renders_hello_world(tmp_path):
    kit = _build_tracer_kit(tmp_path)
    output = render("hello", {"name": "World"}, kit_dir=kit)
    assert "Hello, World" in output


def test_tracer_missing_required_var_raises(tmp_path):
    kit = _build_tracer_kit(tmp_path)
    with pytest.raises(MissingVariableError):
        render("hello", {}, kit_dir=kit)
