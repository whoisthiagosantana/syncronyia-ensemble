import copy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ensemble_poc.contracts import FILES, Rejected, materialize, parse, validate_bundle
from ensemble_poc.containment import bounded, namespace


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.bundle = {"files": [{"path": p, "content": "safe"} for p in FILES]}

    def test_atomic_positive(self):
        with tempfile.TemporaryDirectory() as d:
            manifest = materialize(self.bundle, Path(d) / "out")
            self.assertEqual(set(manifest), set(FILES))
            self.assertEqual((Path(d) / "out/game.mjs").read_text(), "safe")
            with self.assertRaises(Rejected):
                materialize(self.bundle, Path(d) / "out")

    def test_forbidden_paths_and_duplicate_no_partial_write(self):
        for path in ["../escape", "/tmp/escape", ".git/config", "tasks/task.md", "ui.mjs"]:
            b = copy.deepcopy(self.bundle)
            b["files"][0]["path"] = path
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(Rejected):
                    materialize(b, Path(d) / "out")
                self.assertEqual(list(Path(d).iterdir()), [])

    def test_symlink_and_encoding(self):
        with tempfile.TemporaryDirectory() as d:
            parent = Path(d) / "link"
            parent.symlink_to(d)
            with self.assertRaises(Rejected):
                materialize(self.bundle, parent / "out")
        self.bundle["files"][0]["content"] = "\ud800"
        with self.assertRaises(Rejected):
            validate_bundle(self.bundle)

    def test_json_controls(self):
        for value in [b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff", b"[" * 10000]:
            with self.assertRaises(Rejected):
                parse(value)

    def test_real_namespace_positive_and_negative(self):
        script = """import os,socket,pathlib
assert not pathlib.Path('/home/thiago').exists()
assert not os.environ.get('ENSEMBLE_SYNTHETIC_SECRET')
pathlib.Path('/tmp/positive').write_text('ok')
try: pathlib.Path('/usr/forbidden').write_text('bad'); raise AssertionError('write escaped')
except PermissionError: pass
except OSError: pass
s=socket.socket();s.settimeout(.2)
try: s.connect(('1.1.1.1',443)); raise AssertionError('network escaped')
except OSError: pass
print('BOUNDARY_OK')
"""
        previous = os.environ.get("ENSEMBLE_SYNTHETIC_SECRET")
        os.environ["ENSEMBLE_SYNTHETIC_SECRET"] = "synthetic-control"
        try:
            out = bounded(namespace() + ["/usr/bin/python3", "-c", script], timeout=5)
        finally:
            if previous is None:
                os.environ.pop("ENSEMBLE_SYNTHETIC_SECRET", None)
            else:
                os.environ["ENSEMBLE_SYNTHETIC_SECRET"] = previous
        self.assertEqual(out.strip(), b"BOUNDARY_OK")

    def test_real_process_tree_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            script = """import os,time,pathlib
if os.fork()==0:
 os.setsid()
 if os.fork()!=0: os._exit(0)
 while True:
  pathlib.Path('/scratch/heartbeat').write_text(str(time.time()));time.sleep(.05)
time.sleep(20)
"""
            with self.assertRaises(Rejected):
                bounded(namespace([(d, "/scratch", True)]) + ["/usr/bin/python3", "-c", script], timeout=1)
            import time

            f = Path(d) / "heartbeat"
            self.assertTrue(f.exists(), "child positive control did not start")
            before = f.read_bytes()
            time.sleep(0.3)
            self.assertEqual(before, f.read_bytes())

    def test_network_positive_control_and_removed_isolation_mutant(self):
        import socket

        with socket.socket() as host:
            host.bind(("127.0.0.1", 0))
            host.listen()
            port = host.getsockname()[1]
            script = f"""import socket
local=socket.socket();local.bind(('127.0.0.1',0));local.listen()
positive=socket.create_connection(local.getsockname(),timeout=1);positive.close()
forbidden=socket.socket();forbidden.settimeout(.3)
try: forbidden.connect(('127.0.0.1',{port}))
except OSError: print('ISOLATION_OK')
else: raise AssertionError('host endpoint reachable')
"""
            isolated = namespace() + ["/usr/bin/python3", "-c", script]
            self.assertEqual(bounded(isolated, timeout=5).strip(), b"ISOLATION_OK")
            mutant = namespace(network=True) + ["/usr/bin/python3", "-c", script]
            with self.assertRaises(Rejected):
                bounded(mutant, timeout=5)

    def test_key_exclusion_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            key = Path(d) / "synthetic-key"
            key.write_text("synthetic-not-a-real-key")
            script = (
                "from pathlib import Path; assert not Path('/host-common/synthetic-key').exists(); print('KEY_ABSENT')"
            )
            self.assertEqual(
                bounded(namespace() + ["/usr/bin/python3", "-c", script], timeout=5).strip(), b"KEY_ABSENT"
            )
            with self.assertRaises(Rejected):
                bounded(namespace([(d, "/host-common", False)]) + ["/usr/bin/python3", "-c", script], timeout=5)

    def test_out_of_band_parent_cancel_stops_bound_child(self):
        import time
        import uuid
        from ensemble_poc.containment import stop_unit, unit_state

        parent = "ensemble-poc-control-" + uuid.uuid4().hex + ".service"
        child = "ensemble-poc-child-" + uuid.uuid4().hex + ".service"
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(
                [
                    "systemd-run",
                    "--user",
                    "--quiet",
                    "--collect",
                    "--unit=" + parent,
                    "--property=RuntimeMaxSec=20",
                    "/usr/bin/sleep",
                    "20",
                ],
                check=True,
            )
            script = "import time,pathlib\nwhile True:\n pathlib.Path('/scratch/beat').write_text(str(time.time()));time.sleep(.05)"
            cmd = [
                "systemd-run",
                "--user",
                "--quiet",
                "--collect",
                "--unit=" + child,
                "--property=BindsTo=" + parent,
                "--property=After=" + parent,
                "--property=KillMode=control-group",
                "--property=RuntimeMaxSec=20",
                "--",
            ]
            try:
                subprocess.run(
                    cmd + namespace([(d, "/scratch", True)]) + ["/usr/bin/python3", "-c", script], check=True
                )
                beat = Path(d) / "beat"
                deadline = time.monotonic() + 3
                while not beat.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(beat.exists(), "bound worker did not start")
                # This trusted path does not depend on the spawning controller.
                stop_unit(parent)
                deadline = time.monotonic() + 3
                while unit_state(child) in {"active", "deactivating"} and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertIn(unit_state(child), {"inactive", "failed"})
                before = beat.read_bytes()
                time.sleep(0.2)
                self.assertEqual(before, beat.read_bytes())
            finally:
                stop_unit(parent)
                stop_unit(child)

    def test_output_flood_is_stopped_before_buffering_everything(self):
        with self.assertRaisesRegex(Rejected, "PROCESS_OUTPUT_LIMIT"):
            bounded(namespace() + ["/usr/bin/python3", "-c", "import os;os.write(1,b'x'*2000000)"], timeout=5)

    def test_user_bus_survives_mcp_filtered_environment(self):
        with patch.dict(os.environ, {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"]}, clear=True):
            out = bounded(namespace() + ["/usr/bin/python3", "-c", "print('FILTERED_ENV_OK')"], timeout=5)
        self.assertEqual(out.strip(), b"FILTERED_ENV_OK")


if __name__ == "__main__":
    unittest.main()
