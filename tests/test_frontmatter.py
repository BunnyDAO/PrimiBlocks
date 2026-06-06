"""Tests for the internal _frontmatter.split helper."""

from primiblocks._frontmatter import split


def test_no_frontmatter_returns_raw_body():
    raw = "Hello, {{ name }}\n"
    assert split(raw) == ({}, raw)


def test_real_frontmatter_returns_dict_and_body():
    raw = "---\ndescription: hi\n---\nbody\n"
    fm, body = split(raw)
    assert fm == {"description": "hi"}
    assert body == "body\n"


def test_body_starting_with_hr_is_not_misparsed_as_frontmatter():
    """0.2.1 #3 — a body that legitimately begins with a markdown horizontal
    rule (`---`) followed by content that doesn't look like YAML must NOT be
    treated as frontmatter."""
    raw = "---\nthis is just text content\n---\nmore content\n"
    fm, body = split(raw)
    assert fm == {}
    assert body == raw


def test_body_with_hr_then_more_dashes_still_not_frontmatter():
    """Even with multiple `---` lines, no key:value pattern means it's body."""
    raw = "---\n\nplain prose\n\n---\n\nmore prose\n"
    fm, body = split(raw)
    assert fm == {}
    assert body == raw


def test_frontmatter_with_complex_yaml_still_parses():
    raw = (
        "---\n"
        "description: a real primitive\n"
        "vars:\n"
        "  - name: x\n"
        "    type: string\n"
        "    description: testing\n"
        "---\n"
        "body content here\n"
    )
    fm, body = split(raw)
    assert fm["description"] == "a real primitive"
    assert len(fm["vars"]) == 1
    assert body == "body content here\n"
