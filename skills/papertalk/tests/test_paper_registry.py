from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_registry.py"
sys.path.insert(0, str(SCRIPT.parent))
import paper_registry as registry_module  # noqa: E402

sys.path.pop(0)


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

    def test_remove_is_exact_recoverable_and_clears_active_pointer(self) -> None:
        added = self.run_cli("add", "paper-a", str(self.paper_a))
        namespace = Path(added["namespace"])
        sentinel = namespace / "conversation-state" / "keep.txt"
        sentinel.write_text("preserve the whole namespace\n", encoding="utf-8")

        mismatch = self.run_cli(
            "remove",
            "paper-a",
            "--paper-id",
            "sha256:" + ("0" * 64),
            expected=2,
        )
        self.assertIn("confirmation mismatch", mismatch["error"])
        self.assertTrue(namespace.is_dir())
        self.assertEqual(self.run_cli("resolve", "paper-a")["paper_id"], added["paper_id"])

        removed = self.run_cli(
            "remove", "@paper-a", "--paper-id", added["paper_id"]
        )
        self.assertEqual(removed["status"], "removed")
        self.assertIsNone(removed["active_paper"])
        self.assertTrue(removed["recoverable"])
        self.assertFalse(namespace.exists())
        archive = Path(removed["archive"])
        self.assertEqual(
            (archive / "namespace" / "conversation-state" / "keep.txt").read_text(
                encoding="utf-8"
            ),
            "preserve the whole namespace\n",
        )
        listing = self.run_cli("list")
        self.assertEqual(listing, {"active_paper": None, "papers": []})
        removal_listing = self.run_cli("removed")
        self.assertEqual(len(removal_listing["removals"]), 1)
        self.assertTrue(removal_listing["removals"][0]["restorable"])

        restored = self.run_cli("restore", removed["removal_id"])
        self.assertEqual(restored["status"], "restored")
        self.assertIsNone(restored["active_paper"])
        self.assertTrue(namespace.is_dir())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve the whole namespace\n")
        self.assertEqual(self.run_cli("resolve", "paper-a")["paper_id"], added["paper_id"])
        removal_listing = self.run_cli("removed")
        self.assertFalse(removal_listing["removals"][0]["restorable"])
        self.assertEqual(removal_listing["removals"][0]["status"], "restored")

    def test_removing_inactive_paper_does_not_mutate_other_paper(self) -> None:
        first = self.run_cli("add", "paper-a", str(self.paper_a))
        second = self.run_cli("add", "paper-b", str(self.paper_b))
        first_namespace = Path(first["namespace"])
        first_identity = (first_namespace / "identity.json").read_bytes()

        removed = self.run_cli(
            "remove", "paper-b", "--paper-id", second["paper_id"]
        )
        self.assertEqual(removed["active_paper"], "paper-a")
        self.assertEqual((first_namespace / "identity.json").read_bytes(), first_identity)
        self.assertEqual(self.run_cli("resolve")["alias"], "paper-a")

        restored = self.run_cli("restore", removed["removal_id"], "--activate")
        self.assertEqual(restored["active_paper"], "paper-b")
        self.assertEqual(self.run_cli("resolve")["alias"], "paper-b")
        self.assertEqual((first_namespace / "identity.json").read_bytes(), first_identity)

    def test_removing_active_paper_does_not_select_a_replacement(self) -> None:
        first = self.run_cli("add", "paper-a", str(self.paper_a))
        self.run_cli("add", "paper-b", str(self.paper_b))

        removed = self.run_cli(
            "remove", "paper-a", "--paper-id", first["paper_id"]
        )
        self.assertIsNone(removed["active_paper"])
        listing = self.run_cli("list")
        self.assertIsNone(listing["active_paper"])
        self.assertEqual([paper["alias"] for paper in listing["papers"]], ["paper-b"])
        self.assertFalse(listing["papers"][0]["active"])

    def test_restore_refuses_to_overwrite_reused_alias(self) -> None:
        original = self.run_cli("add", "paper-a", str(self.paper_a))
        removed = self.run_cli(
            "remove", "paper-a", "--paper-id", original["paper_id"]
        )
        replacement = self.run_cli("add", "paper-a", str(self.paper_b))

        error = self.run_cli("restore", removed["removal_id"], expected=2)
        self.assertIn("already registered", error["error"])
        current = self.run_cli("resolve", "paper-a")
        self.assertEqual(current["paper_id"], replacement["paper_id"])
        self.assertNotEqual(current["paper_id"], original["paper_id"])
        removal_listing = self.run_cli("removed")
        self.assertTrue(removal_listing["removals"][0]["restorable"])

    def test_restore_rejects_untrusted_removal_id(self) -> None:
        error = self.run_cli("restore", "../../paper-a", expected=2)
        self.assertIn("Invalid removal_id", error["error"])
        self.assertFalse((self.workspace / "paper-a").exists())

    def test_remove_registry_failure_restores_live_namespace(self) -> None:
        added = self.run_cli("add", "paper-a", str(self.paper_a))
        namespace = Path(added["namespace"])
        original_atomic_write = registry_module.atomic_write_json

        def fail_registry_write(path: Path, value: dict) -> None:
            if path == registry_module.registry_path(self.state.resolve()):
                raise OSError("simulated registry failure")
            original_atomic_write(path, value)

        with mock.patch.object(
            registry_module, "atomic_write_json", side_effect=fail_registry_write
        ):
            with self.assertRaises(registry_module.RegistryError) as raised:
                registry_module.command_remove(
                    self.state.resolve(), "paper-a", added["paper_id"]
                )
        self.assertIn("namespace was restored", str(raised.exception))
        self.assertTrue(namespace.is_dir())
        self.assertEqual(self.run_cli("resolve", "paper-a")["paper_id"], added["paper_id"])

    def test_restore_registry_failure_returns_namespace_to_trash(self) -> None:
        added = self.run_cli("add", "paper-a", str(self.paper_a))
        removed = self.run_cli(
            "remove", "paper-a", "--paper-id", added["paper_id"]
        )
        archive = Path(removed["archive"])
        target = self.state.resolve() / "papers" / "paper-a"
        original_atomic_write = registry_module.atomic_write_json

        def fail_registry_write(path: Path, value: dict) -> None:
            if path == registry_module.registry_path(self.state.resolve()):
                raise OSError("simulated registry failure")
            original_atomic_write(path, value)

        with mock.patch.object(
            registry_module, "atomic_write_json", side_effect=fail_registry_write
        ):
            with self.assertRaises(registry_module.RegistryError) as raised:
                registry_module.command_restore(
                    self.state.resolve(), removed["removal_id"], activate=False
                )
        self.assertIn("returned to trash", str(raised.exception))
        self.assertFalse(target.exists())
        self.assertTrue((archive / "namespace").is_dir())
        self.assertEqual(self.run_cli("list")["papers"], [])

        restored = self.run_cli("restore", removed["removal_id"])
        self.assertEqual(restored["status"], "restored")
        self.assertTrue(target.is_dir())

    def test_restore_retry_recovers_namespace_moved_before_registry_update(self) -> None:
        added = self.run_cli("add", "paper-a", str(self.paper_a))
        removed = self.run_cli(
            "remove", "paper-a", "--paper-id", added["paper_id"]
        )
        archive = Path(removed["archive"])
        target = self.state.resolve() / "papers" / "paper-a"
        (archive / "namespace").replace(target)

        restored = self.run_cli("restore", removed["removal_id"])
        self.assertTrue(restored["recovered_interrupted_transaction"])
        self.assertEqual(self.run_cli("resolve", "paper-a")["paper_id"], added["paper_id"])
        self.assertFalse((archive / "namespace").exists())


if __name__ == "__main__":
    unittest.main()
