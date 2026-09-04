from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_registry.py"


class RegistryCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.state = self.workspace / "state"
        self.paper_a = self.workspace / "paper-a.txt"
        self.paper_b = self.workspace / "paper-b.txt"
        self.paper_a.write_text("rho means incumbent\n", encoding="utf-8")
        self.paper_b.write_text("rho means target\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str, expected: int = 0) -> dict:
        process = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.state), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(process.returncode, expected, process.stderr or process.stdout)
        output = process.stdout if expected == 0 else process.stderr
        return json.loads(output)

    def test_aliases_have_isolated_namespaces_and_active_scope(self) -> None:
        added_a = self.run_cli("add", "Paper-A", str(self.paper_a))
        added_b = self.run_cli("add", "paper-b", str(self.paper_b))

        self.assertEqual(added_a["alias"], "paper-a")
        self.assertEqual(added_a["active_paper"], "paper-a")
        self.assertNotEqual(added_a["paper_id"], added_b["paper_id"])

        namespace_a = Path(added_a["namespace"])
        namespace_b = Path(added_b["namespace"])
        self.assertNotEqual(namespace_a, namespace_b)
        self.assertTrue((namespace_a / "identity.json").is_file())
        self.assertTrue((namespace_b / "identity.json").is_file())

        (namespace_a / "paper-model.md").write_text("incumbent\n", encoding="utf-8")
        (namespace_b / "paper-model.md").write_text("target\n", encoding="utf-8")
        self.assertEqual((namespace_a / "paper-model.md").read_text(), "incumbent\n")
        self.assertEqual((namespace_b / "paper-model.md").read_text(), "target\n")

        self.run_cli("use", "@paper-b")
        one_off = self.run_cli("resolve", "@paper-a")
        self.assertEqual(one_off["alias"], "paper-a")
        self.assertEqual(one_off["active_paper"], "paper-b")
        self.assertEqual(self.run_cli("resolve")["alias"], "paper-b")

    def test_collision_is_rejected_without_mutating_existing_entry(self) -> None:
        original = self.run_cli("add", "paper-a", str(self.paper_a))
        error = self.run_cli("add", "@PAPER-A", str(self.paper_b), expected=2)
        self.assertIn("already registered", error["error"])
        resolved = self.run_cli("resolve", "paper-a")
        self.assertEqual(resolved["paper_id"], original["paper_id"])

    def test_same_source_under_two_aliases_keeps_distinct_owners(self) -> None:
        first = self.run_cli("add", "first", str(self.paper_a))
        second = self.run_cli("add", "second", str(self.paper_a))

        self.assertEqual(first["paper_id"], second["paper_id"])
        self.assertNotEqual(first["namespace"], second["namespace"])
        first_identity = json.loads(
            (Path(first["namespace"]) / "identity.json").read_text(encoding="utf-8")
        )
        second_identity = json.loads(
            (Path(second["namespace"]) / "identity.json").read_text(encoding="utf-8")
        )
        self.assertEqual(first_identity["alias"], "first")
        self.assertEqual(second_identity["alias"], "second")

    def test_owner_mismatch_fails_closed(self) -> None:
        added = self.run_cli("add", "paper-a", str(self.paper_a))
        identity_path = Path(added["namespace"]) / "identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["paper_id"] = "sha256:" + ("0" * 64)
        identity_path.write_text(json.dumps(identity), encoding="utf-8")

        error = self.run_cli("resolve", "paper-a", expected=2)
        self.assertIn("owner mismatch", error["error"])

    def test_invalid_alias_cannot_escape_state_directory(self) -> None:
        error = self.run_cli("add", "../paper", str(self.paper_a), expected=2)
        self.assertIn("Alias must be", error["error"])
        self.assertFalse((self.workspace / "paper").exists())

    def test_verify_checks_every_registered_namespace(self) -> None:
        self.run_cli("add", "paper-a", str(self.paper_a))
        self.run_cli("add", "paper-b", str(self.paper_b))
        result = self.run_cli("verify")
        self.assertEqual([paper["alias"] for paper in result["papers"]], ["paper-a", "paper-b"])


if __name__ == "__main__":
    unittest.main()
