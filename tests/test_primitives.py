"""Unit tests for `primiblocks.primitives` — discovery + contract loading."""

from pathlib import Path
from textwrap import dedent

import pytest

from primiblocks.errors import PrimiBlocksError
from primiblocks.primitives import Primitive, discover


def _write_kit(tmp_path: Path, primitives: dict[str, str]) -> Path:
    """Write a fixture kit with given primitive contents. Returns the kit dir."""
    (tmp_path / "primitives").mkdir(parents=True, exist_ok=True)
    for name, content in primitives.items():
        (tmp_path / "primitives" / f"{name}.j2").write_text(content)
    return tmp_path


def test_discover_returns_dict_keyed_by_name(tmp_path):
    kit = _write_kit(
        tmp_path,
        {
            "hello": "Hello\n",
            "goodbye": "Bye\n",
        },
    )
    result = discover(kit)
    assert set(result.keys()) == {"hello", "goodbye"}
    assert all(isinstance(p, Primitive) for p in result.values())


def test_discover_each_primitive_exposes_name_contract_body(tmp_path):
    kit = _write_kit(tmp_path, {"hello": "Hello, {{ name }}\n"})
    p = discover(kit)["hello"]
    assert p.name == "hello"
    assert p.contract is not None  # empty contract for no-frontmatter primitive
    assert "Hello" in p.body


def test_discover_loads_primitive_with_frontmatter_contract(tmp_path):
    content = dedent(
        """\
        ---
        description: Greets someone by name.
        vars:
          - name: name
            type: string
            description: Who to greet.
        ---
        Hello, {{ name }}
        """
    )
    kit = _write_kit(tmp_path, {"hello": content})
    p = discover(kit)["hello"]
    assert len(p.contract.vars) == 1
    assert p.contract.vars[0].name == "name"
    assert p.contract.vars[0].type == "string"


def test_discover_loads_primitive_with_constraints(tmp_path):
    content = dedent(
        """\
        ---
        description: A retrieval block.
        vars:
          - name: top_k
            type: int
            description: How many chunks to retrieve.
            min: 1
            max: 50
            default: 5
            required: false
        ---
        Retrieved: {{ top_k }} chunks
        """
    )
    kit = _write_kit(tmp_path, {"retrieval": content})
    p = discover(kit)["retrieval"]
    assert p.contract.vars[0].min == 1
    assert p.contract.vars[0].max == 50
    assert p.contract.vars[0].default == 5


def test_discover_empty_primitives_dir_returns_empty_dict(tmp_path):
    (tmp_path / "primitives").mkdir()
    assert discover(tmp_path) == {}


def test_discover_missing_primitives_dir_returns_empty_dict(tmp_path):
    """If `kit/primitives/` doesn't exist, return empty — not an error."""
    assert discover(tmp_path) == {}


def test_discover_malformed_frontmatter_raises_with_filename(tmp_path):
    bad = "---\nnot: valid: yaml: at all: nope\n---\nbody\n"
    kit = _write_kit(tmp_path, {"broken": bad})
    with pytest.raises(PrimiBlocksError, match="broken"):
        discover(kit)


def test_discover_var_missing_description_raises_with_filename(tmp_path):
    content = dedent(
        """\
        ---
        description: ok
        vars:
          - name: x
            type: string
        ---
        body
        """
    )
    kit = _write_kit(tmp_path, {"bad": content})
    with pytest.raises(PrimiBlocksError, match="bad"):
        discover(kit)


def test_discover_ignores_non_j2_files(tmp_path):
    kit = _write_kit(tmp_path, {"hello": "Hello\n"})
    (tmp_path / "primitives" / "README.md").write_text("not a primitive")
    result = discover(kit)
    assert "README" not in result
    assert set(result.keys()) == {"hello"}


def test_discover_results_are_deterministic_in_order(tmp_path):
    """Order matters: the fill-skill groups questions by primitive in this order."""
    kit = _write_kit(
        tmp_path,
        {"alpha": "A", "beta": "B", "gamma": "C"},
    )
    keys = list(discover(kit).keys())
    assert keys == sorted(keys)
