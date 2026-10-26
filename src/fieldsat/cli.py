"""Command line entry point: pick the data source, then serve over stdio."""

import argparse
import logging
import os
import sys

from fieldsat.runtime import create_demo_server, create_live_server


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="fieldsat", description="Serve field evidence over MCP.")
    parser.add_argument(
        "--demo",
        action="store_true",
        default=os.environ.get("STEMLINK_MCP_DEMO") == "1",
        help="Serve fixed demo numbers instead of calling Copernicus and Open-Meteo.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    # Logs go to stderr. With stdio, stdout carries the protocol and nothing else.
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    mcp = create_demo_server() if args.demo else create_live_server()
    logging.info("data source: %s", "demo fixtures" if args.demo else "live providers")
    mcp.run(transport="stdio", show_banner=False)
