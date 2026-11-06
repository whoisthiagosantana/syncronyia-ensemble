"""Linux namespace and cgroup wrappers. Missing mechanisms fail closed."""

import os
from pathlib import Path
import shutil
import signal
import selectors
import time
import subprocess
import uuid

from .contracts import Rejected


def control_env():
    """Restore the local user bus when a stdio MCP client filters environment."""
    env = os.environ.copy()
    runtime = Path("/run/user") / str(os.getuid())
    if not runtime.is_dir() or runtime.stat().st_uid != os.getuid() or not (runtime / "bus").is_socket():
        raise Rejected("USER_SYSTEMD_BUS_UNAVAILABLE")
    env["XDG_RUNTIME_DIR"] = str(runtime)
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=" + str(runtime / "bus")
    return env


def namespace(mounts=(), network=False):
    args = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session"]
    if network:
        # Only trusted, tool-free provider CLIs use the host transport.
        args += ["--share-net"]
    for path in ("/usr", "/lib", "/lib64"):
        if Path(path).exists():
            args += ["--ro-bind", path, path]
    args += [
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/home",
        "--dir",
        "/work",
        "--dir",
        "/home/reviewer",
        "--clearenv",
        "--setenv",
        "HOME",
        "/home/reviewer",
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--chdir",
        "/work",
    ]
    if network:
        for path in ("/etc/resolv.conf", "/etc/hosts", "/etc/nsswitch.conf", "/etc/ssl/certs"):
            if Path(path).exists():
                args += ["--ro-bind", path, path]
    for source, dest, writable in mounts:
        args += ["--bind" if writable else "--ro-bind", str(Path(source).resolve()), dest]
    return args


def unit_state(unit):
    r = subprocess.run(
        ["systemctl", "--user", "show", unit, "-p", "ActiveState", "--value"],
        capture_output=True,
        text=True,
        timeout=10,
        env=control_env(),
    )
    if r.returncode:
        raise Rejected("CGROUP_OBSERVATION_UNAVAILABLE")
    return r.stdout.strip()


def stop_unit(unit):
    subprocess.run(["systemctl", "--user", "stop", unit], capture_output=True, timeout=15, env=control_env())
    if unit_state(unit) in {"active", "activating", "deactivating", "reloading"}:
        raise Rejected("TERMINATION_UNCONFIRMED")


def bounded(command, *, data=None, timeout=60, memory="256M", diagnostic=False):
    """Enforce termination independently of the MCP facade, including grandchildren."""
    if data is not None and len(data) > 1048576:
        raise Rejected("PROCESS_INPUT_LIMIT")
    if not shutil.which("bwrap") or not shutil.which("systemd-run"):
        raise Rejected("CONTAINMENT_UNAVAILABLE")
    unit = "ensemble-poc-call-" + uuid.uuid4().hex + ".service"
    argv = [
        "systemd-run",
        "--user",
        "--quiet",
        "--wait",
        "--pipe",
        "--collect",
        "--unit=" + unit,
        "--property=RuntimeMaxSec=" + str(timeout),
        "--property=MemoryMax=" + memory,
        "--property=TasksMax=64",
        "--property=KillMode=control-group",
        "--property=TimeoutStopSec=3",
    ]
    parent = os.environ.get("ENSEMBLE_PARENT_UNIT")
    if parent:
        argv += ["--property=BindsTo=" + parent, "--property=After=" + parent]
    argv += ["--"] + command
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env=control_env(),
    )
    # Bound output while the process is alive, not after buffering it all.
    selector = selectors.DefaultSelector()
    outputs = {proc.stdout: bytearray(), proc.stderr: bytearray()}
    for pipe in outputs:
        os.set_blocking(pipe.fileno(), False)
        selector.register(pipe, selectors.EVENT_READ)
    input_view = memoryview(data or b"")
    os.set_blocking(proc.stdin.fileno(), False)
    if input_view:
        selector.register(proc.stdin, selectors.EVENT_WRITE)
    else:
        proc.stdin.close()
    deadline = time.monotonic() + timeout + 15
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Rejected("PROCESS_TIMEOUT")
            for key, mask in selector.select(min(remaining, 1)):
                pipe = key.fileobj
                if pipe is proc.stdin:
                    try:
                        written = os.write(pipe.fileno(), input_view[:65536])
                    except BrokenPipeError:
                        written = len(input_view)
                    input_view = input_view[written:]
                    if not input_view:
                        selector.unregister(pipe)
                        pipe.close()
                else:
                    chunk = os.read(pipe.fileno(), 65536)
                    if not chunk:
                        selector.unregister(pipe)
                        continue
                    outputs[pipe].extend(chunk)
                    cap = 1048576 if pipe is proc.stdout else 131072
                    if len(outputs[pipe]) > cap:
                        raise Rejected("PROCESS_OUTPUT_LIMIT")
        proc.wait(timeout=5)
    except BaseException:
        try:
            stop_unit(unit)
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=10)
        raise
    finally:
        selector.close()
        for pipe in [proc.stdin, proc.stdout, proc.stderr]:
            if not pipe.closed:
                pipe.close()
    if proc.returncode:
        error = Rejected("ISOLATED_PROCESS_FAILED")
        if diagnostic:
            error.details = bytes(outputs[proc.stderr])[-4000:].decode("utf-8", errors="replace")
        raise error
    return bytes(outputs[proc.stdout])


def run_node(candidate, acceptance, timeout=30):
    node = shutil.which("node")
    if not node:
        raise Rejected("NODE_UNAVAILABLE")
    command = namespace([(candidate, "/work", False), (acceptance, "/acceptance", False), (node, "/node", False)])
    return bounded(
        command + ["/node", "--experimental-vm-modules", "/acceptance/game.test.mjs"], timeout=timeout, diagnostic=True
    )
