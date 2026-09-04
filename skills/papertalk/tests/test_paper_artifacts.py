from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REGISTRY = SKILL / "scripts" / "paper_registry.py"
ARTIFACTS = SKILL / "scripts" / "paper_artifacts.py"


class ArtifactCliTests(unittest.TestCase):
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
        self, script: Path, *arguments: str, expected: int = 0
    ) -> dict:
        process = subprocess.run(
            [sys.executable, str(script), "--root", str(self.state), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(process.returncode, expected, process.stderr or process.stdout)
        output = process.stdout if expected == 0 else process.stderr
        return json.loads(output)

    def write_json(self, relative: str, value: dict) -> None:
        (self.namespace / relative).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def write_jsonl(self, relative: str, records: list[dict]) -> None:
        text = "".join(json.dumps(record) + "\n" for record in records)
        (self.namespace / relative).write_text(text, encoding="utf-8")

    def write_owned_markdown(self, relative: str, title: str) -> None:
        (self.namespace / relative).write_text(
            "---\n"
            "owner:\n"
            f"  alias: {self.owner['alias']}\n"
            f"  paper_id: {self.owner['paper_id']}\n"
            "---\n\n"
            f"# {title}\n",
            encoding="utf-8",
        )

    def source(self, *, owner: dict | None = None) -> dict:
        return {
            "source_id": "src-paper",
            "owner": owner or self.owner,
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

    def claim(
        self,
        *,
        claim_id: str = "claim-1",
        evidence_level: str = "E",
        locations: list[str] | None = None,
        rationale: str = "The paper states this directly.",
        classification: str = "paper-specific-explicit",
        disposition: str = "include",
    ) -> dict:
        return {
            "claim_id": claim_id,
            "owner": self.owner,
            "author_id": "author-1",
            "claim": "The author makes exactness a central constraint.",
            "dimension": "evidence standard",
            "evidence_level": evidence_level,
            "supporting_source_ids": ["src-paper"],
            "supporting_locations": ["§1"] if locations is None else locations,
            "counterevidence_source_ids": [],
            "alternative_explanations": ["The estimand itself may require exactness."],
            "relevance_to_target_paper": "Explains the main design constraint.",
            "linked_paper_decisions": ["decision-1"],
            "temporal_scope": "target paper",
            "confidence": "high",
            "rationale": rationale,
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
                "classification": classification,
                "disposition": disposition,
            },
        }

    def populate_valid_bundle(self) -> None:
        self.write_jsonl("author-research/sources.jsonl", [self.source()])
        self.write_jsonl("author-research/claims.jsonl", [self.claim()])
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
        self.write_owned_markdown(
            "author-research/individuals/author-1.md", "Author One"
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
        self.write_json(
            "role-state/reviewer/scope.json",
            {
                "schema_version": 1,
                "owner": self.owner,
                "role": "reviewer",
                "status": "ready",
                "source_status": "public",
                "material_scope": ["full paper"],
                "requested_lenses": ["evaluation"],
                "external_processing_used": False,
                "external_services_authorized": False,
                "venue_policy_checked": False,
                "retention_policy_confirmed": False,
            },
        )
        self.write_jsonl(
            "role-state/reviewer/findings.jsonl",
            [
                {
                    "finding_id": "finding-1",
                    "owner": self.owner,
                    "role": "reviewer",
                    "lens": "evaluation",
                    "finding_type": "strength",
                    "claim_id": "paper-claim-1",
                    "location": "§3",
                    "observation": "The experiment isolates the claimed effect.",
                    "criterion": "The experiment should test the central claim.",
                    "supporting_evidence": ["The ablation removes only the proposed component."],
                    "counterevidence": [],
                    "alternative_explanations": [],
                    "evidence_state": "supported",
                    "consequence": "This raises confidence in the central claim.",
                    "severity": "observation",
                    "requested_action": "",
                    "confidence": "high",
                    "not_assessed_reason": "",
                }
            ],
        )

    def test_add_scaffolds_all_p0_artifacts_without_author_readiness(self) -> None:
        expected = [
            "author-research/sources.jsonl",
            "author-research/claims.jsonl",
            "author-research/research-status.json",
            "author-research/composite.json",
            "author-research/validation.json",
            "author-research/composite.md",
            "role-state/reviewer/scope.json",
            "role-state/reviewer/findings.jsonl",
        ]
        for relative in expected:
            self.assertTrue((self.namespace / relative).exists(), relative)
        result = self.run_cli(ARTIFACTS, "validate", "demo")
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["author_context_ready"])

    def test_valid_bundle_authorizes_role_specific_contexts(self) -> None:
        self.populate_valid_bundle()
        result = self.run_cli(ARTIFACTS, "validate", "@demo")
        self.assertTrue(result["author_context_ready"])
        self.assertEqual(result["counts"]["included_claims"], 1)
        self.assertEqual(result["counts"]["composite_claims"], 1)
        self.assertEqual(result["counts"]["composite_decisions"], 1)

        author = self.run_cli(ARTIFACTS, "context", "author", "demo")
        reviewer = self.run_cli(ARTIFACTS, "context", "reviewer", "demo")
        researcher = self.run_cli(ARTIFACTS, "context", "researcher", "demo")
        self.assertTrue(any("author-research" in path for path in author["allowed_paths"]))
        self.assertFalse(any("author-research" in path for path in reviewer["allowed_paths"]))
        self.assertFalse(any("author-research" in path for path in researcher["allowed_paths"]))
        self.assertEqual(reviewer["denied_paths"], [str(self.namespace / "author-research")])

    def test_owner_mismatch_fails_closed(self) -> None:
        wrong = {"alias": "other", "paper_id": self.owner["paper_id"]}
        self.write_jsonl("author-research/sources.jsonl", [self.source(owner=wrong)])
        error = self.run_cli(ARTIFACTS, "validate", "demo", expected=2)
        self.assertEqual(error["status"], "invalid")
        self.assertTrue(any("owner does not match" in item for item in error["errors"]))

    def test_explicit_and_inferred_claim_evidence_rules_fail_closed(self) -> None:
        self.write_jsonl("author-research/sources.jsonl", [self.source()])
        explicit = self.claim(locations=[])
        inferred = self.claim(
            claim_id="claim-2",
            evidence_level="I",
            rationale="",
            classification="decision-heuristic",
        )
        self.write_jsonl("author-research/claims.jsonl", [explicit, inferred])
        error = self.run_cli(ARTIFACTS, "validate", "demo", expected=2)
        joined = "\n".join(error["errors"])
        self.assertIn("E claims require a direct source and location", joined)
        self.assertIn("I/H claims require supporting evidence and a rationale", joined)

    def test_omitted_claim_cannot_enter_an_individual_or_composite(self) -> None:
        self.populate_valid_bundle()
        omitted = self.claim(classification="omit", disposition="omit")
        self.write_jsonl("author-research/claims.jsonl", [omitted])
        error = self.run_cli(ARTIFACTS, "validate", "demo", expected=2)
        self.assertTrue(any("omitted claim" in item for item in error["errors"]))

    def test_author_evidence_in_shared_model_blocks_every_context(self) -> None:
        model = self.namespace / "paper-model.md"
        model.write_text(model.read_text(encoding="utf-8") + "\nLeak [AW]\n", encoding="utf-8")
        error = self.run_cli(ARTIFACTS, "context", "researcher", "demo", expected=2)
        self.assertIn("forbidden in the shared model", error["error"])

    def test_unpublished_external_processing_requires_all_permissions(self) -> None:
        scope_path = "role-state/reviewer/scope.json"
        scope = json.loads((self.namespace / scope_path).read_text(encoding="utf-8"))
        scope.update(
            {
                "status": "ready",
                "source_status": "unpublished",
                "external_processing_used": True,
                "external_services_authorized": True,
                "venue_policy_checked": False,
                "retention_policy_confirmed": False,
            }
        )
        self.write_json(scope_path, scope)
        error = self.run_cli(ARTIFACTS, "validate", "demo", expected=2)
        joined = "\n".join(error["errors"])
        self.assertIn("venue_policy_checked=true", joined)
        self.assertIn("retention_policy_confirmed=true", joined)

    def test_reviewer_merits_and_concerns_require_evidence(self) -> None:
        self.populate_valid_bundle()
        finding_path = self.namespace / "role-state/reviewer/findings.jsonl"
        finding = json.loads(finding_path.read_text(encoding="utf-8"))
        finding["supporting_evidence"] = []
        self.write_jsonl("role-state/reviewer/findings.jsonl", [finding])
        error = self.run_cli(ARTIFACTS, "validate", "demo", expected=2)
        self.assertTrue(
            any("evaluative findings require supporting_evidence" in item for item in error["errors"])
        )


if __name__ == "__main__":
    unittest.main()
