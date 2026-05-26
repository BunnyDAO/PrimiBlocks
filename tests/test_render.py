"""Integration tests for `primiblocks.render.render` — end-to-end."""

from pathlib import Path
from textwrap import dedent

import pytest

from primiblocks.errors import (
    MissingVariableError,
    PrimiBlocksError,
    TemplateNotFoundError,
)
from primiblocks.render import render


def _write_kit(
    tmp_path: Path,
    templates: dict[str, str] | None = None,
    primitives: dict[str, str] | None = None,
) -> Path:
    (tmp_path / "templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "primitives").mkdir(parents=True, exist_ok=True)
    for name, content in (templates or {}).items():
        (tmp_path / "templates" / f"{name}.j2").write_text(content, encoding="utf-8")
    for name, content in (primitives or {}).items():
        (tmp_path / "primitives" / f"{name}.j2").write_text(content, encoding="utf-8")
    return tmp_path


def test_render_composes_multiple_primitives_via_include(tmp_path):
    """Render a template that includes two primitives; output contains both."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "greeting": "Hello, {{ name }}!",
            "signoff": "-- {{ signer }}",
        },
        templates={
            "letter": dedent(
                """\
                ---
                description: A short letter composed from primitives.
                primitives:
                  - greeting
                  - signoff
                vars:
                  - name: name
                    type: string
                    description: Recipient.
                  - name: signer
                    type: string
                    description: Sender.
                ---
                {% include "primitives/greeting.j2" %}

                {% include "primitives/signoff.j2" %}
                """
            ),
        },
    )
    out = render("letter", {"name": "World", "signer": "BunnyDAO"}, kit_dir=kit)
    assert "Hello, World!" in out
    assert "-- BunnyDAO" in out


def test_render_validates_primitive_declared_vars(tmp_path):
    """A var declared by a primitive is required at the template level too."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "retrieval": dedent(
                """\
                ---
                description: Pretends to retrieve N chunks.
                vars:
                  - name: top_k
                    type: int
                    description: How many chunks.
                ---
                retrieved {{ top_k }} chunks
                """
            ),
        },
        templates={
            "rag": dedent(
                """\
                ---
                description: A RAG template.
                primitives:
                  - retrieval
                ---
                {% include "primitives/retrieval.j2" %}
                """
            ),
        },
    )
    with pytest.raises(MissingVariableError, match="top_k"):
        render("rag", {}, kit_dir=kit)


def test_render_rejects_wrong_type_before_jinja_renders(tmp_path):
    """Type mismatch raises before any Jinja2 processing happens."""
    kit = _write_kit(
        tmp_path,
        primitives={},
        templates={
            "x": dedent(
                """\
                ---
                description: Numeric template.
                vars:
                  - name: count
                    type: int
                    description: A count.
                ---
                {{ count }}
                """
            ),
        },
    )
    with pytest.raises(PrimiBlocksError, match="count"):
        render("x", {"count": "not a number"}, kit_dir=kit)


def test_render_rejects_constraint_violation(tmp_path):
    """Constraint violations raise from the renderer (e.g. enum, min/max)."""
    kit = _write_kit(
        tmp_path,
        primitives={},
        templates={
            "tone": dedent(
                """\
                ---
                description: Constrained tone.
                vars:
                  - name: tone
                    type: enum
                    description: Tone.
                    enum: [calm, urgent]
                ---
                {{ tone }}
                """
            ),
        },
    )
    with pytest.raises(PrimiBlocksError, match="enum"):
        render("tone", {"tone": "frantic"}, kit_dir=kit)


def test_render_missing_template_raises(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "primitives").mkdir()
    with pytest.raises(TemplateNotFoundError):
        render("does_not_exist", {}, kit_dir=tmp_path)


def test_render_strips_primitive_frontmatter_from_output(tmp_path):
    """Regression: included primitives must NOT leak their YAML frontmatter
    into the rendered output."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "greeting": dedent(
                """\
                ---
                description: Greets someone.
                vars:
                  - name: name
                    type: string
                    description: Who to greet.
                ---
                Hello, {{ name }}!
                """
            ),
        },
        templates={
            "letter": dedent(
                """\
                ---
                description: A short letter.
                primitives:
                  - greeting
                ---
                {% include "primitives/greeting.j2" %}
                """
            ),
        },
    )
    out = render("letter", {"name": "World"}, kit_dir=kit)
    assert "Hello, World!" in out
    # Frontmatter markers and contract fields must not appear in output.
    assert "---" not in out
    assert "description:" not in out
    assert "type: string" not in out


def test_render_template_overrides_primitive_var_value(tmp_path):
    """When template overrides a primitive var (e.g., tighter bounds), the
    template's constraint is the one enforced."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "ret": dedent(
                """\
                ---
                description: Retrieves.
                vars:
                  - name: top_k
                    type: int
                    description: Loose bounds (primitive).
                    min: 1
                    max: 100
                ---
                k={{ top_k }}
                """
            ),
        },
        templates={
            "rag": dedent(
                """\
                ---
                description: Tighter RAG.
                primitives:
                  - ret
                vars:
                  - name: top_k
                    type: int
                    description: Tight bounds (template).
                    min: 1
                    max: 10
                ---
                {% include "primitives/ret.j2" %}
                """
            ),
        },
    )
    # 50 is allowed by primitive's bounds but rejected by template's tighter bounds.
    with pytest.raises(PrimiBlocksError, match="max"):
        render("rag", {"top_k": 50}, kit_dir=kit)
    # 5 is fine.
    out = render("rag", {"top_k": 5}, kit_dir=kit)
    assert "k=5" in out
