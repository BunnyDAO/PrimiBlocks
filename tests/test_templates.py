"""Unit tests for `primiblocks.templates` — discovery + effective contract."""

from pathlib import Path
from textwrap import dedent

import pytest

from primiblocks.errors import PrimiBlocksError, TemplateNotFoundError
from primiblocks.primitives import discover as discover_primitives
from primiblocks.templates import (
    Template,
    discover,
    effective_contract,
    load_template,
)


def _write_kit(
    tmp_path: Path,
    templates: dict[str, str] | None = None,
    primitives: dict[str, str] | None = None,
) -> Path:
    """Write a fixture kit with given template and primitive contents."""
    (tmp_path / "templates").mkdir(parents=True, exist_ok=True)
    (tmp_path / "primitives").mkdir(parents=True, exist_ok=True)
    for name, content in (templates or {}).items():
        (tmp_path / "templates" / f"{name}.j2").write_text(content)
    for name, content in (primitives or {}).items():
        (tmp_path / "primitives" / f"{name}.j2").write_text(content)
    return tmp_path


# ── discover() ──────────────────────────────────────────────────────────────

def test_discover_returns_dict_keyed_by_name(tmp_path):
    kit = _write_kit(tmp_path, templates={"alpha": "A", "beta": "B"})
    result = discover(kit)
    assert set(result.keys()) == {"alpha", "beta"}
    assert all(isinstance(t, Template) for t in result.values())


def test_discover_empty_templates_dir_returns_empty_dict(tmp_path):
    (tmp_path / "templates").mkdir()
    assert discover(tmp_path) == {}


def test_template_primitives_list_parsed_from_frontmatter(tmp_path):
    content = dedent(
        """\
        ---
        description: A composing template.
        primitives:
          - greeting
          - signoff
        ---
        {% include "primitives/greeting.j2" %}
        {% include "primitives/signoff.j2" %}
        """
    )
    kit = _write_kit(tmp_path, templates={"compose": content})
    t = discover(kit)["compose"]
    assert t.primitives == ["greeting", "signoff"]


def test_template_with_no_primitives_field_has_empty_primitives_list(tmp_path):
    content = dedent(
        """\
        ---
        description: A standalone template.
        ---
        Hello!
        """
    )
    kit = _write_kit(tmp_path, templates={"solo": content})
    t = discover(kit)["solo"]
    assert t.primitives == []


# ── load_template() ─────────────────────────────────────────────────────────

def test_load_template_missing_raises_template_not_found(tmp_path):
    (tmp_path / "templates").mkdir()
    with pytest.raises(TemplateNotFoundError):
        load_template("nope", tmp_path)


# ── effective_contract() ────────────────────────────────────────────────────

def test_effective_contract_no_primitives_returns_template_contract(tmp_path):
    template_content = dedent(
        """\
        ---
        description: A standalone template.
        vars:
          - name: title
            type: string
            description: The title.
        ---
        # {{ title }}
        """
    )
    kit = _write_kit(tmp_path, templates={"solo": template_content})
    t = discover(kit)["solo"]
    eff = effective_contract(t, {})
    assert [v.name for v in eff.vars] == ["title"]


def test_effective_contract_unions_template_and_primitive_vars(tmp_path):
    primitive_content = dedent(
        """\
        ---
        description: A retrieval block.
        vars:
          - name: top_k
            type: int
            description: How many chunks to retrieve.
        ---
        retrieve {{ top_k }}
        """
    )
    template_content = dedent(
        """\
        ---
        description: A RAG prompt.
        primitives:
          - retrieval
        vars:
          - name: question
            type: string
            description: The user question.
        ---
        {% include "primitives/retrieval.j2" %}
        Q: {{ question }}
        """
    )
    kit = _write_kit(
        tmp_path,
        templates={"rag": template_content},
        primitives={"retrieval": primitive_content},
    )
    t = discover(kit)["rag"]
    primitives_map = discover_primitives(kit)
    eff = effective_contract(t, primitives_map)
    names = [v.name for v in eff.vars]
    # primitive vars come first (their order), then template-only vars
    assert names == ["top_k", "question"]


def test_effective_contract_template_var_replaces_primitive_var_on_collision(tmp_path):
    """ADR-0002: template wins on name collision (full replace, not merge)."""
    primitive_content = dedent(
        """\
        ---
        description: A retrieval block.
        vars:
          - name: top_k
            type: int
            description: From primitive — default 5.
            default: 5
            min: 1
            max: 50
        ---
        retrieve {{ top_k }}
        """
    )
    template_content = dedent(
        """\
        ---
        description: A constrained RAG prompt.
        primitives:
          - retrieval
        vars:
          - name: top_k
            type: int
            description: From template — tighter bounds.
            default: 3
            min: 1
            max: 10
        ---
        {% include "primitives/retrieval.j2" %}
        """
    )
    kit = _write_kit(
        tmp_path,
        templates={"rag": template_content},
        primitives={"retrieval": primitive_content},
    )
    t = discover(kit)["rag"]
    primitives_map = discover_primitives(kit)
    eff = effective_contract(t, primitives_map)
    top_k = [v for v in eff.vars if v.name == "top_k"]
    assert len(top_k) == 1  # not duplicated
    # template's declaration wins (description + max are template's)
    assert "template" in top_k[0].description
    assert top_k[0].max == 10
    assert top_k[0].default == 3


def test_effective_contract_unknown_primitive_raises(tmp_path):
    template_content = dedent(
        """\
        ---
        description: References a missing primitive.
        primitives:
          - does_not_exist
        ---
        body
        """
    )
    kit = _write_kit(tmp_path, templates={"broken": template_content})
    t = discover(kit)["broken"]
    primitives_map = discover_primitives(kit)
    with pytest.raises(PrimiBlocksError, match="does_not_exist"):
        effective_contract(t, primitives_map)


def test_effective_contract_multiple_primitives_var_order_follows_primitive_order(tmp_path):
    """The fill-skill groups questions by primitive in this order."""
    prim_a = dedent(
        """\
        ---
        description: First.
        vars:
          - name: a
            type: string
            description: from A
        ---
        """
    )
    prim_b = dedent(
        """\
        ---
        description: Second.
        vars:
          - name: b
            type: string
            description: from B
        ---
        """
    )
    template_content = dedent(
        """\
        ---
        description: composes A then B
        primitives:
          - a_prim
          - b_prim
        vars:
          - name: t
            type: string
            description: template-only
        ---
        body
        """
    )
    kit = _write_kit(
        tmp_path,
        templates={"compose": template_content},
        primitives={"a_prim": prim_a, "b_prim": prim_b},
    )
    t = discover(kit)["compose"]
    primitives_map = discover_primitives(kit)
    eff = effective_contract(t, primitives_map)
    assert [v.name for v in eff.vars] == ["a", "b", "t"]
