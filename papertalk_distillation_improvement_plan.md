# PaperTalk Distillation Improvement Plan

## Summary

PaperTalk already has a strong conceptual model for paper-specific author distillation: every author is distilled independently, the results are combined into a decision-specific Composite Author, author ordering is treated as a calibrated prior, and author-derived information is isolated from Reviewer and Researcher roles.

The main improvement is to make that design operational and verifiable. The next version should add machine-readable evidence artifacts, explicit claim filtering, research-depth controls, behavioral evaluation, correction history, and lazy retrieval. It should preserve PaperTalk's paper ownership and role boundaries rather than adopting a global reusable persona model.

## Design Principles

1. Keep every interpretation owned by exactly one `(alias, paper_id)` namespace.
2. Distill every named author independently before constructing the Composite Author.
3. Treat direct contribution evidence as stronger than author-order heuristics.
4. Use first/co-first, corresponding, and field-specific senior-author positions only as decision-specific priors.
5. Separate explicit evidence, supported inference, and hypothesis.
6. Preserve contradictions, alternative explanations, missing evidence, and changes over time.
7. Give only Author mode access to author research; Reviewer and Researcher must remain independent.
8. Optimize for research-decision reconstruction rather than personality imitation.

## Lessons from Related Skills

### Nuwa

Adopt:

- research depth tiers and local/network evidence modes
- separate evidence-collection channels
- explicit candidate filtering
- preservation of contradictions and insufficient evidence
- user checkpoints after research and synthesis
- independent behavioral validation
- bounded refinement loops

Adapt Nuwa's recurrence, generativity, and distinctiveness tests to PaperTalk's target-conditioned setting. Do not copy its global-person model, broad life-history collection, strong expression mimicry, or fixed mental-model quotas.

Source: <https://github.com/alchaincyf/nuwa-skill>

### Distilly

Adopt versioned profiles, explicit corrections, reviewable candidates, promotion/rejection, rollback, deterministic ingestion, and fail-closed behavior when a complete evidence package cannot fit the available context.

Source: <https://github.com/titanwings/distilly>

### book-to-skill

Adopt structure-aware source extraction, cost estimation, decision-oriented artifacts, and lazy loading of only the relevant parts of a large corpus.

Source: <https://github.com/virgiliojr94/book-to-skill>

### Academic and deep-research skills

Adopt evidence ledgers, source dates and authority metadata, documented search gaps, counter-claim review, contradiction inventories, claim-strength drift checks, citation verification, and staged quality gates.

Sources:

- <https://github.com/Imbad0202/academic-research-skills>
- <https://github.com/pinshuai/literature-review-skill>
- <https://github.com/daymade/claude-code-skills/tree/main/deep-research>

### Skill evaluation systems

Adopt realistic test prompts, with-skill versus baseline comparisons, independent evaluators, regression testing, early stopping, and keep-or-revert refinement.

Sources:

- <https://github.com/anthropics/skills/tree/main/skills/skill-creator>
- <https://github.com/alchaincyf/darwin-skill>

## Proposed Distillation Pipeline

```text
Resolve paper and owner
        |
        v
Verify author identities and authorship metadata
        |
        v
Build an auditable source ledger for every author
        |
        v
Extract and validate target-conditioned mindset claims
        |
        v
Build independent per-author distillates
        |
        v
Synthesize decisions into the Composite Author
        |
        v
Run evidence, behavior, role-leakage, and alias-isolation tests
        |
        v
Publish a versioned active distillate
```

## P0: Make the Evidence Contract Executable

### Machine-readable artifacts

Store auditable artifacts alongside the readable Markdown files:

```text
.papertalk/papers/<alias>/author-research/
├── sources.jsonl
├── claims.jsonl
├── individuals/
│   ├── <author-id>.json
│   └── <author-id>.md
├── composite.json
├── composite.md
└── validation.json
```

All files must carry the same owner:

```yaml
owner:
  alias: <alias>
  paper_id: <paper_id>
```

### Source record

Each source should record at least:

```yaml
source_id:
owner:
author_id:
url_or_path:
title:
source_type: P | AW | AS | D
publication_date:
retrieved_at:
primary_or_secondary:
identity_match_evidence:
target_relevance:
content_location:
```

### Claim record

Each author-mindset claim should record:

```yaml
claim_id:
owner:
author_id:
claim:
dimension:
evidence_level: E | I | H
supporting_source_ids: []
supporting_locations: []
counterevidence_source_ids: []
alternative_explanations: []
relevance_to_target_paper:
linked_paper_decisions: []
temporal_scope:
confidence:
```

### Deterministic validation

Add a validator that fails closed when:

- an artifact's owner does not match the resolved `(alias, paper_id)`;
- a claim references an unknown or differently owned source;
- an `[E]` claim lacks a direct source location;
- an `[I]` or `[H]` claim lacks its supporting evidence and rationale;
- a composite claim cannot be traced to individual author claims;
- author-derived evidence appears in the shared paper model;
- a non-Author context attempts to load author-research artifacts.

## P0: Add a Paper-Specific Claim Filter

Evaluate candidate claims with four gates:

1. **Recurrence:** Does the tendency appear across multiple relevant works, decisions, or source types?
2. **Target relevance:** Does it help explain a concrete choice, constraint, or tradeoff in this paper?
3. **Predictive value:** Can it reconstruct a withheld paper decision or distinguish among plausible alternatives?
4. **Specificity:** Is it more informative than a generic research virtue or normal field practice?

Classification:

- Strong across all applicable gates: durable target-conditioned mindset tendency.
- Useful but narrow: decision heuristic or localized tendency.
- Explicit only in the target source: retain as a paper-specific `[E]` claim even without recurrence.
- Weak, generic, or untraceable: omit from the author model.

Do not require every valid paper-specific claim to recur across unrelated domains. A one-off explicit statement can still matter greatly for the target paper.

## P0: Research Depth and Stopping Rules

Support three research tiers:

### Quick

- target paper and official artifacts
- verified authorship and contribution metadata
- one or two closest relevant works per author
- explicit coverage and confidence report

### Standard

- breadth-first pass over every author
- several topically and temporally close works per author
- public technical statements where available
- contradiction and alternative-explanation search
- user-visible research-quality checkpoint

### Deep

- broader scholarly trajectory
- talks, interviews, project histories, rebuttals, and code history
- stronger temporal analysis
- external technical perspectives
- behavioral validation and independent review

Stop when additional sources no longer materially change the high-confidence claims. Do not use a fixed source quota. For long author lists, preserve breadth-first coverage before deepening authors with larger public footprints.

## P0: Strengthen Composite Author Synthesis

Keep the existing decision-specific contribution logic, but represent it explicitly for every major paper decision:

```yaml
decision_id:
decision:
decision_type: direction | execution | mixed
candidate_explanations: []
authors:
  - author_id:
    direct_contribution_evidence: []
    authorship_role_priors: []
    relevant_claim_ids: []
    supporting_weight:
    contradicting_weight:
    inferred_influence:
    evidence_level:
ordering_convention:
ordering_effect:
unresolved_uncertainty:
```

Rules:

- direct contribution statements and attributable artifacts dominate;
- first/co-first authors receive strong general and execution priors, while remaining eligible for topic and motivation influence;
- corresponding authors receive an additional direction-facing prior without excluding first authors;
- last/senior-author priors apply only when field conventions or evidence support them;
- alphabetical, mixed, unknown, and large-collaboration cases weaken ordering priors;
- every author retains a nonzero prior that direct evidence can override;
- disagreement must remain visible rather than being averaged into false consensus.

## P1: Behavioral and Safety Evaluation

### Proposed scorecard

| Dimension | Weight |
|---|---:|
| Claim-to-source traceability | 25 |
| Paper-decision reconstruction fidelity | 25 |
| Honest uncertainty and boundary behavior | 15 |
| Composite contribution calibration | 15 |
| Role and alias isolation | 15 |
| Conversational usefulness | 5 |

Evidence fidelity should matter substantially more than voice resemblance.

### Representative tests

- Withhold a paper section and test whether the author model reconstructs the actual decision from earlier evidence.
- Ask about an issue the authors have never publicly addressed and require explicit uncertainty.
- Remove one author's distillate and measure which composite conclusions change.
- Change or disable ordering priors and inspect sensitivity.
- Test single-author, co-first, corresponding-author, alphabetical, mixed-order, and large-consortium papers.
- Verify that Reviewer and Researcher cannot reproduce `[AW]` or `[AS]` information available only to Author.
- Register papers sharing an author, terminology, or source URL and test for cross-alias leakage.
- Test that a strong paper does not receive invented criticism and a weak paper does not receive unsupported praise.
- Compare responses with and without author research to show that the distillation adds decision-relevant value.

Where possible, use separate answering and evaluating agents. Record the prompt, active artifact version, model, result, evaluator rationale, token use, and execution time.

## P1: Versioning and Corrections

Use a reviewable lifecycle:

```text
draft
  -> validated candidate
      -> active version
      -> rejected candidate

active version
  -> correction candidate
      -> promoted version
      -> rejected correction
      -> rollback to earlier version
```

Never silently overwrite an active distillate. Record:

- source additions and removals;
- claims added, weakened, contradicted, or removed;
- changes to author identity or authorship-role interpretation;
- changes to composite decisions;
- validation results before and after the change;
- the reason a version was promoted, rejected, or rolled back.

## P2: Lazy Retrieval and External Adapters

At answer time, resolve `(alias, paper_id, role)` before retrieval. Load only:

- relevant shared-paper decisions and evidence;
- relevant per-author claim records for Author mode;
- relevant Composite Author decisions;
- compact coverage and uncertainty metadata.

Immutable raw source bytes may be content-addressed and deduplicated, but source selection, annotations, relevance scores, claims, author distillates, and composites must remain paper-specific.

External distillation tools may be supported through an adapter, but every result must be normalized to PaperTalk's schema and rejected if it lacks the correct owner, provenance, access classification, or uncertainty information. PaperTalk must retain a native fallback and must not depend on the name or private implementation of any external skill.

## Explicit Non-goals

Do not add:

- global author-persona profiles reused directly across papers;
- private, sensitive, demographic, or merely biographical profiling;
- strong expression imitation or claims to reproduce an author's personality;
- forced counts of mental models, heuristics, or contradictions;
- fixed source-count targets;
- unqualified domain-wide source blacklists;
- prestige-based mindset inference;
- a simple global author-weight average;
- author research in Reviewer or Researcher contexts.

A limited research-communication signature may help Author responses feel natural, but it should describe professional explanatory habits rather than attempt identity imitation.

## Suggested Delivery Sequence

### Milestone 1: Evidence foundation

- add source and claim schemas
- add owner-aware validators
- convert the existing TCAB distillate into the structured representation
- test claim-to-source and role-boundary failures

### Milestone 2: Native distillation pipeline

- implement research tiers
- implement candidate-claim filtering
- add coverage, contradiction, and stopping reports
- add the research-quality checkpoint

### Milestone 3: Composite validation

- implement decision-level contribution records
- add multi-author fixtures covering different ordering conventions
- add ordering-ablation and author-ablation tests

### Milestone 4: Behavioral evaluation

- add reconstruction, uncertainty, conversational, leakage, and baseline tests
- store repeatable evaluation results
- gate promotion of new distillate versions on regression results

### Milestone 5: Versioning and optional adapters

- add correction, promotion, rejection, and rollback
- add lazy retrieval indexes
- define and test the external-distillation adapter contract

## Success Criteria

The improvement is complete when:

1. Every author and composite claim is traceable to owned sources and locations.
2. Every registered author receives documented breadth-first coverage or an explicit gap.
3. Composite conclusions expose their contribution evidence, ordering priors, contradictions, and uncertainty.
4. Reviewer and Researcher tests prove that author-derived evidence is inaccessible to them.
5. Cross-paper tests remain isolated even when papers share authors or sources.
6. Behavioral tests demonstrate better decision reconstruction than the shared paper model alone.
7. Unsupported questions reliably produce bounded, hedged answers.
8. Distillate updates are versioned, reviewable, and reversible.
9. Ordinary PaperTalk responses remain concise and conversational despite the richer internal evidence model.
