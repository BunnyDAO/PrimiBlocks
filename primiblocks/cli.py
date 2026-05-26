"""The `primiblocks` CLI.

argparse-driven subcommands. Each subcommand supports `--json` for a
`{"ok": bool, "data"?, "error"?}` envelope; in human mode, success goes to
stdout and errors go to stderr. Exit codes:

- 0 — success
- 1 — contract / render / validation error (anything raised as PrimiBlocksError)
- 2 — usage error (handled by argparse)
"""

import argparse
import json
import sys
from pathlib import Path

from primiblocks import __version__
from primiblocks.errors import PrimiBlocksError
from primiblocks.primitives import discover as discover_primitives
from primiblocks.render import render
from primiblocks.templates import effective_contract, load_template


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


def _emit_success(json_mode: bool, data: str | None, out_path: str | None) -> int:
    """Emit success per mode. Returns the intended exit code."""
    if out_path:
        Path(out_path).write_text(data or "", encoding="utf-8")
    if json_mode:
        envelope = {"ok": True, "data": data}
        print(json.dumps(envelope))
    elif data is not None and not out_path:
        sys.stdout.write(data)
        if not data.endswith("\n"):
            sys.stdout.write("\n")
    return 0


def _emit_error(json_mode: bool, message: str, kind: str = "error") -> int:
    """Emit error per mode. Returns exit code 1."""
    if json_mode:
        envelope = {"ok": False, "error": {"kind": kind, "message": message}}
        print(json.dumps(envelope))
    else:
        print(f"primiblocks: {message}", file=sys.stderr)
    return 1


def _load_vars(path: str | None) -> dict:
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_render(args: argparse.Namespace) -> int:
    try:
        vars_data = _load_vars(args.vars)
        output = render(args.template, vars_data, kit_dir=Path(args.kit_dir))
    except PrimiBlocksError as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    except (OSError, json.JSONDecodeError) as e:
        return _emit_error(args.json_mode, str(e), kind=type(e).__name__)
    return _emit_success(args.json_mode, output, args.out)


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
