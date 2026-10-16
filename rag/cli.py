"""Command-line entry point: python -m rag.cli <command>"""

import argparse
import sys

from rag import __version__

COMMANDS = {
    "collect": "Gather system info, event logs and crash reports (issues #2-#4)",
    "index": "Build the searchable index from collected data (issues #5-#6)",
    "refresh": "Collect and index only what's new (issue #7)",
    "search": "Show the evidence retrieved for a question, without an LLM (issue #8)",
    "ask": "Answer a question about your PC (issue #10)",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag",
        description="Ask questions about why your Windows PC crashed.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    for name, help_text in COMMANDS.items():
        p = sub.add_parser(name, help=help_text)
        if name == "collect":
            p.add_argument("--days", type=int, default=30, help="how far back to read event logs (default: 30)")
        if name in ("search", "ask"):
            p.add_argument("question", help="e.g. \"why did my game crash last night?\"")
    return parser


def collect(days: int) -> int:
    from rag.collect import event_logs, system_info

    info = system_info.collect()
    path = system_info.save(info)
    gpus = ", ".join(g["name"] for g in info["gpus"]) or "none found"
    print(f"System info: {info['os']['name']} (build {info['os']['build']}), GPU: {gpus} -> {path}")

    events = event_logs.read_events(days)
    path = event_logs.save(events)
    print(f"Event logs: {len(events)} events from the last {days} days -> {path}")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "collect":
        return collect(args.days)
    print(f"'{args.command}' is not implemented yet.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
