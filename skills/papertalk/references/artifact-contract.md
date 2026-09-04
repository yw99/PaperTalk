# P0 artifact contract

Read this reference when building, refreshing, validating, or loading persisted PaperTalk evidence. The readable Markdown explains the paper; these artifacts make ownership, provenance, filtering, coverage, and composite synthesis auditable.

## Commands

Run relative to the skill directory:

```text
python3 scripts/paper_artifacts.py [--root <state-dir>] scaffold [alias]
python3 scripts/paper_artifacts.py [--root <state-dir>] validate [alias]
python3 scripts/paper_artifacts.py [--root <state-dir>] context <author|reviewer|researcher> [alias]
```

- `scaffold` adds missing P0 files without overwriting existing state.
- `validate` validates all P0 records and writes `author-research/validation.json`. Treat a nonzero exit as a hard failure.
- `context` returns only the paths that the requested role may load. Run it before loading persisted analysis state. Author is denied until per-author research and the composite are ready; Reviewer and Researcher never receive an author-research path.

Interactive Panel transcripts are conversation state rather than evidence artifacts. `scripts/panel_sessions.py` owns and validates them, and delegates every initial or continuation role context back to this helper. A peer Panel turn never becomes an allowed evidence path. Read [panel-sessions.md](panel-sessions.md) for that contract.

Never repair validation failures by weakening the recorded evidence. Correct the source, claim, ownership, or synthesis record and rerun validation.

## Namespace

```text
.papertalk/papers/<alias>/
├── paper-model.md
├── author-research/
│   ├── sources.jsonl
│   ├── claims.jsonl
│   ├── research-status.json
│   ├── individuals/<author-id>.json
│   ├── individuals/<author-id>.md
│   ├── composite.json
│   ├── composite.md
│   └── validation.json
├── role-state/reviewer/
│   ├── scope.json
│   └── findings.jsonl
└── conversation-state/
    ├── panel-sessions.json    Created lazily
    └── panel-sessions.lock    Internal mutation lock
```

Every JSON object and JSONL record uses:

```json
{"owner":{"alias":"paper-alias","paper_id":"sha256:..."}}
```

Use stable IDs within one paper namespace. IDs are not global and must never be resolved across aliases.

## Source records

Write one JSON object per line to `author-research/sources.jsonl`:

```json
{
  "source_id": "src-paper",
  "owner": {"alias": "paper-alias", "paper_id": "sha256:..."},
  "author_id": "paper",
  "url_or_path": "https://example.org/paper",
  "title": "Paper title",
  "source_type": "P",
  "publication_date": "2026-01-01",
  "retrieved_at": "2026-09-04T12:00:00+00:00",
  "primary_or_secondary": "primary",
  "identity_match_evidence": ["author list and affiliation"],
  "target_relevance": "target paper",
  "content_location": ["§1", "§3"]
}
```

`source_type` is `P`, `AW`, `AS`, or `D`. Use `author_id: "paper"` for a target-paper source shared by several authors; otherwise use the matched author's stable ID. Discovery metadata may locate evidence but should not carry a mindset claim by itself.

## Claim records and filter

Write every considered claim—including rejected candidates—to `author-research/claims.jsonl`. This keeps omission auditable. Only records with `claim_filter.disposition: "include"` may enter an individual distillate or composite.

```json
{
  "claim_id": "claim-exactness",
  "owner": {"alias": "paper-alias", "paper_id": "sha256:..."},
  "author_id": "author-1",
  "claim": "The author favors exact marginal preservation for this decision.",
  "dimension": "evidence standard",
  "evidence_level": "I",
  "supporting_source_ids": ["src-paper"],
  "supporting_locations": ["§1", "Theorem 1"],
  "counterevidence_source_ids": [],
  "alternative_explanations": ["Exactness may be imposed by the estimand rather than a durable preference."],
  "relevance_to_target_paper": "Explains the coupling constraint.",
  "linked_paper_decisions": ["decision-coupling"],
  "temporal_scope": "target paper",
  "confidence": "moderate",
  "rationale": "The method repeatedly rejects approximations that change finite-horizon laws.",
  "claim_filter": {
    "gates": {
      "recurrence": {"outcome": "not-applicable", "rationale": "Target-paper inference only."},
      "target_relevance": {"outcome": "pass", "rationale": "Directly explains a central constraint."},
      "predictive_value": {"outcome": "pass", "rationale": "Predicts rejection of biased reuse schemes."},
      "specificity": {"outcome": "pass", "rationale": "More specific than a generic preference for rigor."}
    },
    "classification": "decision-heuristic",
    "disposition": "include"
  }
}
```

Allowed classifications are:

- `durable`: supported across relevant works or decisions and useful for this paper;
- `decision-heuristic`: useful but narrow or localized;
- `paper-specific-explicit`: explicitly stated in a target-paper source, even without recurrence;
- `omit`: generic, weak, irrelevant, or untraceable.

An `E` claim requires a direct source and location. An `I` or `H` claim requires supporting sources plus a rationale. Always preserve counterevidence and plausible alternative explanations.

## Research depth and author files

`research-status.json` records `tier` as `quick`, `standard`, or `deep`, every named `author_id`, whether breadth-first coverage is complete, coverage gaps, the research-quality checkpoint, and the evidence-based stopping reason. Standard and Deep research cannot become ready until the user-facing quality checkpoint is accepted. Use `ready-with-gaps` when every author was considered but relevant public evidence remains sparse.

Each `individuals/<author-id>.json` records:

```json
{
  "schema_version": 1,
  "owner": {"alias": "paper-alias", "paper_id": "sha256:..."},
  "author_id": "author-1",
  "author_name": "Name",
  "status": "ready",
  "identity_evidence_source_ids": ["src-paper"],
  "authorship_metadata": {
    "position": 1,
    "author_count": 3,
    "equal_contribution_group": [],
    "is_corresponding_author": false,
    "ordering_convention": "contribution-ordered",
    "ordering_convention_confidence": "moderate"
  },
  "coverage": {
    "tier": "quick",
    "searched_source_ids": ["src-paper"],
    "included_source_ids": ["src-paper"],
    "gaps": [],
    "stopping_reason": "Further searching did not change the retained high-confidence claims."
  },
  "mindset_claim_ids": ["claim-exactness"],
  "target_paper_connections": ["decision-coupling"],
  "explicit_contribution_source_ids": ["src-paper"]
}
```

Quick uses the paper, official artifacts, verified contribution metadata, and the closest useful author work. Standard makes a breadth-first pass over every author, searches counterevidence, and pauses at a quality checkpoint. Deep adds broader trajectories, project history, rebuttals, code history, external technical perspectives, and behavioral validation. These are depth definitions, not fixed source quotas. Stop when additional sources no longer materially change high-confidence claims; record why.

## Composite Author

`composite.json` has `status: not-built | draft | ready`, its author IDs, traceable composite claims, and a decision record for each major paper choice:

```json
{
  "decision_id": "decision-coupling",
  "decision": "Preserve every policy's finite-horizon law.",
  "decision_type": "mixed",
  "candidate_explanations": ["estimand validity", "preference for exact reuse"],
  "authors": [{
    "author_id": "author-1",
    "direct_contribution_source_ids": ["src-paper"],
    "authorship_role_priors": ["first"],
    "relevant_claim_ids": ["claim-exactness"],
    "supporting_weight": 1.0,
    "contradicting_weight": 0.0,
    "inferred_influence": "Strong execution-facing influence; direction influence remains plausible.",
    "evidence_level": "I"
  }],
  "ordering_convention": "contribution-ordered",
  "ordering_effect": "The first-author prior increased execution influence but did not determine the conclusion.",
  "unresolved_uncertainty": "No direct project-history statement is available."
}
```

Direct contribution evidence dominates. First/co-first, corresponding, field-specific senior, and neutral priors may overlap and remain decision-specific. Alphabetical, mixed, unknown, and large-collaboration cases weaken positional inference. Every composite claim must point to included individual claim IDs; disagreement is retained through supporting and contradicting links rather than averaged away.

## Reviewer artifacts

Before consequential review, set `role-state/reviewer/scope.json`: source status, material actually available, requested lenses, and any external-processing authorization. If an unpublished manuscript would leave the local environment, the validator requires affirmative external-service authorization, a venue-policy check, and a confirmed retention policy.

Reviewer findings use the contract in [reviewer.md](reviewer.md). They remain role-specific and must never be copied into the shared paper model or author research as paper facts.
