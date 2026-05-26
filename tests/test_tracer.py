"""Tracer-bullet tests for the renderer. Proves end-to-end render works.

These tests use the bundled reference `hello` template + primitive in `kit/`.
They are the architectural seed: every subsequent slice extends the modules
exercised here without changing their public interfaces.
"""

from pathlib import Path

import pytest

from primiblocks.errors import PrimiBlocksError
from primiblocks.render import render

KIT_DIR = Path(__file__).parent.parent / "kit"


def test_tracer_renders_hello_world():
    """Rendering the hello template with name=World produces 'Hello, World'."""
    output = render("hello", {"name": "World"}, kit_dir=KIT_DIR)
    assert "Hello, World" in output


def test_tracer_missing_required_var_raises():
    """Rendering the hello template without the required `name` var raises."""
    with pytest.raises(PrimiBlocksError):
        render("hello", {}, kit_dir=KIT_DIR)
