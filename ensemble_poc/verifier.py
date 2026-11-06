"""Fixed independent verification; no generated build scripts are executed."""

import hashlib
import json
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .containment import bounded, namespace, run_node
from .contracts import FILES, Rejected, parse


def acceptance_hashes(repository, config):
    acceptance = Path(repository) / "experiments/poc/acceptance"
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in acceptance.iterdir() if p.is_file()}
    if hashes != config.get("acceptance_sha256"):
        raise Rejected("ACCEPTANCE_HARNESS_CHANGED")
    return hashes


def browser_check(candidate, repository, config, *, preflight=False):
    acceptance = Path(repository) / "experiments/poc/acceptance"
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
    if preflight:
        command += ["--preflight"]
    return parse(bounded(command, timeout=60, memory="768M", tasks=256, diagnostic=True))


def preflight(repository, config):
    acceptance_hashes(repository, config)
    with tempfile.TemporaryDirectory(prefix="browser-positive-", dir=config["runtime_root"]) as work:
        result = browser_check(work, repository, config, preflight=True)
    if result != {"passed": True, "preflight": True}:
        raise Rejected("BROWSER_POSITIVE_CONTROL_FAILED")
    return result


def verify(candidate, repository, config):
    candidate = Path(candidate).resolve()
    before = {f: hashlib.sha256((candidate / f).read_bytes()).hexdigest() for f in FILES}
    acceptance = Path(repository) / "experiments/poc/acceptance"
    results = {}
    try:
        harness = acceptance_hashes(repository, config)
        results["logic"] = parse(run_node(candidate, acceptance))
        results["browser"] = browser_check(candidate, repository, config)
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
