"""The `primiblocks` CLI.

argparse-driven subcommands. Each subcommand supports `--json` for a
`{"ok": bool, "data"?, "error"?}` envelope; in human mode, success goes to
stdout and errors go to stderr. Exit codes:

- 0 — success
- 1 — contract / render / validation / lint error
- 2 — usage error (handled by argparse)
"""

import argparse
import json
import sys
from pathlib import Path

# Force stdout/stderr to UTF-8 on Windows. The default codepage is cp1252,
# which can't encode common characters in error messages (em-dashes, etc.)
# and would crash with UnicodeEncodeError. Safe no-op elsewhere.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

from primiblocks import __version__
from primiblocks.errors import PrimiBlocksError
from primiblocks.lint import lint as run_lint
from primiblocks.primitives import discover as discover_primitives
from primiblocks.render import render
from primiblocks.scaffold import scaffold
from primiblocks.templates import (
    discover as discover_templates,
    effective_contract,
    load_template,
)


def _add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--kit-dir",
        default="kit",
        help="Path to the kit directory (default: ./kit)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="Emit a JSON envelope on stdout instead of human-readable output.",
    )


def _emit_success(json_mode: bool, data, out_path: str | None = None) -> int:
    """Emit success per mode. `data` may be a string or a JSON-serialisable obj."""
    if out_path:
        Path(out_path).write_text(data or "", encoding="utf-8")
    if json_mode:
        print(json.dumps({"ok": True, "data": data}))
    elif data is not None and not out_path:
        if isinstance(data, str):
            sys.stdout.write(data)
            if not data.endswith("\n"):
                sys.stdout.write("\n")
        else:
            print(json.dumps(data, indent=2))
    return 0


def _emit_error(json_mode: bool, message: str, kind: str = "error") -> int:
    if json_mode:
        print(json.dumps({"ok": False, "error": {"kind": kind, "message": message}}))
    else:
        print(f"primiblocks: {message}", file=sys.stderr)
    return 1


def _load_vars(path: str | None) -> dict:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ── render ────────────────────────────────────────────────────────────────

def cmd_render(args: argparse.Namespace) -> int:
    try:
        vars_data = _load_vars(args.vars)
        output = render(args.template, vars_data, kit_dir=Path(args.kit_dir))
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    except (OSError, json.JSONDecodeError) as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    return _emit_success(args.json_mode, output, args.out)


# ── validate ──────────────────────────────────────────────────────────────

def cmd_validate(args: argparse.Namespace) -> int:
    try:
        vars_data = _load_vars(args.vars)
        kit_dir = Path(args.kit_dir)
        template = load_template(args.template, kit_dir)
        primitives_map = discover_primitives(kit_dir)
        contract = effective_contract(template, primitives_map)
        contract.validate(vars_data)
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    except (OSError, json.JSONDecodeError) as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    return _emit_success(args.json_mode, None, None)


# ── lint ──────────────────────────────────────────────────────────────────

def cmd_lint(args: argparse.Namespace) -> int:
    issues = run_lint(Path(args.kit_dir))
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    if args.json_mode:
        payload = {
            "errors": [
                {"code": i.code, "message": i.message, "file": str(i.file) if i.file else None}
                for i in errors
            ],
            "warnings": [
                {"code": i.code, "message": i.message, "file": str(i.file) if i.file else None}
                for i in warnings
            ],
        }
        ok = len(errors) == 0
        if ok:
            print(json.dumps({"ok": True, "data": payload}))
            return 0
        print(json.dumps({"ok": False, "error": {"kind": "lint", "message": "lint errors", "issues": payload}}))
        return 1
    if not issues:
        print("primiblocks: kit lints clean.")
        return 0
    for i in issues:
        prefix = "ERROR" if i.severity == "error" else "warn "
        loc = f" [{i.file}]" if i.file else ""
        print(f"{prefix}  [{i.code}] {i.message}{loc}", file=sys.stderr if i.severity == "error" else sys.stdout)
    return 1 if errors else 0


# ── list ──────────────────────────────────────────────────────────────────

def cmd_list(args: argparse.Namespace) -> int:
    kit_dir = Path(args.kit_dir)
    try:
        if args.what == "templates":
            items = [
                {"name": t.name, "primitives": t.primitives, "vars": [v.name for v in t.contract.vars]}
                for t in discover_templates(kit_dir).values()
            ]
        else:
            items = [
                {"name": p.name, "vars": [v.name for v in p.contract.vars]}
                for p in discover_primitives(kit_dir).values()
            ]
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    if args.json_mode:
        print(json.dumps({"ok": True, "data": items}))
        return 0
    if not items:
        print(f"primiblocks: no {args.what} found in {kit_dir}/")
        return 0
    for item in items:
        if args.what == "templates":
            extras = f" (composes: {', '.join(item['primitives']) or 'none'})"
        else:
            extras = f" (vars: {', '.join(item['vars']) or 'none'})"
        print(f"  {item['name']}{extras}")
    return 0


# ── new ───────────────────────────────────────────────────────────────────

def cmd_new(args: argparse.Namespace) -> int:
    try:
        path = scaffold(args.kind, args.name, kit_dir=Path(args.kit_dir))
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    if args.json_mode:
        print(json.dumps({"ok": True, "data": {"path": str(path)}}))
    else:
        print(f"primiblocks: wrote {path}")
    return 0


# ── contract ──────────────────────────────────────────────────────────────

def cmd_contract(args: argparse.Namespace) -> int:
    """Dump a template's effective contract as JSON. Used by skills to drive
    the fill walkthrough (one question per var, grouped by primitive)."""
    try:
        kit_dir = Path(args.kit_dir)
        template = load_template(args.template, kit_dir)
        primitives_map = discover_primitives(kit_dir)
        contract = effective_contract(template, primitives_map)
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    # Build a grouped view: which primitive contributed each var.
    # Vars contributed by both a primitive and the template (override case)
    # are attributed to the template.
    template_var_names = {v.name for v in template.contract.vars}
    var_to_source: dict[str, str] = {}
    for prim_name in template.primitives:
        if prim_name not in primitives_map:
            continue
        for v in primitives_map[prim_name].contract.vars:
            if v.name in template_var_names:
                continue
            var_to_source.setdefault(v.name, prim_name)
    for v in template.contract.vars:
        var_to_source[v.name] = "template"
    vars_payload = []
    for v in contract.vars:
        vars_payload.append(
            {
                "name": v.name,
                "type": v.type,
                "description": v.description,
                "required": v.required,
                "default": v.default,
                "enum": v.enum,
                "min": v.min,
                "max": v.max,
                "pattern": v.pattern,
                "examples": v.examples,
                "hidden": v.hidden,
                "source": var_to_source.get(v.name, "template"),
            }
        )
    payload = {
        "template": template.name,
        "template_description": (
            template.body.split("\n", 1)[0]
            if not getattr(template, "description", None)
            else template.description
        ),
        "primitives": template.primitives,
        "vars": vars_payload,
    }
    if args.json_mode:
        print(json.dumps({"ok": True, "data": payload}))
    else:
        print(f"Template: {payload['template']}")
        print(f"Composes primitives: {', '.join(payload['primitives']) or 'none'}\n")
        last_source = None
        for v in vars_payload:
            if v["source"] != last_source:
                print(f"-- from {v['source']} --")
                last_source = v["source"]
            req = "required" if v["required"] else f"optional (default: {v['default']!r})"
            extras = []
            if v["enum"]:
                extras.append(f"enum: {v['enum']}")
            if v["min"] is not None:
                extras.append(f"min: {v['min']}")
            if v["max"] is not None:
                extras.append(f"max: {v['max']}")
            if v["pattern"]:
                extras.append(f"pattern: {v['pattern']!r}")
            extras_str = f"  [{'; '.join(extras)}]" if extras else ""
            print(f"  {v['name']}: {v['type']}, {req}{extras_str}")
            print(f"      {v['description']}")
    return 0


# ── doctor ────────────────────────────────────────────────────────────────

def cmd_doctor(args: argparse.Namespace) -> int:
    checks: list[dict] = []
    # Python version
    ok_py = sys.version_info >= (3, 11)
    checks.append(
        {
            "name": "python_version",
            "ok": ok_py,
            "detail": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
    )
    # Deps
    for dep in ("jinja2", "yaml"):
        try:
            __import__(dep)
            checks.append({"name": f"dep_{dep}", "ok": True, "detail": "importable"})
        except ImportError as e:
            checks.append({"name": f"dep_{dep}", "ok": False, "detail": str(e)})
    # Kit dir
    kit_dir = Path(args.kit_dir)
    checks.append(
        {
            "name": "kit_dir_exists",
            "ok": kit_dir.is_dir(),
            "detail": str(kit_dir),
        }
    )
    checks.append(
        {
            "name": "kit_primitives_dir",
            "ok": (kit_dir / "primitives").is_dir(),
            "detail": str(kit_dir / "primitives"),
        }
    )
    checks.append(
        {
            "name": "kit_templates_dir",
            "ok": (kit_dir / "templates").is_dir(),
            "detail": str(kit_dir / "templates"),
        }
    )
    # Lint clean
    try:
        issues = run_lint(kit_dir)
        lint_errors = [i for i in issues if i.severity == "error"]
        checks.append(
            {
                "name": "kit_lint_clean",
                "ok": len(lint_errors) == 0,
                "detail": f"{len(lint_errors)} errors, "
                f"{len(issues) - len(lint_errors)} warnings",
            }
        )
    except Exception as e:
        checks.append(
            {"name": "kit_lint_clean", "ok": False, "detail": f"lint crashed: {e}"}
        )
    overall_ok = all(c["ok"] for c in checks)
    if args.json_mode:
        envelope = {"ok": overall_ok, "data": {"checks": checks}}
        print(json.dumps(envelope))
    else:
        for c in checks:
            mark = "[ok]  " if c["ok"] else "[FAIL]"
            print(f"  {mark}  {c['name']:<24} {c['detail']}")
        print("\nprimiblocks: " + ("all checks passed." if overall_ok else "some checks failed."))
    return 0 if overall_ok else 1


# ── build the argument parser ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="primiblocks",
        description=(
            "PrimiBlocks — render typed, contract-validated templates from a kit "
            "of composable primitives."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"primiblocks {__version__}"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_render = sub.add_parser("render", help="Render a template to stdout or a file.")
    p_render.add_argument("template", help="Template name (without .j2 extension).")
    p_render.add_argument("--vars", help="Path to a JSON file of variable values.")
    p_render.add_argument("--out", help="Write the rendered artifact to this path.")
    _add_common_args(p_render)
    p_render.set_defaults(func=cmd_render)

    p_validate = sub.add_parser(
        "validate",
        help="Validate vars against a template's effective contract without rendering.",
    )
    p_validate.add_argument("template", help="Template name (without .j2 extension).")
    p_validate.add_argument("--vars", help="Path to a JSON file of variable values.")
    _add_common_args(p_validate)
    p_validate.set_defaults(func=cmd_validate)

    p_lint = sub.add_parser("lint", help="Run kit-wide consistency checks.")
    _add_common_args(p_lint)
    p_lint.set_defaults(func=cmd_lint)

    p_list = sub.add_parser("list", help="List templates or primitives in the kit.")
    p_list.add_argument("what", choices=("templates", "primitives"))
    _add_common_args(p_list)
    p_list.set_defaults(func=cmd_list)

    p_new = sub.add_parser("new", help="Scaffold a new template or primitive stub.")
    p_new.add_argument("kind", choices=("template", "primitive"))
    p_new.add_argument("name", help="The name (no extension).")
    _add_common_args(p_new)
    p_new.set_defaults(func=cmd_new)

    p_contract = sub.add_parser(
        "contract",
        help="Dump a template's effective contract (used by skills).",
    )
    p_contract.add_argument("template", help="Template name (without .j2 extension).")
    _add_common_args(p_contract)
    p_contract.set_defaults(func=cmd_contract)

    p_doctor = sub.add_parser(
        "doctor",
        help="Diagnose common problems (Python version, deps, kit health).",
    )
    _add_common_args(p_doctor)
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
