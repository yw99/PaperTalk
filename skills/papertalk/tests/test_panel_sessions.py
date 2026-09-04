from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REGISTRY = SKILL / "scripts" / "paper_registry.py"
PANELS = SKILL / "scripts" / "panel_sessions.py"


class PanelSessionCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.state = self.workspace / "state"
        self.paper = self.workspace / "paper.txt"
        self.paper.write_text("A small target paper.\n", encoding="utf-8")
        self.added = self.run_cli(REGISTRY, "add", "demo", str(self.paper))
        self.namespace = Path(self.added["namespace"])
        self.owner = {"alias": "demo", "paper_id": self.added["paper_id"]}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(
        self,
        script: Path,
        *arguments: str,
        payload: dict | None = None,
        expected: int = 0,
    ) -> dict:
        process = subprocess.run(
            [sys.executable, str(script), "--root", str(self.state), *arguments],
            input=json.dumps(payload) if payload is not None else None,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(process.returncode, expected, process.stderr or process.stdout)
        output = process.stdout if expected == 0 else process.stderr
        return json.loads(output)

    def write_json(self, relative: str, value: dict) -> None:
        path = self.namespace / relative
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def write_jsonl(self, relative: str, records: list[dict]) -> None:
        path = self.namespace / relative
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

    def make_author_ready(self) -> None:
        source = {
            "source_id": "src-paper",
            "owner": self.owner,
            "author_id": "paper",
            "url_or_path": str(self.paper),
            "title": "Demo paper",
            "source_type": "P",
            "publication_date": "2026-01-01",
            "retrieved_at": "2026-09-04T12:00:00+00:00",
            "primary_or_secondary": "primary",
            "identity_match_evidence": ["paper author list"],
            "target_relevance": "target paper",
            "content_location": ["§1"],
        }
        claim = {
            "claim_id": "claim-1",
            "owner": self.owner,
            "author_id": "author-1",
            "claim": "The author makes exactness a central constraint.",
            "dimension": "evidence standard",
            "evidence_level": "E",
            "supporting_source_ids": ["src-paper"],
            "supporting_locations": ["§1"],
            "counterevidence_source_ids": [],
            "alternative_explanations": ["The estimand itself may require exactness."],
            "relevance_to_target_paper": "Explains the main design constraint.",
            "linked_paper_decisions": ["decision-1"],
            "temporal_scope": "target paper",
            "confidence": "high",
            "rationale": "The paper states this directly.",
            "claim_filter": {
                "gates": {
                    "recurrence": {
                        "outcome": "not-applicable",
                        "rationale": "Target-paper evidence only.",
                    },
                    "target_relevance": {
                        "outcome": "pass",
                        "rationale": "Explains the central constraint.",
                    },
                    "predictive_value": {
                        "outcome": "pass",
                        "rationale": "Predicts the method choice.",
                    },
                    "specificity": {
                        "outcome": "pass",
                        "rationale": "It is paper-specific.",
                    },
                },
                "classification": "paper-specific-explicit",
                "disposition": "include",
            },
        }
        self.write_jsonl("author-research/sources.jsonl", [source])
        self.write_jsonl("author-research/claims.jsonl", [claim])
        self.write_json(
            "author-research/research-status.json",
            {
                "schema_version": 1,
                "owner": self.owner,
                "status": "ready",
                "tier": "quick",
                "author_ids": ["author-1"],
                "breadth_first_complete": True,
                "coverage_summary": {
                    "searched_author_ids": ["author-1"],
                    "included_author_ids": ["author-1"],
                    "gaps": [],
                },
                "research_quality_checkpoint": "not-required",
                "stopping_reason": "The target question is supported at Quick depth.",
            },
        )
        self.write_json(
            "author-research/individuals/author-1.json",
            {
                "schema_version": 1,
                "owner": self.owner,
                "author_id": "author-1",
                "author_name": "Author One",
                "status": "ready",
                "identity_evidence_source_ids": ["src-paper"],
                "authorship_metadata": {
                    "position": 1,
                    "author_count": 1,
                    "equal_contribution_group": [],
                    "is_corresponding_author": True,
                    "ordering_convention": "contribution-ordered",
                    "ordering_convention_confidence": "high",
                },
                "coverage": {
                    "tier": "quick",
                    "searched_source_ids": ["src-paper"],
                    "included_source_ids": ["src-paper"],
                    "gaps": [],
                    "stopping_reason": "The target question is supported at Quick depth.",
                },
                "mindset_claim_ids": ["claim-1"],
                "target_paper_connections": ["decision-1"],
                "explicit_contribution_source_ids": ["src-paper"],
            },
        )
        individual_md = self.namespace / "author-research/individuals/author-1.md"
        individual_md.write_text(
            "---\nowner:\n"
            f"  alias: {self.owner['alias']}\n"
            f"  paper_id: {self.owner['paper_id']}\n"
            "---\n\n# Author One\n",
            encoding="utf-8",
        )
        self.write_json(
            "author-research/composite.json",
            {
                "schema_version": 1,
                "owner": self.owner,
                "status": "ready",
                "authors": ["author-1"],
                "claims": [
                    {
                        "composite_claim_id": "composite-claim-1",
                        "statement": "Exactness governs the design.",
                        "supporting_author_claim_ids": ["claim-1"],
                        "contradicting_author_claim_ids": [],
                        "confidence": "high",
                    }
                ],
                "decisions": [
                    {
                        "decision_id": "decision-1",
                        "decision": "Preserve exact behavior.",
                        "decision_type": "mixed",
                        "candidate_explanations": ["estimand validity"],
                        "authors": [
                            {
                                "author_id": "author-1",
                                "direct_contribution_source_ids": ["src-paper"],
                                "authorship_role_priors": ["sole"],
                                "relevant_claim_ids": ["claim-1"],
                                "supporting_weight": 1.0,
                                "contradicting_weight": 0.0,
                                "inferred_influence": "Sole-author responsibility.",
                                "evidence_level": "E",
                            }
                        ],
                        "ordering_convention": "contribution-ordered",
                        "ordering_effect": "No ordering effect for one author.",
                        "unresolved_uncertainty": "No project-history evidence.",
                    }
                ],
            },
        )

    def start(self, *, topic: str = "Is the claim correct?", members: list[str] | None = None) -> dict:
        payload = {"topic": topic}
        if members is not None:
            payload["members"] = members
        return self.run_cli(PANELS, "start", "demo", payload=payload)

    def append_initial(self, role: str, body: str | None = None) -> dict:
        context = self.run_cli(PANELS, "initial-context", role, "demo")
        return self.run_cli(
            PANELS,
            "append-initial",
            role,
            "demo",
            payload={
                "context_token": context["context_token"],
                "body": body or f"{role} initial answer",
                "evidence_footer": "Evidence: [E] paper §1 · confidence: high.",
            },
        )

    def complete_default_panel(self) -> None:
        self.make_author_ready()
        self.start()
        # All three tokens may be obtained before any response is frozen.
        contexts = {
            role: self.run_cli(PANELS, "initial-context", role, "demo")
            for role in ("author", "reviewer", "researcher")
        }
        for role in ("author", "reviewer", "researcher"):
            self.run_cli(
                PANELS,
                "append-initial",
                role,
                "demo",
                payload={
                    "context_token": contexts[role]["context_token"],
                    "body": f"{role} initial answer",
                    "evidence_footer": "Evidence: [E] paper §1 · confidence: high.",
                },
            )

    def test_start_is_owned_and_archives_only_the_previous_latest_panel(self) -> None:
        first = self.start(topic="First", members=["reviewer", "researcher"])
        self.assertEqual(first["owner"], self.owner)
        self.assertFalse(first["archived_previous"])
        self.append_initial("reviewer")
        self.append_initial("researcher")

        second = self.start(topic="Second", members=["reviewer", "researcher"])
        self.assertTrue(second["archived_previous"])
        shown = self.run_cli(PANELS, "show", "demo")
        history = self.run_cli(PANELS, "show-history", "demo")
        self.assertEqual(shown["latest_panel"]["topic"], "Second")
        self.assertEqual([panel["topic"] for panel in history["history"]], ["First"])
        self.assertEqual(history["history"][0]["status"], "archived")

    def test_role_pair_parser_accepts_only_one_distinct_formatted_pair(self) -> None:
        valid = self.run_cli(PANELS, "parse-pair", " Reviewer : AUTHOR ")
        self.assertEqual((valid["responder"], valid["target"]), ("reviewer", "author"))
        for invalid in (
            "reviewer-author",
            "reviewer:author,researcher:author",
            "reviewer:reviewer",
            "editor:author",
            ":author",
        ):
            error = self.run_cli(PANELS, "parse-pair", invalid, expected=2)
            self.assertIn("role", error["error"].lower())

    def test_initial_contexts_are_isolated_and_incomplete_panel_cannot_continue(self) -> None:
        self.start(members=["reviewer", "researcher"])
        reviewer = self.run_cli(PANELS, "initial-context", "reviewer", "demo")
        self.assertEqual(reviewer["peer_turns"], [])
        self.append_initial("reviewer")
        researcher = self.run_cli(PANELS, "initial-context", "researcher", "demo")
        self.assertEqual(researcher["peer_turns"], [])
        error = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "researcher", "guidance": "focus"},
            expected=2,
        )
        self.assertIn("incomplete", error["error"])

    def test_initial_token_cannot_cross_panel_generations(self) -> None:
        self.start(topic="Same", members=["reviewer", "researcher"])
        old = self.run_cli(PANELS, "initial-context", "reviewer", "demo")
        self.start(topic="Same", members=["reviewer", "researcher"])
        error = self.run_cli(
            PANELS,
            "append-initial",
            "reviewer",
            "demo",
            payload={
                "context_token": old["context_token"],
                "body": "stale initial",
                "evidence_footer": "Evidence: [E] paper §1.",
            },
            expected=2,
        )
        self.assertIn("stale", error["error"])

    def test_parallel_initial_appends_do_not_lose_a_turn(self) -> None:
        self.start(members=["reviewer", "researcher"])
        contexts = {
            role: self.run_cli(PANELS, "initial-context", role, "demo")
            for role in ("reviewer", "researcher")
        }
        processes = []
        for role in ("reviewer", "researcher"):
            payload = {
                "context_token": contexts[role]["context_token"],
                "body": f"parallel {role}",
                "evidence_footer": "Evidence: [E] paper §1.",
            }
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(PANELS),
                    "--root",
                    str(self.state),
                    "append-initial",
                    role,
                    "demo",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
            process.stdin = None
            processes.append(process)
        for process in processes:
            _, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
        latest = self.run_cli(PANELS, "show", "demo")["latest_panel"]
        self.assertEqual(latest["status"], "ready")
        self.assertEqual(
            {turn["role"] for turn in latest["turns"]}, {"reviewer", "researcher"}
        )

    def test_targeted_continuation_uses_latest_target_and_role_safe_context(self) -> None:
        self.complete_default_panel()
        context = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "author", "guidance": "Focus on the theorem."},
        )
        self.assertEqual(context["peer_turn"]["body"], "author initial answer")
        self.assertTrue(context["peer_turn"]["peer_claim_only"])
        self.assertNotIn("evidence_footer", context["peer_turn"])
        self.assertEqual(context["guidance"], "Focus on the theorem.")
        self.assertFalse(any("author-research" in path for path in context["allowed_paths"]))
        continued = self.run_cli(
            PANELS,
            "append-continuation",
            "reviewer",
            "demo",
            payload={
                "target": "author",
                "guidance": "Focus on the theorem.",
                "context_token": context["context_token"],
                "body": "I am responding to the author's theorem argument.",
                "evidence_footer": "Evidence: [E] paper Theorem 1 · confidence: high.",
            },
        )
        self.assertEqual(continued["turn"]["responds_to_turn_ids"], ["turn-0001"])

        author_context = self.run_cli(
            PANELS,
            "continue-context",
            "author",
            "demo",
            payload={"target": "reviewer", "guidance": ""},
        )
        self.assertEqual(
            author_context["peer_turn"]["body"],
            "I am responding to the author's theorem argument.",
        )
        self.assertTrue(any("author-research" in path for path in author_context["allowed_paths"]))
        self.run_cli(
            PANELS,
            "append-continuation",
            "author",
            "demo",
            payload={
                "target": "reviewer",
                "guidance": "",
                "context_token": author_context["context_token"],
                "body": "author's newer reply",
                "evidence_footer": "Evidence: [E] paper §1 · confidence: high.",
            },
        )
        newest = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "author", "guidance": ""},
        )
        self.assertEqual(newest["peer_turn"]["body"], "author's newer reply")

    def test_invalid_or_missing_roles_fail_without_changing_state(self) -> None:
        self.start(members=["reviewer", "researcher"])
        self.append_initial("reviewer")
        self.append_initial("researcher")
        before = self.run_cli(PANELS, "show", "demo")["latest_panel"]
        same = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "reviewer"},
            expected=2,
        )
        self.assertIn("distinct", same["error"])
        absent = self.run_cli(
            PANELS,
            "continue-context",
            "author",
            "demo",
            payload={"target": "reviewer"},
            expected=2,
        )
        self.assertIn("members", absent["error"])
        after = self.run_cli(PANELS, "show", "demo")["latest_panel"]
        self.assertEqual(before, after)

    def test_missing_latest_panel_and_missing_target_answer_fail(self) -> None:
        missing = self.run_cli(PANELS, "show", "demo", expected=2)
        self.assertIn("No latest panel", missing["error"])
        self.start(members=["reviewer", "researcher"])
        # Simulate a valid archived partial panel by starting another panel.
        self.append_initial("reviewer")
        self.start(topic="Replacement", members=["reviewer", "researcher"])
        self.append_initial("reviewer")
        self.append_initial("researcher")
        # Both latest roles now have answers; an excluded role cannot be targeted.
        missing_target = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "author"},
            expected=2,
        )
        self.assertIn("members", missing_target["error"])

    def test_stale_continuation_token_is_rejected(self) -> None:
        self.start(members=["reviewer", "researcher"])
        self.append_initial("reviewer")
        self.append_initial("researcher")
        stale = self.run_cli(
            PANELS,
            "continue-context",
            "reviewer",
            "demo",
            payload={"target": "researcher", "guidance": "old"},
        )
        fresh = self.run_cli(
            PANELS,
            "continue-context",
            "researcher",
            "demo",
            payload={"target": "reviewer", "guidance": "new"},
        )
        self.run_cli(
            PANELS,
            "append-continuation",
            "researcher",
            "demo",
            payload={
                "target": "reviewer",
                "guidance": "new",
                "context_token": fresh["context_token"],
                "body": "new response",
                "evidence_footer": "Evidence: [E] paper §1.",
            },
        )
        error = self.run_cli(
            PANELS,
            "append-continuation",
            "reviewer",
            "demo",
            payload={
                "target": "researcher",
                "guidance": "old",
                "context_token": stale["context_token"],
                "body": "stale response",
                "evidence_footer": "Evidence: [E] paper §1.",
            },
            expected=2,
        )
        self.assertIn("stale", error["error"])

    def test_hash_tampering_and_cross_alias_state_fail_closed(self) -> None:
        self.start(members=["reviewer", "researcher"])
        self.append_initial("reviewer")
        path = self.namespace / "conversation-state/panel-sessions.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["latest_panel"]["turns"][0]["body"] = "tampered"
        path.write_text(json.dumps(value), encoding="utf-8")
        invalid = self.run_cli(PANELS, "validate", "demo", expected=2)
        self.assertTrue(any("content_hash" in item for item in invalid["errors"]))

        other_paper = self.workspace / "other.txt"
        other_paper.write_text("Other paper.\n", encoding="utf-8")
        other = self.run_cli(REGISTRY, "add", "other", str(other_paper))
        other_path = Path(other["namespace"]) / "conversation-state/panel-sessions.json"
        other_path.write_text(json.dumps(value), encoding="utf-8")
        mismatch = self.run_cli(PANELS, "validate", "other", expected=2)
        self.assertTrue(any("owner" in item for item in mismatch["errors"]))

    def test_registry_remove_and_restore_preserves_panel_state(self) -> None:
        self.start(members=["reviewer", "researcher"])
        topic = self.run_cli(PANELS, "show", "demo")["latest_panel"]["topic"]
        removed = self.run_cli(
            REGISTRY, "remove", "demo", "--paper-id", self.owner["paper_id"]
        )
        self.run_cli(REGISTRY, "restore", removed["removal_id"])
        restored = self.run_cli(PANELS, "show", "demo")
        self.assertEqual(restored["latest_panel"]["topic"], topic)

    def test_author_initial_context_still_requires_ready_author_artifacts(self) -> None:
        self.start()
        error = self.run_cli(PANELS, "initial-context", "author", "demo", expected=2)
        self.assertIn("Author context is not ready", error["error"])


if __name__ == "__main__":
    unittest.main()
