"""Integration tests for the `primiblocks` CLI via subprocess."""

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


def _write_kit(tmp_path: Path) -> Path:
    """Build a fixture kit with one primitive and one template."""
    (tmp_path / "primitives").mkdir(parents=True)
    (tmp_path / "templates").mkdir(parents=True)
    (tmp_path / "primitives" / "greeting.j2").write_text(
        dedent(
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
        encoding="utf-8",
    )
    (tmp_path / "templates" / "letter.j2").write_text(
        dedent(
            """\
            ---
            description: A short letter.
            primitives:
              - greeting
            vars:
              - name: tone
                type: enum
                description: Tone.
                enum: [casual, formal]
            ---
            {% include "primitives/greeting.j2" %}
            ({{ tone }})
            """
        ),
        encoding="utf-8",
    )
    return tmp_path


def _run(*args, cwd=None):
    """Run `python -m primiblocks ...` and capture stdout/stderr/code."""
    return subprocess.run(
        [sys.executable, "-m", "primiblocks", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


# ── render ───────────────────────────────────────────────────────────────

def test_render_to_stdout(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "World", "tone": "casual"}))
    r = _run(
        "render", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
    )
    assert r.returncode == 0, r.stderr
    assert "Hello, World!" in r.stdout
    assert "(casual)" in r.stdout


def test_render_to_out_file(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "World", "tone": "casual"}))
    out_path = tmp_path / "letter.txt"
    r = _run(
        "render", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
        "--out", str(out_path),
    )
    assert r.returncode == 0
    assert "Hello, World!" in out_path.read_text()


def test_render_missing_required_var_exits_1(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run(
        "render", "letter",
        "--kit-dir", str(kit),
    )
    assert r.returncode == 1
    assert "missing required" in r.stderr.lower() or "name" in r.stderr.lower()


def test_render_missing_template_exits_1(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run(
        "render", "does_not_exist",
        "--kit-dir", str(kit),
    )
    assert r.returncode == 1


def test_render_json_mode_success_envelope(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "World", "tone": "casual"}))
    r = _run(
        "render", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
        "--json",
    )
    assert r.returncode == 0
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True
    assert "Hello, World!" in envelope["data"]


def test_render_json_mode_error_envelope(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run(
        "render", "letter",
        "--kit-dir", str(kit),
        "--json",
    )
    assert r.returncode == 1
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is False
    assert "error" in envelope
    assert "message" in envelope["error"]


# ── validate ────────────────────────────────────────────────────────────

def test_validate_with_valid_vars_exits_0(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "X", "tone": "casual"}))
    r = _run(
        "validate", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
    )
    assert r.returncode == 0


def test_validate_with_invalid_vars_exits_1(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "X", "tone": "rude"}))  # not in enum
    r = _run(
        "validate", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
    )
    assert r.returncode == 1
    assert "enum" in r.stderr.lower() or "tone" in r.stderr.lower()


def test_validate_json_mode_success(tmp_path):
    kit = _write_kit(tmp_path)
    vars_path = tmp_path / "vars.json"
    vars_path.write_text(json.dumps({"name": "X", "tone": "casual"}))
    r = _run(
        "validate", "letter",
        "--kit-dir", str(kit),
        "--vars", str(vars_path),
        "--json",
    )
    assert r.returncode == 0
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True


def test_validate_json_mode_error(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run(
        "validate", "letter",
        "--kit-dir", str(kit),
        "--json",
    )
    assert r.returncode == 1
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is False


# ── usage errors (exit 2) ──────────────────────────────────────────────

def test_unknown_subcommand_exits_2(tmp_path):
    r = _run("nonsense")
    assert r.returncode == 2


def test_missing_required_arg_exits_2(tmp_path):
    r = _run("render")  # missing positional template arg
    assert r.returncode == 2


# ── lint ──────────────────────────────────────────────────────────────────

def test_lint_clean_kit_exits_0(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("lint", "--kit-dir", str(kit))
    assert r.returncode == 0


def test_lint_detects_frontmatter_include_drift(tmp_path):
    kit = _write_kit(tmp_path)
    # Add a primitive that's declared in frontmatter but not included in body
    (kit / "primitives" / "extra.j2").write_text(
        dedent(
            """\
            ---
            description: Extra primitive.
            vars:
              - name: x
                type: string
                description: x
            ---
            extra {{ x }}
            """
        ),
        encoding="utf-8",
    )
    # Rewrite letter.j2 to list `extra` in primitives: but not include it
    (kit / "templates" / "letter.j2").write_text(
        dedent(
            """\
            ---
            description: drift test
            primitives:
              - greeting
              - extra
            vars:
              - name: tone
                type: enum
                description: Tone.
                enum: [casual, formal]
            ---
            {% include "primitives/greeting.j2" %}
            """
        ),
        encoding="utf-8",
    )
    r = _run("lint", "--kit-dir", str(kit))
    assert r.returncode == 1
    assert "drift" in r.stderr.lower() or "include" in r.stderr.lower()


def test_lint_detects_broken_include(tmp_path):
    kit = _write_kit(tmp_path)
    # Reference a non-existent primitive
    (kit / "templates" / "letter.j2").write_text(
        dedent(
            """\
            ---
            description: broken
            primitives:
              - greeting
              - nope
            vars:
              - name: tone
                type: enum
                description: Tone.
                enum: [casual]
            ---
            {% include "primitives/greeting.j2" %}
            {% include "primitives/nope.j2" %}
            """
        ),
        encoding="utf-8",
    )
    r = _run("lint", "--kit-dir", str(kit))
    assert r.returncode == 1


def test_lint_json_mode(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("lint", "--kit-dir", str(kit), "--json")
    assert r.returncode == 0
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True


# ── list ──────────────────────────────────────────────────────────────────

def test_list_templates(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("list", "templates", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert "letter" in r.stdout


def test_list_primitives(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("list", "primitives", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert "greeting" in r.stdout


def test_list_templates_json(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("list", "templates", "--kit-dir", str(kit), "--json")
    assert r.returncode == 0
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True
    names = [item["name"] for item in envelope["data"]]
    assert "letter" in names


# ── new ───────────────────────────────────────────────────────────────────

def test_new_template_writes_stub_that_parses(tmp_path):
    kit = tmp_path / "kit"
    r = _run("new", "template", "my_template", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert (kit / "templates" / "my_template.j2").exists()
    # The stub should be parseable + lintable (after we fill the placeholder)
    r2 = _run("list", "templates", "--kit-dir", str(kit))
    assert r2.returncode == 0
    assert "my_template" in r2.stdout


def test_new_primitive_writes_stub_that_parses(tmp_path):
    kit = tmp_path / "kit"
    r = _run("new", "primitive", "my_prim", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert (kit / "primitives" / "my_prim.j2").exists()


def test_new_template_existing_name_fails(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("new", "template", "letter", "--kit-dir", str(kit))
    assert r.returncode == 1
    assert "exists" in r.stderr.lower() or "already" in r.stderr.lower()


# ── doctor ────────────────────────────────────────────────────────────────

def test_doctor_healthy_kit_passes(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("doctor", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert "passed" in r.stdout.lower() or "[ok]" in r.stdout


def test_doctor_missing_kit_fails(tmp_path):
    r = _run("doctor", "--kit-dir", str(tmp_path / "no_such_kit"))
    assert r.returncode == 1


def test_doctor_json_mode(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("doctor", "--kit-dir", str(kit), "--json")
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True
    assert isinstance(envelope["data"]["checks"], list)
    assert all("name" in c and "ok" in c for c in envelope["data"]["checks"])


# ── contract ──────────────────────────────────────────────────────────────

def test_contract_json_shows_effective_contract(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("contract", "letter", "--kit-dir", str(kit), "--json")
    assert r.returncode == 0
    envelope = json.loads(r.stdout)
    assert envelope["ok"] is True
    data = envelope["data"]
    assert data["template"] == "letter"
    assert data["primitives"] == ["greeting"]
    var_names = [v["name"] for v in data["vars"]]
    # `name` from the greeting primitive + `tone` from the template
    assert "name" in var_names
    assert "tone" in var_names


def test_contract_attributes_vars_to_source(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("contract", "letter", "--kit-dir", str(kit), "--json")
    data = json.loads(r.stdout)["data"]
    sources = {v["name"]: v["source"] for v in data["vars"]}
    assert sources["name"] == "greeting"   # from primitive
    assert sources["tone"] == "template"   # template-only var


def test_contract_human_mode_groups_by_source(tmp_path):
    kit = _write_kit(tmp_path)
    r = _run("contract", "letter", "--kit-dir", str(kit))
    assert r.returncode == 0
    assert "Template: letter" in r.stdout
    assert "from greeting" in r.stdout or "greeting" in r.stdout
    assert "tone" in r.stdout
    assert "casual" in r.stdout  # enum value
