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
        )
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
        )
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
