"""Command-line entry point for LLM Verify."""

import argparse
from collections.abc import Sequence

import uvicorn


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="benchmarker",
        description="Run the LLM Verify API service.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve = subparsers.add_parser("serve", help="Start the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "serve":
        parser.print_help()
        return 0

    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
