#!/usr/bin/env python3
"""Initialize and validate PaperTalk P0 evidence artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ARTIFACT_SCHEMA_VERSION = 1
EVIDENCE_LEVELS = {"E", "I", "H"}
SOURCE_TYPES = {"P", "AW", "AS", "D"}
DEPTH_TIERS = {"quick", "standard", "deep"}
RESEARCH_STATUSES = {"not-started", "in-progress", "ready", "ready-with-gaps"}
FILTER_GATES = {"recurrence", "target_relevance", "predictive_value", "specificity"}
GATE_OUTCOMES = {"pass", "partial", "not-applicable", "fail"}
FILTER_CLASSES = {"durable", "decision-heuristic", "paper-specific-explicit", "omit"}
ORDERING_CONVENTIONS = {"contribution-ordered", "alphabetical", "mixed", "unknown"}
ROLE_PRIORS = {"sole", "first", "co-first", "corresponding", "field-specific-senior", "neutral"}
DECISION_TYPES = {"direction", "execution", "mixed"}
REVIEW_LENSES = {
    "claims",
    "methods",
    "theory",
    "novelty",
    "evaluation",
    "reproducibility",
    "ethics",
    "re-review",
    "attack",
}
FINDING_TYPES = {"strength", "concern", "limitation", "question"}
SEVERITIES = {"critical", "major", "minor", "clarification", "observation"}
EVIDENCE_STATES = {"supported", "contradicted", "unsupported", "not-reported", "not-available", "not-assessed"}
SOURCE_STATUSES = {"public", "preprint", "partial", "unpublished", "unknown"}


class ArtifactError(Exception):
    """A user-facing artifact contract error."""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_json_if_missing(path: Path, value: dict[str, Any]) -> None:
    if not path.exists():
        atomic_write_json(path, value)


def touch_if_missing(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.touch(exist_ok=False)
    except FileExistsError:
        pass


def write_text_if_missing(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(value)
    except FileExistsError:
        pass


def initialize_artifact_scaffold(namespace: Path, owner: dict[str, str]) -> list[str]:
    """Create missing P0 files without overwriting existing paper state."""
    created: list[str] = []
    author_root = namespace / "author-research"
    reviewer_root = namespace / "role-state" / "reviewer"
    (author_root / "individuals").mkdir(parents=True, exist_ok=True)
    reviewer_root.mkdir(parents=True, exist_ok=True)

    files: list[tuple[Path, dict[str, Any] | None]] = [
        (author_root / "sources.jsonl", None),
        (author_root / "claims.jsonl", None),
        (
            author_root / "research-status.json",
            {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                "owner": owner,
                "status": "not-started",
                "tier": None,
                "author_ids": [],
                "breadth_first_complete": False,
                "coverage_summary": {
                    "searched_author_ids": [],
                    "included_author_ids": [],
                    "gaps": [],
                },
                "research_quality_checkpoint": "pending",
                "stopping_reason": None,
            },
        ),
        (
            author_root / "composite.json",
            {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                "owner": owner,
                "status": "not-built",
                "authors": [],
                "claims": [],
                "decisions": [],
            },
        ),
        (
            author_root / "validation.json",
            {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                "owner": owner,
                "status": "not-run",
                "validated_at": None,
                "errors": [],
                "warnings": [],
            },
        ),
        (
            reviewer_root / "scope.json",
            {
                "schema_version": ARTIFACT_SCHEMA_VERSION,
                "owner": owner,
                "role": "reviewer",
                "status": "not-started",
                "source_status": "unknown",
                "material_scope": [],
                "requested_lenses": [],
                "external_processing_used": False,
                "external_services_authorized": False,
                "venue_policy_checked": False,
                "retention_policy_confirmed": False,
            },
        ),
        (reviewer_root / "findings.jsonl", None),
    ]

    for path, value in files:
        existed = path.exists()
        if value is None:
            touch_if_missing(path)
        else:
            write_json_if_missing(path, value)
        if not existed and path.exists():
            created.append(str(path.relative_to(namespace)))
    composite_markdown = author_root / "composite.md"
    existed = composite_markdown.exists()
    write_text_if_missing(
        composite_markdown,
        "---\n"
        "owner:\n"
        f"  alias: {owner['alias']}\n"
        f"  paper_id: {owner['paper_id']}\n"
        "---\n\n"
        "# Composite Author\n\n"
        "Status: not built.\n",
    )
    if not existed and composite_markdown.exists():
        created.append(str(composite_markdown.relative_to(namespace)))
    return created


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing required artifact")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: expected a JSON object")
        return None
    return value


def load_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        errors.append(f"{path}: missing required artifact")
        return records
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}:{line_number}: expected a JSON object")
            continue
        value["_record_location"] = f"{path}:{line_number}"
        records.append(value)
    return records


def require_keys(record: dict[str, Any], keys: Iterable[str], location: str, errors: list[str]) -> None:
    for key in keys:
        if key not in record:
            errors.append(f"{location}: missing required field '{key}'")


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def is_allowed(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def owner_matches(value: Any, owner: dict[str, str]) -> bool:
    return isinstance(value, dict) and value == owner


def validate_owner(record: dict[str, Any], owner: dict[str, str], location: str, errors: list[str]) -> None:
    if not owner_matches(record.get("owner"), owner):
        errors.append(f"{location}: owner does not match resolved paper {owner}")


def validate_shared_model(namespace: Path, owner: dict[str, str]) -> list[str]:
    errors: list[str] = []
    path = namespace / "paper-model.md"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"{path}: missing shared paper model"]
    alias_present = bool(re.search(rf"(?:alias:\s*|@){re.escape(owner['alias'])}\b", text, re.IGNORECASE))
    if not alias_present or owner["paper_id"] not in text:
        errors.append(f"{path}: shared paper model owner is missing or mismatched")
    forbidden = sorted(marker for marker in ("[AW]", "[AS]") if marker.lower() in text.lower())
    if forbidden:
        errors.append(
            f"{path}: author-derived evidence marker(s) {', '.join(forbidden)} are forbidden in the shared model"
        )
    return errors


def validate_owned_markdown(path: Path, owner: dict[str, str], errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"{path}: missing required readable artifact")
        return
    alias_present = bool(re.search(rf"alias:\s*{re.escape(owner['alias'])}\b", text, re.IGNORECASE))
    if not alias_present or owner["paper_id"] not in text:
        errors.append(f"{path}: readable artifact owner is missing or mismatched")


def validate_source_records(
    records: list[dict[str, Any]], owner: dict[str, str], errors: list[str]
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    required = (
        "source_id",
        "owner",
        "author_id",
        "url_or_path",
        "title",
        "source_type",
        "publication_date",
        "retrieved_at",
        "primary_or_secondary",
        "identity_match_evidence",
        "target_relevance",
        "content_location",
    )
    for record in records:
        location = record.pop("_record_location")
        require_keys(record, required, location, errors)
        validate_owner(record, owner, location, errors)
        source_id = record.get("source_id")
        if not nonempty_text(source_id):
            errors.append(f"{location}: source_id must be non-empty text")
            continue
        if source_id in indexed:
            errors.append(f"{location}: duplicate source_id '{source_id}'")
        indexed[source_id] = record
        if not is_allowed(record.get("source_type"), SOURCE_TYPES):
            errors.append(f"{location}: invalid source_type '{record.get('source_type')}'")
        if not is_allowed(record.get("primary_or_secondary"), {"primary", "secondary"}):
            errors.append(f"{location}: primary_or_secondary must be 'primary' or 'secondary'")
        for field in ("author_id", "url_or_path", "title", "retrieved_at", "target_relevance"):
            if not nonempty_text(record.get(field)):
                errors.append(f"{location}: {field} must be non-empty text")
        if not nonempty_list(record.get("identity_match_evidence")):
            errors.append(f"{location}: identity_match_evidence must be a non-empty list")
        content_location = record.get("content_location")
        if not nonempty_text(content_location) and not nonempty_list(content_location):
            errors.append(f"{location}: content_location must identify where the evidence appears")
    return indexed


def validate_filter(
    record: dict[str, Any], source_index: dict[str, dict[str, Any]], location: str, errors: list[str]
) -> bool:
    filter_record = record.get("claim_filter")
    if not isinstance(filter_record, dict):
        errors.append(f"{location}: claim_filter must be an object")
        return False
    gates = filter_record.get("gates")
    if not isinstance(gates, dict) or set(gates) != FILTER_GATES:
        errors.append(f"{location}: claim_filter.gates must contain exactly {sorted(FILTER_GATES)}")
    else:
        for gate_name, gate in gates.items():
            if not isinstance(gate, dict):
                errors.append(f"{location}: gate '{gate_name}' must be an object")
                continue
            if not is_allowed(gate.get("outcome"), GATE_OUTCOMES):
                errors.append(f"{location}: gate '{gate_name}' has an invalid outcome")
            if not nonempty_text(gate.get("rationale")):
                errors.append(f"{location}: gate '{gate_name}' requires a rationale")
    classification = filter_record.get("classification")
    disposition = filter_record.get("disposition")
    if not is_allowed(classification, FILTER_CLASSES):
        errors.append(f"{location}: invalid claim-filter classification '{classification}'")
    if not is_allowed(disposition, {"include", "omit"}):
        errors.append(f"{location}: claim_filter.disposition must be 'include' or 'omit'")
    if (classification == "omit") != (disposition == "omit"):
        errors.append(f"{location}: omit classification and disposition must agree")
    if classification == "durable" and isinstance(gates, dict):
        if any(isinstance(gate, dict) and gate.get("outcome") == "fail" for gate in gates.values()):
            errors.append(f"{location}: a durable claim cannot fail a filter gate")
    if classification == "paper-specific-explicit":
        if record.get("evidence_level") != "E":
            errors.append(f"{location}: paper-specific-explicit claims must use evidence level E")
        source_ids = record.get("supporting_source_ids", [])
        if not any(source_index.get(source_id, {}).get("source_type") == "P" for source_id in source_ids):
            errors.append(f"{location}: paper-specific-explicit claims require a target-paper source")
    return disposition == "include" and classification != "omit"


def validate_claim_records(
    records: list[dict[str, Any]],
    owner: dict[str, str],
    source_index: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    indexed: dict[str, dict[str, Any]] = {}
    included: set[str] = set()
    required = (
        "claim_id",
        "owner",
        "author_id",
        "claim",
        "dimension",
        "evidence_level",
        "supporting_source_ids",
        "supporting_locations",
        "counterevidence_source_ids",
        "alternative_explanations",
        "relevance_to_target_paper",
        "linked_paper_decisions",
        "temporal_scope",
        "confidence",
        "rationale",
        "claim_filter",
    )
    for record in records:
        location = record.pop("_record_location")
        require_keys(record, required, location, errors)
        validate_owner(record, owner, location, errors)
        claim_id = record.get("claim_id")
        if not nonempty_text(claim_id):
            errors.append(f"{location}: claim_id must be non-empty text")
            continue
        if claim_id in indexed:
            errors.append(f"{location}: duplicate claim_id '{claim_id}'")
        indexed[claim_id] = record
        if not is_allowed(record.get("evidence_level"), EVIDENCE_LEVELS):
            errors.append(f"{location}: invalid evidence_level '{record.get('evidence_level')}'")
        for field in (
            "author_id",
            "claim",
            "dimension",
            "relevance_to_target_paper",
            "temporal_scope",
            "confidence",
        ):
            if not nonempty_text(record.get(field)):
                errors.append(f"{location}: {field} must be non-empty text")
        for field in (
            "supporting_source_ids",
            "supporting_locations",
            "counterevidence_source_ids",
            "alternative_explanations",
            "linked_paper_decisions",
        ):
            if not isinstance(record.get(field), list):
                errors.append(f"{location}: {field} must be a list")
        supporting_ids = list_or_empty(record.get("supporting_source_ids"))
        counter_ids = list_or_empty(record.get("counterevidence_source_ids"))
        for source_id in supporting_ids + counter_ids:
            if not nonempty_text(source_id):
                errors.append(f"{location}: source references must be non-empty text")
                continue
            source = source_index.get(source_id)
            if source is None:
                errors.append(f"{location}: references unknown source_id '{source_id}'")
            elif source.get("author_id") not in (record.get("author_id"), "paper"):
                errors.append(f"{location}: source '{source_id}' belongs to a different author")
        if record.get("evidence_level") == "E":
            if not nonempty_list(supporting_ids) or not nonempty_list(record.get("supporting_locations")):
                errors.append(f"{location}: E claims require a direct source and location")
        elif record.get("evidence_level") in {"I", "H"}:
            if not nonempty_list(supporting_ids) or not nonempty_text(record.get("rationale")):
                errors.append(f"{location}: I/H claims require supporting evidence and a rationale")
        if validate_filter(record, source_index, location, errors):
            included.add(claim_id)
    return indexed, included


def validate_research_status(
    path: Path, owner: dict[str, str], errors: list[str], warnings: list[str]
) -> dict[str, Any] | None:
    record = load_json(path, errors)
    if record is None:
        return None
    validate_owner(record, owner, str(path), errors)
    require_keys(
        record,
        (
            "status",
            "tier",
            "author_ids",
            "breadth_first_complete",
            "coverage_summary",
            "research_quality_checkpoint",
            "stopping_reason",
        ),
        str(path),
        errors,
    )
    status = record.get("status")
    tier = record.get("tier")
    if not is_allowed(status, RESEARCH_STATUSES):
        errors.append(f"{path}: invalid research status '{status}'")
    if tier is not None and not is_allowed(tier, DEPTH_TIERS):
        errors.append(f"{path}: invalid research tier '{tier}'")
    author_ids = record.get("author_ids")
    if not isinstance(author_ids, list):
        errors.append(f"{path}: author_ids must be a list")
    elif any(not nonempty_text(author_id) for author_id in author_ids):
        errors.append(f"{path}: every author_id must be non-empty text")
    elif len(author_ids) != len(set(author_ids)):
        errors.append(f"{path}: author_ids must not contain duplicates")
    if not isinstance(record.get("coverage_summary"), dict):
        errors.append(f"{path}: coverage_summary must be an object")
    if status in {"ready", "ready-with-gaps"}:
        if not is_allowed(tier, DEPTH_TIERS):
            errors.append(f"{path}: completed research requires quick, standard, or deep tier")
        if not nonempty_list(record.get("author_ids")):
            errors.append(f"{path}: completed research requires every named author_id")
        if record.get("breadth_first_complete") is not True:
            errors.append(f"{path}: completed research requires breadth-first author coverage")
        if not nonempty_text(record.get("stopping_reason")):
            errors.append(f"{path}: completed research requires an evidence-based stopping reason")
        checkpoint = record.get("research_quality_checkpoint")
        if tier in {"standard", "deep"} and checkpoint != "accepted":
            errors.append(f"{path}: standard/deep research requires an accepted quality checkpoint")
        if tier == "quick" and not is_allowed(checkpoint, {"accepted", "not-required"}):
            errors.append(f"{path}: quick research requires an accepted or not-required checkpoint")
    if status == "ready-with-gaps":
        gaps = record.get("coverage_summary", {}).get("gaps", []) if isinstance(record.get("coverage_summary"), dict) else []
        if not nonempty_list(gaps):
            errors.append(f"{path}: ready-with-gaps requires explicit coverage gaps")
        else:
            warnings.append(f"{path}: author research is ready with documented gaps")
    return record


def validate_individuals(
    directory: Path,
    owner: dict[str, str],
    source_index: dict[str, dict[str, Any]],
    claim_index: dict[str, dict[str, Any]],
    included_claim_ids: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    if not directory.is_dir():
        errors.append(f"{directory}: missing individual-author directory")
        return indexed
    for path in sorted(directory.glob("*.json")):
        record = load_json(path, errors)
        if record is None:
            continue
        validate_owner(record, owner, str(path), errors)
        require_keys(
            record,
            (
                "author_id",
                "author_name",
                "status",
                "identity_evidence_source_ids",
                "authorship_metadata",
                "coverage",
                "mindset_claim_ids",
                "target_paper_connections",
                "explicit_contribution_source_ids",
            ),
            str(path),
            errors,
        )
        author_id = record.get("author_id")
        if not nonempty_text(author_id):
            errors.append(f"{path}: author_id must be non-empty text")
            continue
        if author_id in indexed:
            errors.append(f"{path}: duplicate author_id '{author_id}'")
        indexed[author_id] = record
        if path.stem != author_id:
            errors.append(f"{path}: filename must match author_id '{author_id}'")
        if not nonempty_text(record.get("author_name")):
            errors.append(f"{path}: author_name must be non-empty text")
        if not is_allowed(record.get("status"), {"draft", "ready"}):
            errors.append(f"{path}: status must be draft or ready")
        for field in ("identity_evidence_source_ids", "mindset_claim_ids", "target_paper_connections", "explicit_contribution_source_ids"):
            if not isinstance(record.get(field), list):
                errors.append(f"{path}: {field} must be a list")
        identity_source_ids = list_or_empty(record.get("identity_evidence_source_ids"))
        contribution_source_ids = list_or_empty(record.get("explicit_contribution_source_ids"))
        for source_id in identity_source_ids + contribution_source_ids:
            if not nonempty_text(source_id):
                errors.append(f"{path}: source references must be non-empty text")
                continue
            source = source_index.get(source_id)
            if source is None:
                errors.append(f"{path}: references unknown source_id '{source_id}'")
            elif source.get("author_id") not in (author_id, "paper"):
                errors.append(f"{path}: source '{source_id}' belongs to a different author")
        for claim_id in list_or_empty(record.get("mindset_claim_ids")):
            if not nonempty_text(claim_id):
                errors.append(f"{path}: claim references must be non-empty text")
                continue
            claim = claim_index.get(claim_id)
            if claim is None:
                errors.append(f"{path}: references unknown claim_id '{claim_id}'")
            elif claim_id not in included_claim_ids:
                errors.append(f"{path}: omitted claim '{claim_id}' cannot enter an author distillate")
            elif claim.get("author_id") != author_id:
                errors.append(f"{path}: claim '{claim_id}' belongs to a different author")
        coverage = record.get("coverage")
        if not isinstance(coverage, dict):
            errors.append(f"{path}: coverage must be an object")
        else:
            if not is_allowed(coverage.get("tier"), DEPTH_TIERS):
                errors.append(f"{path}: coverage.tier must be quick, standard, or deep")
            for field in ("searched_source_ids", "included_source_ids", "gaps"):
                if not isinstance(coverage.get(field), list):
                    errors.append(f"{path}: coverage.{field} must be a list")
            for source_id in list_or_empty(coverage.get("included_source_ids")):
                if not nonempty_text(source_id):
                    errors.append(f"{path}: coverage source references must be non-empty text")
                    continue
                source = source_index.get(source_id)
                if source is None:
                    errors.append(f"{path}: coverage references unknown source_id '{source_id}'")
                elif source.get("author_id") not in (author_id, "paper"):
                    errors.append(f"{path}: coverage source '{source_id}' belongs to a different author")
            if not nonempty_text(coverage.get("stopping_reason")):
                errors.append(f"{path}: coverage requires an evidence-based stopping_reason")
        if record.get("status") == "ready":
            if not nonempty_list(record.get("identity_evidence_source_ids")):
                errors.append(f"{path}: ready author distillates require identity evidence")
            validate_owned_markdown(path.with_suffix(".md"), owner, errors)
    return indexed


def validate_composite(
    path: Path,
    owner: dict[str, str],
    source_index: dict[str, dict[str, Any]],
    claim_index: dict[str, dict[str, Any]],
    included_claim_ids: set[str],
    individuals: dict[str, dict[str, Any]],
    errors: list[str],
) -> dict[str, Any] | None:
    record = load_json(path, errors)
    if record is None:
        return None
    validate_owner(record, owner, str(path), errors)
    require_keys(record, ("status", "authors", "claims", "decisions"), str(path), errors)
    if not is_allowed(record.get("status"), {"not-built", "draft", "ready"}):
        errors.append(f"{path}: invalid composite status '{record.get('status')}'")
    if record.get("status") != "ready":
        return record
    authors = record.get("authors")
    if not nonempty_list(authors):
        errors.append(f"{path}: ready composite requires authors")
        authors = []
    elif any(not nonempty_text(author_id) for author_id in authors):
        errors.append(f"{path}: every composite author_id must be non-empty text")
    elif len(authors) != len(set(authors)):
        errors.append(f"{path}: ready composite authors must not contain duplicates")
    author_set = {author_id for author_id in list_or_empty(authors) if nonempty_text(author_id)}
    if author_set != set(individuals):
        errors.append(f"{path}: ready composite authors must match individual distillates")
    composite_claim_ids: set[str] = set()
    composite_claims = record.get("claims")
    if not nonempty_list(composite_claims):
        errors.append(f"{path}: ready composite requires at least one traceable claim")
        composite_claims = []
    for claim in composite_claims:
        location = f"{path}:composite claim"
        require_keys(
            claim,
            ("composite_claim_id", "statement", "supporting_author_claim_ids", "contradicting_author_claim_ids", "confidence"),
            location,
            errors,
        )
        composite_claim_id = claim.get("composite_claim_id")
        if not nonempty_text(composite_claim_id):
            errors.append(f"{location}: composite_claim_id must be non-empty text")
        elif composite_claim_id in composite_claim_ids:
            errors.append(f"{location}: duplicate composite_claim_id '{composite_claim_id}'")
        else:
            composite_claim_ids.add(composite_claim_id)
        supporting = claim.get("supporting_author_claim_ids")
        if not nonempty_list(supporting):
            errors.append(f"{location}: composite claim requires supporting individual claims")
        contradicting = claim.get("contradicting_author_claim_ids")
        if not isinstance(contradicting, list):
            errors.append(f"{location}: contradicting_author_claim_ids must be a list")
        for claim_id in list_or_empty(supporting) + list_or_empty(contradicting):
            if not nonempty_text(claim_id):
                errors.append(f"{location}: author claim references must be non-empty text")
                continue
            if claim_id not in claim_index:
                errors.append(f"{location}: references unknown author claim '{claim_id}'")
            elif claim_id not in included_claim_ids:
                errors.append(f"{location}: omitted claim '{claim_id}' cannot support the composite")
    decisions = record.get("decisions")
    if not nonempty_list(decisions):
        errors.append(f"{path}: ready composite requires at least one decision record")
        decisions = []
    decision_ids: set[str] = set()
    for decision in decisions:
        location = f"{path}:decision"
        require_keys(
            decision,
            (
                "decision_id",
                "decision",
                "decision_type",
                "candidate_explanations",
                "authors",
                "ordering_convention",
                "ordering_effect",
                "unresolved_uncertainty",
            ),
            location,
            errors,
        )
        decision_id = decision.get("decision_id")
        if not nonempty_text(decision_id):
            errors.append(f"{location}: decision_id must be non-empty text")
        elif decision_id in decision_ids:
            errors.append(f"{location}: duplicate decision_id '{decision_id}'")
        else:
            decision_ids.add(decision_id)
        if not is_allowed(decision.get("decision_type"), DECISION_TYPES):
            errors.append(f"{location}: invalid decision_type '{decision.get('decision_type')}'")
        if not is_allowed(decision.get("ordering_convention"), ORDERING_CONVENTIONS):
            errors.append(f"{location}: invalid ordering_convention '{decision.get('ordering_convention')}'")
        if not nonempty_list(decision.get("candidate_explanations")):
            errors.append(f"{location}: candidate_explanations must be a non-empty list")
        if not nonempty_text(decision.get("ordering_effect")):
            errors.append(f"{location}: ordering_effect must state how ordering affected synthesis")
        if not nonempty_text(decision.get("unresolved_uncertainty")):
            errors.append(f"{location}: unresolved_uncertainty must be stated, even when none is known")
        if not nonempty_list(decision.get("authors")):
            errors.append(f"{location}: authors must be a non-empty list")
            continue
        for author in decision["authors"]:
            author_location = f"{location}:author"
            if not isinstance(author, dict):
                errors.append(f"{author_location}: expected an object")
                continue
            require_keys(
                author,
                (
                    "author_id",
                    "direct_contribution_source_ids",
                    "authorship_role_priors",
                    "relevant_claim_ids",
                    "supporting_weight",
                    "contradicting_weight",
                    "inferred_influence",
                    "evidence_level",
                ),
                author_location,
                errors,
            )
            if author.get("author_id") not in individuals:
                errors.append(f"{author_location}: unknown author_id '{author.get('author_id')}'")
            priors = author.get("authorship_role_priors")
            if not nonempty_list(priors) or any(
                not nonempty_text(prior) or prior not in ROLE_PRIORS for prior in list_or_empty(priors)
            ):
                errors.append(f"{author_location}: invalid authorship_role_priors")
            direct_source_ids = author.get("direct_contribution_source_ids")
            relevant_claim_ids = author.get("relevant_claim_ids")
            if not isinstance(direct_source_ids, list):
                errors.append(f"{author_location}: direct_contribution_source_ids must be a list")
            if not isinstance(relevant_claim_ids, list):
                errors.append(f"{author_location}: relevant_claim_ids must be a list")
            for source_id in list_or_empty(direct_source_ids):
                if not nonempty_text(source_id):
                    errors.append(f"{author_location}: contribution source references must be non-empty text")
                    continue
                if source_id not in source_index:
                    errors.append(f"{author_location}: unknown contribution source '{source_id}'")
            for claim_id in list_or_empty(relevant_claim_ids):
                if not nonempty_text(claim_id):
                    errors.append(f"{author_location}: relevant claim references must be non-empty text")
                    continue
                if claim_id not in included_claim_ids:
                    errors.append(f"{author_location}: relevant claim '{claim_id}' is unknown or omitted")
                elif claim_index[claim_id].get("author_id") != author.get("author_id"):
                    errors.append(f"{author_location}: relevant claim '{claim_id}' belongs to a different author")
            for weight_name in ("supporting_weight", "contradicting_weight"):
                weight = author.get(weight_name)
                if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
                    errors.append(f"{author_location}: {weight_name} must be a non-negative number")
            if not is_allowed(author.get("evidence_level"), EVIDENCE_LEVELS):
                errors.append(f"{author_location}: invalid evidence_level")
            if not nonempty_text(author.get("inferred_influence")):
                errors.append(f"{author_location}: inferred_influence must be stated")
    return record


def validate_reviewer_scope(path: Path, owner: dict[str, str], errors: list[str]) -> dict[str, Any] | None:
    record = load_json(path, errors)
    if record is None:
        return None
    validate_owner(record, owner, str(path), errors)
    require_keys(
        record,
        (
            "role",
            "status",
            "source_status",
            "material_scope",
            "requested_lenses",
            "external_processing_used",
            "external_services_authorized",
            "venue_policy_checked",
            "retention_policy_confirmed",
        ),
        str(path),
        errors,
    )
    if record.get("role") != "reviewer":
        errors.append(f"{path}: role must be reviewer")
    if not is_allowed(record.get("source_status"), SOURCE_STATUSES):
        errors.append(f"{path}: invalid source_status '{record.get('source_status')}'")
    if not isinstance(record.get("material_scope"), list):
        errors.append(f"{path}: material_scope must be a list")
    lenses = record.get("requested_lenses")
    if not isinstance(lenses, list) or any(
        not nonempty_text(lens) or lens not in REVIEW_LENSES for lens in list_or_empty(lenses)
    ):
        errors.append(f"{path}: requested_lenses contains an invalid reviewer lens")
    if record.get("source_status") == "unpublished" and record.get("external_processing_used") is True:
        for permission in ("external_services_authorized", "venue_policy_checked", "retention_policy_confirmed"):
            if record.get(permission) is not True:
                errors.append(f"{path}: unpublished external processing requires {permission}=true")
    return record


def validate_review_findings(path: Path, owner: dict[str, str], errors: list[str]) -> int:
    records = load_jsonl(path, errors)
    required = (
        "finding_id",
        "owner",
        "role",
        "lens",
        "finding_type",
        "claim_id",
        "location",
        "observation",
        "criterion",
        "supporting_evidence",
        "counterevidence",
        "alternative_explanations",
        "evidence_state",
        "consequence",
        "severity",
        "requested_action",
        "confidence",
        "not_assessed_reason",
    )
    seen: set[str] = set()
    for record in records:
        location = record.pop("_record_location")
        require_keys(record, required, location, errors)
        validate_owner(record, owner, location, errors)
        finding_id = record.get("finding_id")
        if not nonempty_text(finding_id):
            errors.append(f"{location}: finding_id must be non-empty text")
        elif finding_id in seen:
            errors.append(f"{location}: duplicate finding_id '{finding_id}'")
        else:
            seen.add(finding_id)
        if record.get("role") != "reviewer":
            errors.append(f"{location}: role must be reviewer")
        if not is_allowed(record.get("lens"), REVIEW_LENSES):
            errors.append(f"{location}: invalid reviewer lens '{record.get('lens')}'")
        if not is_allowed(record.get("finding_type"), FINDING_TYPES):
            errors.append(f"{location}: invalid finding_type '{record.get('finding_type')}'")
        if not is_allowed(record.get("severity"), SEVERITIES):
            errors.append(f"{location}: invalid severity '{record.get('severity')}'")
        if not is_allowed(record.get("evidence_state"), EVIDENCE_STATES):
            errors.append(f"{location}: invalid evidence_state '{record.get('evidence_state')}'")
        for field in ("supporting_evidence", "counterevidence", "alternative_explanations"):
            if not isinstance(record.get(field), list):
                errors.append(f"{location}: {field} must be a list")
        if record.get("evidence_state") == "not-assessed" and not nonempty_text(record.get("not_assessed_reason")):
            errors.append(f"{location}: not-assessed findings require not_assessed_reason")
        if record.get("finding_type") in {"strength", "concern", "limitation"}:
            for field in ("location", "observation", "criterion", "consequence", "confidence"):
                if not nonempty_text(record.get(field)):
                    errors.append(f"{location}: {field} is required for evaluative findings")
            if not nonempty_list(record.get("supporting_evidence")):
                errors.append(f"{location}: evaluative findings require supporting_evidence")
        if record.get("finding_type") == "concern" and not nonempty_text(record.get("requested_action")):
            errors.append(f"{location}: concerns require the smallest proportionate requested_action")
        for forbidden in ("acceptance_decision", "venue_recommendation", "overall_score"):
            if forbidden in record:
                errors.append(f"{location}: Reviewer cannot persist editorial field '{forbidden}'")
    return len(records)


def validate_namespace(namespace: Path, owner: dict[str, str], *, write_report: bool = True) -> dict[str, Any]:
    errors = validate_shared_model(namespace, owner)
    warnings: list[str] = []
    author_root = namespace / "author-research"
    sources = load_jsonl(author_root / "sources.jsonl", errors)
    source_index = validate_source_records(sources, owner, errors)
    claims = load_jsonl(author_root / "claims.jsonl", errors)
    claim_index, included_claim_ids = validate_claim_records(claims, owner, source_index, errors)
    research_status = validate_research_status(author_root / "research-status.json", owner, errors, warnings)
    individuals = validate_individuals(
        author_root / "individuals", owner, source_index, claim_index, included_claim_ids, errors
    )
    composite = validate_composite(
        author_root / "composite.json",
        owner,
        source_index,
        claim_index,
        included_claim_ids,
        individuals,
        errors,
    )
    validate_owned_markdown(author_root / "composite.md", owner, errors)
    reviewer_root = namespace / "role-state" / "reviewer"
    validate_reviewer_scope(reviewer_root / "scope.json", owner, errors)
    finding_count = validate_review_findings(reviewer_root / "findings.jsonl", owner, errors)

    expected_authors = (
        {
            author_id
            for author_id in list_or_empty(research_status.get("author_ids"))
            if nonempty_text(author_id)
        }
        if research_status
        else set()
    )
    if research_status and research_status.get("status") in {"ready", "ready-with-gaps"}:
        if expected_authors != set(individuals):
            errors.append("research-status author_ids must match the individual-author artifacts")

    author_ready = bool(
        not errors
        and research_status
        and research_status.get("status") in {"ready", "ready-with-gaps"}
        and composite
        and composite.get("status") == "ready"
    )
    report = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "owner": owner,
        "status": "valid" if not errors else "invalid",
        "validated_at": now_utc(),
        "author_context_ready": author_ready,
        "counts": {
            "sources": len(source_index),
            "claims": len(claim_index),
            "included_claims": len(included_claim_ids),
            "individual_authors": len(individuals),
            "composite_claims": len(list_or_empty(composite.get("claims"))) if composite else 0,
            "composite_decisions": len(list_or_empty(composite.get("decisions"))) if composite else 0,
            "review_findings": finding_count,
        },
        "errors": errors,
        "warnings": warnings,
    }
    report_path = author_root / "validation.json"
    can_write = True
    if report_path.exists():
        existing_errors: list[str] = []
        existing = load_json(report_path, existing_errors)
        if existing is None or not owner_matches(existing.get("owner"), owner):
            errors.extend(existing_errors or [f"{report_path}: owner does not match resolved paper"])
            report["status"] = "invalid"
            report["errors"] = errors
            can_write = False
    if write_report and can_write:
        atomic_write_json(report_path, report)
    return report


def validate_non_author_context(namespace: Path, owner: dict[str, str], role: str) -> list[str]:
    errors = validate_shared_model(namespace, owner)
    if role == "reviewer":
        reviewer_root = namespace / "role-state" / "reviewer"
        validate_reviewer_scope(reviewer_root / "scope.json", owner, errors)
        validate_review_findings(reviewer_root / "findings.jsonl", owner, errors)
    return errors


def resolve(raw_root: str | None, raw_alias: str | None) -> tuple[Path, dict[str, str], dict[str, Any]]:
    from paper_registry import command_resolve, state_root

    root = state_root(raw_root)
    resolved = command_resolve(root, raw_alias)
    namespace = Path(resolved["namespace"])
    owner = {"alias": resolved["alias"], "paper_id": resolved["paper_id"]}
    return namespace, owner, resolved


def command_scaffold(raw_root: str | None, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner, _ = resolve(raw_root, raw_alias)
    created = initialize_artifact_scaffold(namespace, owner)
    return {"status": "scaffolded", "owner": owner, "namespace": str(namespace), "created": created}


def command_validate(raw_root: str | None, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner, _ = resolve(raw_root, raw_alias)
    initialize_artifact_scaffold(namespace, owner)
    return validate_namespace(namespace, owner)


def command_context(raw_root: str | None, role: str, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner, _ = resolve(raw_root, raw_alias)
    initialize_artifact_scaffold(namespace, owner)
    if role == "author":
        report = validate_namespace(namespace, owner)
        if report["status"] != "valid" or not report["author_context_ready"]:
            raise ArtifactError(
                "Author context is not ready; complete and validate per-author research and the Composite Author."
            )
        allowed = [
            namespace / "paper-model.md",
            namespace / "author-research" / "sources.jsonl",
            namespace / "author-research" / "claims.jsonl",
            namespace / "author-research" / "research-status.json",
            namespace / "author-research" / "individuals",
            namespace / "author-research" / "composite.json",
            namespace / "author-research" / "composite.md",
        ]
    elif role in {"reviewer", "researcher"}:
        errors = validate_non_author_context(namespace, owner, role)
        if errors:
            raise ArtifactError("Context validation failed: " + "; ".join(errors))
        allowed = [namespace / "paper-model.md"]
        if role == "reviewer":
            allowed.append(namespace / "role-state" / "reviewer")
    else:
        raise ArtifactError("P0 context checks support author, reviewer, or researcher.")
    return {
        "status": "allowed",
        "owner": owner,
        "role": role,
        "allowed_paths": [str(path) for path in allowed if path.exists()],
        "denied_paths": [str(namespace / "author-research")] if role != "author" else [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="State directory; defaults to .papertalk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold = subparsers.add_parser("scaffold", help="Create missing P0 artifact files")
    scaffold.add_argument("alias", nargs="?")

    validate = subparsers.add_parser("validate", help="Validate the complete P0 artifact contract")
    validate.add_argument("alias", nargs="?")

    context = subparsers.add_parser("context", help="Return only paths allowed for a role")
    context.add_argument("role", choices=("author", "reviewer", "researcher"))
    context.add_argument("alias", nargs="?")
    return parser


def emit(value: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(value, stream, indent=2, sort_keys=True)
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "scaffold":
            result = command_scaffold(args.root, args.alias)
        elif args.command == "validate":
            result = command_validate(args.root, args.alias)
            if result["status"] != "valid":
                emit(result, stream=sys.stderr)
                return 2
        elif args.command == "context":
            result = command_context(args.root, args.role, args.alias)
        else:  # pragma: no cover
            raise ArtifactError(f"Unsupported command: {args.command}")
    except Exception as exc:
        registry_error = exc.__class__.__name__ == "RegistryError"
        if not isinstance(exc, ArtifactError) and not registry_error:
            raise
        emit({"status": "error", "error": str(exc)}, stream=sys.stderr)
        return 2
    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
