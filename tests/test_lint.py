"""Unit tests for `primiblocks.lint` warning rules (0.2.1)."""

from pathlib import Path
from textwrap import dedent

from primiblocks.lint import lint


def _write_kit(
    tmp_path: Path,
    primitives: dict[str, str] | None = None,
    templates: dict[str, str] | None = None,
) -> Path:
    (tmp_path / "primitives").mkdir(parents=True, exist_ok=True)
    (tmp_path / "templates").mkdir(parents=True, exist_ok=True)
    for name, content in (primitives or {}).items():
        (tmp_path / "primitives" / f"{name}.j2").write_text(content, encoding="utf-8")
    for name, content in (templates or {}).items():
        (tmp_path / "templates" / f"{name}.j2").write_text(content, encoding="utf-8")
    return tmp_path


def _codes(issues):
    return [i.code for i in issues]


# ── #4 — primitive-primitive var collisions ─────────────────────────────

def test_primitive_var_collision_emits_warning(tmp_path):
    """Two primitives both declare `top_k`; template doesn't override; warn."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "a": dedent(
                """\
                ---
                description: A.
                vars:
                  - name: top_k
                    type: int
                    description: from A
                ---
                {{ top_k }} from A
                """
            ),
            "b": dedent(
                """\
                ---
                description: B.
                vars:
                  - name: top_k
                    type: int
                    description: from B
                ---
                {{ top_k }} from B
                """
            ),
        },
        templates={
            "compose": dedent(
                """\
                ---
                description: composes A and B
                primitives:
                  - a
                  - b
                ---
                {% include "primitives/a.j2" %}
                {% include "primitives/b.j2" %}
                """
            ),
        },
    )
    issues = lint(kit)
    assert "primitive-var-collision" in _codes(issues)


def test_template_override_silences_collision_warning(tmp_path):
    """If the template explicitly overrides the colliding var, no warning."""
    kit = _write_kit(
        tmp_path,
        primitives={
            "a": dedent(
                """\
                ---
                description: A.
                vars:
                  - name: top_k
                    type: int
                    description: from A
                ---
                {{ top_k }} from A
                """
            ),
            "b": dedent(
                """\
                ---
                description: B.
                vars:
                  - name: top_k
                    type: int
                    description: from B
                ---
                {{ top_k }} from B
                """
            ),
        },
        templates={
            "compose": dedent(
                """\
                ---
                description: composes A and B with explicit override
                primitives:
                  - a
                  - b
                vars:
                  - name: top_k
                    type: int
                    description: explicit template override
                ---
                {% include "primitives/a.j2" %}
                {% include "primitives/b.j2" %}
                """
            ),
        },
    )
    issues = lint(kit)
    assert "primitive-var-collision" not in _codes(issues)


# ── #5 — declared-but-unreferenced vars in primitives ──────────────────

def test_unused_var_emits_warning(tmp_path):
    kit = _write_kit(
        tmp_path,
        primitives={
            "p": dedent(
                """\
                ---
                description: declares but never uses unused_var
                vars:
                  - name: used
                    type: string
                    description: this one is used
                  - name: unused_var
                    type: string
                    description: this one is stale
                ---
                Hello, {{ used }}
                """
            ),
        },
        templates={
            "t": dedent(
                """\
                ---
                description: t
                primitives:
                  - p
                ---
                {% include "primitives/p.j2" %}
                """
            ),
        },
    )
    codes = _codes(lint(kit))
    assert "unused-var" in codes


def test_used_vars_dont_emit_unused_warning(tmp_path):
    kit = _write_kit(
        tmp_path,
        primitives={
            "p": dedent(
                """\
                ---
                description: uses both
                vars:
                  - name: a
                    type: string
                    description: a
                  - name: b
                    type: string
                    description: b
                ---
                {{ a }} {{ b }}
                """
            ),
        },
        templates={
            "t": dedent(
                """\
                ---
                description: t
                primitives:
                  - p
                ---
                {% include "primitives/p.j2" %}
                """
            ),
        },
    )
    assert "unused-var" not in _codes(lint(kit))


def test_var_referenced_via_for_loop_counts_as_used(tmp_path):
    kit = _write_kit(
        tmp_path,
        primitives={
            "p": dedent(
                """\
                ---
                description: uses items via for
                vars:
                  - name: items
                    type: list
                    description: list
                ---
                {% for item in items %}- {{ item }}
                {% endfor %}
                """
            ),
        },
        templates={
            "t": dedent(
                """\
                ---
                description: t
                primitives:
                  - p
                ---
                {% include "primitives/p.j2" %}
                """
            ),
        },
    )
    assert "unused-var" not in _codes(lint(kit))


# ── #8 — recursive primitive includes ──────────────────────────────────

def test_recursive_primitive_include_warns(tmp_path):
    kit = _write_kit(
        tmp_path,
        primitives={
            "outer": dedent(
                """\
                ---
                description: includes inner
                vars:
                  - name: x
                    type: string
                    description: x
                ---
                {{ x }}
                {% include "primitives/inner.j2" %}
                """
            ),
            "inner": dedent(
                """\
                ---
                description: leaf
                vars:
                  - name: y
                    type: string
                    description: y
                ---
                {{ y }}
                """
            ),
        },
        templates={
            "t": dedent(
                """\
                ---
                description: t
                primitives:
                  - outer
                  - inner
                ---
                {% include "primitives/outer.j2" %}
                """
            ),
        },
    )
    codes = _codes(lint(kit))
    assert "recursive-primitive-include" in codes
