"""
Command-line interface.
"""
import argparse
import json
import os
import sys

def _cmd_preflight(args) -> int:
    print("Preflight check stub.")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fossil-scan", description="FossilScanner CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("preflight", help="Run hardware preflight")
    sp.set_defaults(func=_cmd_preflight)
    return p

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
