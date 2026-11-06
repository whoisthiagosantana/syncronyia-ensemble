"""Fixed independent verification; no generated build scripts are executed."""

import hashlib
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .containment import bounded, namespace, run_node
from .contracts import FILES, Rejected, parse


def verify(candidate, repository, config):
    candidate = Path(candidate).resolve()
    before = {f: hashlib.sha256((candidate / f).read_bytes()).hexdigest() for f in FILES}
    acceptance = Path(repository) / "experiments/poc/acceptance"
    results = {}
    try:
        harness = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in acceptance.iterdir() if p.is_file()}
        if harness != config.get("acceptance_sha256"):
            raise Rejected("ACCEPTANCE_HARNESS_CHANGED")
        results["logic"] = parse(run_node(candidate, acceptance))
        deps = config.get("browser_site_packages")
        browsers = config.get("browser_cache")
        if not deps or not browsers:
            raise Rejected("BROWSER_RUNTIME_UNAVAILABLE")
        command = namespace(
            [
                (candidate, "/work", False),
                (acceptance, "/acceptance", False),
                (deps, "/deps", False),
                (browsers, "/browsers", False),
            ]
        )
        command += [
            "--setenv",
            "PYTHONPATH",
            "/deps",
            "--setenv",
            "PLAYWRIGHT_BROWSERS_PATH",
            "/browsers",
            "/usr/bin/python3",
            "/acceptance/browser.py",
        ]
        results["browser"] = parse(bounded(command, timeout=60, memory="768M", diagnostic=True))
        if not results["logic"].get("passed") or not results["browser"].get("passed"):
            raise Rejected("VERIFIER_NOT_PASSED")
        after = {f: hashlib.sha256((candidate / f).read_bytes()).hexdigest() for f in FILES}
        if before != after:
            raise Rejected("CANDIDATE_CHANGED_DURING_VERIFICATION")
        return {"passed": True, "checks": results, "manifest": before, "acceptance_sha256": harness}
    except (Rejected, ValueError) as exc:
        return {
            "passed": False,
            "checks": results,
            "reason": str(exc) if isinstance(exc, Rejected) else "VERIFIER_OUTPUT_INVALID",
            "diagnostic": getattr(exc, "details", ""),
        }


def preview(candidate, port=0):
    """Serve accepted-by-operator artifacts locally with the same restrictive CSP."""

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.split("?", 1)[0] not in ["/"] + ["/" + f for f in FILES]:
                self.send_error(404)
                return
            super().do_GET()

        def end_headers(self):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'",
            )
            self.send_header("X-Content-Type-Options", "nosniff")
            super().end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(candidate)))
    print(json.dumps({"preview_url": "http://127.0.0.1:" + str(server.server_port)}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
