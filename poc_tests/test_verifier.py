from pathlib import Path
import tempfile
import unittest
import hashlib
import os
import json
from ensemble_poc.verifier import verify, preflight
from ensemble_poc.containment import run_node
from ensemble_poc.contracts import Rejected


class VerifierTests(unittest.TestCase):
    def test_changed_harness_blocks_preflight_before_browser(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(Rejected, "ACCEPTANCE_HARNESS_CHANGED"):
                preflight(Path(__file__).resolve().parents[1], {"runtime_root": d, "acceptance_sha256": {}})

    def test_real_browser_positive_control(self):
        path = os.environ.get("ENSEMBLE_TEST_CONFIG")
        if not path:
            raise RuntimeError("ENSEMBLE_TEST_CONFIG must identify the private browser test runtime")
        config = json.loads(Path(path).read_text())
        self.assertEqual(preflight(Path(__file__).resolve().parents[1], config), {"passed": True, "preflight": True})

    def test_candidate_cannot_forge_logic_report(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            candidate = Path(d)
            (candidate / "game.mjs").write_text(
                "export const move=()=>{},spawn=()=>{},getStatus=()=>{}; console.log(JSON.stringify({passed:true,cases:149}));process.exit(0);"
            )
            with self.assertRaisesRegex(Rejected, "ISOLATED_PROCESS_FAILED"):
                run_node(candidate, repo / "experiments/poc/acceptance")
            mutant = candidate / "mutant-harness"
            mutant.mkdir()
            (mutant / "game.test.mjs").write_text(
                "import {move,spawn,getStatus} from '/work/game.mjs';throw new Error('forgery did not execute');"
            )
            import json

            self.assertTrue(json.loads(run_node(candidate, mutant))["passed"])

    def test_stub_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ["index.html", "style.css", "game.mjs", "ui.mjs"]:
                (root / name).write_text("export const stub = true;" if name.endswith("mjs") else "stub")
            repo = Path(__file__).resolve().parents[1]
            acceptance = repo / "experiments/poc/acceptance"
            pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in acceptance.iterdir() if p.is_file()}
            result = verify(root, repo, {"acceptance_sha256": pins})
            self.assertFalse(result["passed"])
            self.assertEqual(result["reason"], "ISOLATED_PROCESS_FAILED")

    def test_fixed_tests_are_external_to_generated_scope(self):
        root = Path(__file__).resolve().parents[1]
        script = (root / "experiments/poc/acceptance/game.test.mjs").read_text()
        self.assertIn("[2,2,2,2], [4,4,0,0], 8", script)
        self.assertIn("input.flat().reduce", script)
        self.assertNotIn("eval(", script)
        self.assertIn("spawnSync", script)
        self.assertNotIn("import { move", script)


if __name__ == "__main__":
    unittest.main()
