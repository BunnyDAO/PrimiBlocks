"""Unit tests for `primiblocks.contract`. Covers type validation (0002)
and constraint validation (0003) as those slices land."""

import re

import pytest

from primiblocks.contract import Contract
from primiblocks.errors import PrimiBlocksError


# ── 0002 — type system ────────────────────────────────────────────────────

def _contract(*vars_):
    """Helper: build a Contract from a list of var-dicts. Auto-injects a
    placeholder `description` (which 0003 makes mandatory) so older type-only
    tests stay readable without re-stating it."""
    enriched = [{"description": "test", **v} for v in vars_]
    return Contract.parse({"vars": enriched})


def test_string_type_accepts_string():
    c = _contract({"name": "name", "type": "string"})
    assert c.validate({"name": "World"}) == {"name": "World"}


def test_string_type_rejects_int():
    c = _contract({"name": "name", "type": "string"})
    with pytest.raises(PrimiBlocksError, match="name"):
        c.validate({"name": 42})


def test_int_type_accepts_int():
    c = _contract({"name": "n", "type": "int"})
    assert c.validate({"n": 5}) == {"n": 5}


def test_int_type_rejects_string():
    c = _contract({"name": "n", "type": "int"})
    with pytest.raises(PrimiBlocksError, match="int"):
        c.validate({"n": "5"})


def test_int_type_rejects_bool_explicitly():
    """Python's `isinstance(True, int)` is True; we must reject bool-as-int."""
    c = _contract({"name": "n", "type": "int"})
    with pytest.raises(PrimiBlocksError):
        c.validate({"n": True})


def test_float_type_accepts_float_and_int():
    c = _contract({"name": "x", "type": "float"})
    assert c.validate({"x": 1.5}) == {"x": 1.5}
    assert c.validate({"x": 2}) == {"x": 2}


def test_float_type_rejects_string():
    c = _contract({"name": "x", "type": "float"})
    with pytest.raises(PrimiBlocksError):
        c.validate({"x": "1.5"})


def test_bool_type_accepts_bool():
    c = _contract({"name": "b", "type": "bool"})
    assert c.validate({"b": True}) == {"b": True}
    assert c.validate({"b": False}) == {"b": False}


def test_bool_type_rejects_int():
    c = _contract({"name": "b", "type": "bool"})
    with pytest.raises(PrimiBlocksError):
        c.validate({"b": 1})


def test_list_type_accepts_list():
    c = _contract({"name": "xs", "type": "list"})
    assert c.validate({"xs": [1, 2, 3]}) == {"xs": [1, 2, 3]}


def test_list_type_rejects_tuple():
    c = _contract({"name": "xs", "type": "list"})
    with pytest.raises(PrimiBlocksError):
        c.validate({"xs": (1, 2, 3)})


def test_path_type_accepts_string():
    """`path` is string-shaped — filesystem existence is not enforced."""
    c = _contract({"name": "p", "type": "path"})
    assert c.validate({"p": "/tmp/does/not/exist"}) == {"p": "/tmp/does/not/exist"}


def test_path_type_rejects_int():
    c = _contract({"name": "p", "type": "path"})
    with pytest.raises(PrimiBlocksError):
        c.validate({"p": 42})


def test_enum_type_accepts_string_for_now():
    """In 0002, enum is treated as string. Allowed-value enforcement is 0003."""
    c = _contract({"name": "e", "type": "enum"})
    assert c.validate({"e": "anything"}) == {"e": "anything"}


def test_unknown_type_rejected_at_parse_time():
    with pytest.raises(PrimiBlocksError, match="unknown type"):
        Contract.parse({"vars": [{"name": "x", "type": "nonsense"}]})


def test_missing_type_rejected_at_parse_time():
    with pytest.raises(PrimiBlocksError, match="missing 'type'"):
        Contract.parse({"vars": [{"name": "x"}]})


def test_type_error_message_cites_field_name():
    c = _contract({"name": "username", "type": "string"})
    with pytest.raises(PrimiBlocksError, match=re.compile(r"username", re.IGNORECASE)):
        c.validate({"username": 99})


# ── 0003 — constraints ──────────────────────────────────────────────────────

def _v(**kw):
    """Helper for 0003 tests: build a var-dict with sensible defaults."""
    kw.setdefault("name", "x")
    kw.setdefault("type", "string")
    kw.setdefault("description", "test var")
    return kw


def test_description_required_on_every_var():
    with pytest.raises(PrimiBlocksError, match="description"):
        Contract.parse({"vars": [{"name": "x", "type": "string"}]})


def test_description_can_be_any_nonempty_string():
    c = Contract.parse({"vars": [_v(description="A short blurb.")]})
    assert c.vars[0].description == "A short blurb."


def test_required_false_allows_missing_with_default():
    c = Contract.parse({"vars": [_v(name="x", type="int", required=False, default=42)]})
    assert c.validate({}) == {"x": 42}


def test_required_false_uses_none_when_no_default_given():
    c = Contract.parse({"vars": [_v(name="x", type="int", required=False)]})
    assert c.validate({}) == {"x": None}


def test_required_true_still_raises_when_missing():
    c = Contract.parse({"vars": [_v(name="x", type="string", required=True)]})
    with pytest.raises(PrimiBlocksError, match="missing required"):
        c.validate({})


def test_enum_accepts_allowed_value():
    c = Contract.parse({"vars": [_v(name="tone", type="enum", enum=["a", "b"])]})
    assert c.validate({"tone": "a"}) == {"tone": "a"}


def test_enum_rejects_disallowed_value():
    c = Contract.parse({"vars": [_v(name="tone", type="enum", enum=["a", "b"])]})
    with pytest.raises(PrimiBlocksError, match="enum"):
        c.validate({"tone": "c"})


def test_enum_on_string_also_works():
    """enum is also valid as a constraint on type:string."""
    c = Contract.parse({"vars": [_v(name="t", type="string", enum=["x", "y"])]})
    assert c.validate({"t": "x"}) == {"t": "x"}
    with pytest.raises(PrimiBlocksError):
        c.validate({"t": "z"})


def test_min_max_on_int_in_range():
    c = Contract.parse({"vars": [_v(name="k", type="int", min=1, max=10)]})
    assert c.validate({"k": 5}) == {"k": 5}


def test_min_max_on_int_below_min():
    c = Contract.parse({"vars": [_v(name="k", type="int", min=1, max=10)]})
    with pytest.raises(PrimiBlocksError, match="min"):
        c.validate({"k": 0})


def test_min_max_on_int_above_max():
    c = Contract.parse({"vars": [_v(name="k", type="int", min=1, max=10)]})
    with pytest.raises(PrimiBlocksError, match="max"):
        c.validate({"k": 11})


def test_min_max_on_float():
    c = Contract.parse({"vars": [_v(name="x", type="float", min=0.0, max=1.0)]})
    assert c.validate({"x": 0.5}) == {"x": 0.5}
    with pytest.raises(PrimiBlocksError):
        c.validate({"x": 1.5})


def test_min_max_on_list_length():
    c = Contract.parse({"vars": [_v(name="xs", type="list", min=2, max=4)]})
    assert c.validate({"xs": [1, 2, 3]}) == {"xs": [1, 2, 3]}
    with pytest.raises(PrimiBlocksError):
        c.validate({"xs": [1]})
    with pytest.raises(PrimiBlocksError):
        c.validate({"xs": [1, 2, 3, 4, 5]})


def test_pattern_matches_string():
    c = Contract.parse(
        {"vars": [_v(name="slug", type="string", pattern=r"^[a-z0-9-]+$")]}
    )
    assert c.validate({"slug": "hello-world-123"}) == {"slug": "hello-world-123"}


def test_pattern_rejects_non_matching_string():
    c = Contract.parse(
        {"vars": [_v(name="slug", type="string", pattern=r"^[a-z0-9-]+$")]}
    )
    with pytest.raises(PrimiBlocksError, match="pattern"):
        c.validate({"slug": "Hello World"})


def test_examples_is_informational_only():
    """examples may be set but never affects validation."""
    c = Contract.parse(
        {"vars": [_v(name="x", type="string", examples=["foo", "bar"])]}
    )
    assert c.validate({"x": "anything-not-in-examples"}) == {
        "x": "anything-not-in-examples"
    }
    assert c.vars[0].examples == ["foo", "bar"]


def test_defaults_applied_before_type_check():
    """A default must satisfy the var's type, but optional var with a default
    should pass validation when the var is omitted."""
    c = Contract.parse(
        {"vars": [_v(name="k", type="int", required=False, default=5)]}
    )
    assert c.validate({}) == {"k": 5}


# ── 0.2.0 — hidden flag ──────────────────────────────────────────────────

def test_hidden_defaults_to_false():
    c = _contract({"name": "x", "type": "string"})
    assert c.vars[0].hidden is False


def test_hidden_parses_when_set_to_true():
    c = Contract.parse({"vars": [_v(name="x", type="string", hidden=True)]})
    assert c.vars[0].hidden is True


def test_hidden_does_not_affect_validation():
    """hidden is a UX hint — validate() still enforces type/constraints."""
    c = Contract.parse(
        {"vars": [_v(name="x", type="int", hidden=True, default=5, required=False)]}
    )
    assert c.validate({}) == {"x": 5}
    assert c.validate({"x": 10}) == {"x": 10}
    with pytest.raises(PrimiBlocksError):
        c.validate({"x": "not-an-int"})
