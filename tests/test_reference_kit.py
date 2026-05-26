"""Smoke test for the reference kit shipped with PrimiBlocks.

Renders every template in `kit/templates/` against its sample vars in
`kit/vars.example.json` and asserts the output is non-empty + contains the
expected anchor substrings (proving primitives composed correctly).

Also asserts `primiblocks lint` exits 0 against the live `kit/`.

This test runs in the standard `pytest` invocation and is picked up by the
cross-OS CI matrix.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from primiblocks.render import render
from primiblocks.templates import discover as discover_templates


REPO_ROOT = Path(__file__).parent.parent
KIT_DIR = REPO_ROOT / "kit"


def _load_example_vars() -> dict:
    return json.loads((KIT_DIR / "vars.example.json").read_text(encoding="utf-8"))


# Anchors expected to appear in each template's rendered output.
# These prove the right primitives composed together correctly — not just
# that the renderer produced *something*.
EXPECTED_ANCHORS: dict[str, list[str]] = {
    "rag-qa-prompt": [
        "Senior PostgreSQL DBA",            # from system_persona
        "Retrieved context",                 # from retrieval_block heading
        "postgres-docs",                     # from retrieval_block via index_name
        "Task",                              # from task_instruction heading
        "Output format",                     # from output_format_markdown heading
        "How do I diagnose slow index",      # from template-level var `question`
    ],
    "agent-tool-using-prompt": [
        "Code Review Agent",                 # system_persona
        "Tool examples: `flag_issue`",       # tool_use_examples
        "Guardrails",                        # guardrail_refusal
        "Review the diff at PR #123",        # template-level `user_request`
    ],
    "eval-judge-prompt": [
        "LLM Output Judge",                  # system_persona
        "Examples",                          # few_shot_block heading
        "Reference response",                # template-level
        "Candidate response",                # template-level
    ],
}


@pytest.fixture(scope="module")
def example_vars() -> dict:
    return _load_example_vars()


@pytest.fixture(scope="module")
def template_names() -> list[str]:
    return sorted(discover_templates(KIT_DIR).keys())


def test_all_templates_have_example_vars(example_vars, template_names):
    """Every template in kit/templates/ has a matching entry in vars.example.json."""
    missing = [t for t in template_names if t not in example_vars]
    assert not missing, f"templates with no example vars: {missing}"


def test_all_example_vars_correspond_to_real_templates(example_vars, template_names):
    """Every entry in vars.example.json corresponds to a real template
    (catches stale examples for removed templates)."""
    orphans = [k for k in example_vars if k not in template_names]
    assert not orphans, f"vars.example.json has entries for missing templates: {orphans}"


@pytest.mark.parametrize("template_name", list(EXPECTED_ANCHORS.keys()))
def test_reference_template_renders_with_example_vars(template_name, example_vars):
    """Each reference template renders cleanly against its example vars and
    contains the expected anchor substrings."""
    vars_for_template = example_vars[template_name]
    output = render(template_name, vars_for_template, kit_dir=KIT_DIR)
    assert output, f"{template_name} rendered empty output"
    for anchor in EXPECTED_ANCHORS[template_name]:
        assert anchor in output, (
            f"{template_name}: expected anchor {anchor!r} not in output. "
            f"Got (first 500 chars):\n{output[:500]}"
        )


def test_reference_kit_lints_clean():
    """`primiblocks lint` exits 0 against the live kit/."""
    r = subprocess.run(
        [sys.executable, "-m", "primiblocks", "lint", "--kit-dir", str(KIT_DIR)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (
        f"lint failed:\nstdout={r.stdout}\nstderr={r.stderr}"
    )
