"""Unit tests for `primiblocks.contract`. Covers type validation (0002)
and constraint validation (0003) as those slices land."""

import re

import pytest

from primiblocks.contract import Contract
from primiblocks.errors import PrimiBlocksError


# ── 0002 — type system ────────────────────────────────────────────────────

def _contract(*vars_):
    """Helper: build a Contract from a list of var-dicts."""
    return Contract.parse({"vars": list(vars_)})


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
