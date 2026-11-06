"""Explicit local entrypoints; serving MCP never migrates a database."""

import argparse
import json
import sys

from .contracts import Rejected
from .service import Service, load_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("action", choices=["init", "mcp", "worker", "status", "cancel", "reconcile", "preview"])
    parser.add_argument("attempt_id", nargs="?")
    args = parser.parse_args()
    try:
        service = Service(load_config(args.config))
        if args.action == "init":
            service.store.initialize()
            print("LEDGER_READY")
        elif args.action == "mcp":
            from .mcp import serve

            serve(service)
        elif args.action == "preview":
            from .verifier import preview

            preview(service.candidate(args.attempt_id))
        elif args.action == "worker":
            service.work(args.attempt_id)
        else:
            print(json.dumps(getattr(service, args.action)(args.attempt_id)))
    except Exception as exc:
        print(str(exc) if isinstance(exc, Rejected) else "CONTROLLER_UNAVAILABLE", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
