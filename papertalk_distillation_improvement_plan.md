# PaperTalk Distillation Improvement Plan

## Summary

PaperTalk already has a strong conceptual model for paper-specific author distillation: every author is distilled independently, the results are combined into a decision-specific Composite Author, author ordering is treated as a calibrated prior, and author-derived information is isolated from Reviewer and Researcher roles.

The main improvement is to make that design operational and verifiable. The next version should add machine-readable evidence artifacts, explicit claim filtering, research-depth controls, calibrated Reviewer reasoning, paper-blind Researcher ideation, traceable Panel synthesis, behavioral evaluation, correction history, and lazy retrieval. It should preserve PaperTalk's paper ownership and role boundaries rather than adopting a global reusable persona model or turning ordinary paper conversation into a heavyweight referee workflow.

## Design Principles

1. Keep every interpretation owned by exactly one `(alias, paper_id)` namespace.
2. Distill every named author independently before constructing the Composite Author.
3. Treat direct contribution evidence as stronger than author-order heuristics.
4. Use first/co-first, corresponding, and field-specific senior-author positions only as decision-specific priors.
5. Separate explicit evidence, supported inference, and hypothesis.
6. Preserve contradictions, alternative explanations, missing evidence, and changes over time.
7. Give only Author mode access to author research; Reviewer and Researcher must remain independent.
8. Optimize for research-decision reconstruction rather than personality imitation.
9. Treat Reviewer as an evaluator, not an editor: assess how well claims hold without issuing venue decisions unless a separate, explicitly requested Editor role is introduced.
10. Judge strengths and concerns by the same evidence standard and calibrate severity by their effect on the paper's central claims.
11. Make Researcher generate alternatives before seeing the paper's eventual choice whenever the task calls for independent reconstruction.
12. Make Panel preserve role boundaries, provenance, and unresolved disagreement rather than treating votes or apparent consensus as truth.
13. Treat unpublished manuscripts as confidential material and respect the applicable venue's rules for AI-assisted review, external services, and retention.

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

### Reviewer, Researcher, and Panel skills

Adopt from scientific peer-review skills:

- neutral orientation before judgment
- explicit review scope and partial-evidence handling
- claim-to-evidence mapping
- methodology, statistics, novelty, evaluation, reproducibility, and ethics lenses
- severity based on consequences for central claims
- proportional, actionable requests
- conditional judgments when information is missing
- confidentiality and human-accountability boundaries for unpublished manuscripts

Adopt from research-ideation skills:

- independent candidate generation before exposure to preferred solutions
- separation of ideas, assumptions, predictions, evidence, and decisions
- falsifying observations and alternative explanations for each candidate
- literature checking after an initial generation round, followed by reopened ideation
- visible uncertainty, minority positions, and rejected alternatives

Adopt from panel and council skills:

- fresh or isolated contexts for each role
- commitment before peer visibility
- synthesis that traces back to role outputs
- explicit distinction among corroboration, value tension, error detection, and unresolved disagreement
- no majority-vote truth and no claim that same-model role separation creates independent error processes

Sources:

- <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/peer-review>
- <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-critical-thinking>
- <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-brainstorming>
- <https://github.com/Imbad0202/academic-research-skills/tree/main/academic-paper-reviewer>
- <https://github.com/neuromechanist/research-skills/tree/main/plugins/manuscript/skills/paper-review>
- <https://github.com/ngmeyer/council-review>

### Future Teacher and Implementer roles

For Teacher, adopt learner-goal calibration, intuition before formalism, prediction, bounded Socratic questioning, counterexamples, teach-back, and demonstrated-understanding gates. For Implementer, separate what the paper specifies, what official code implements, what PaperTalk infers, what default it chooses for underspecified details, and what has actually been reproduced.

Sources:

- <https://github.com/cskwork/supertutor-skill>
- <https://github.com/baizhanxu/research-paper-code-study-codex-skill>

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

Role execution remains downstream of this pipeline. Reviewer and Researcher receive only the owned shared paper model plus independently permitted task evidence. Author additionally receives the matching Composite Author. Panel constructs and freezes each role response under those same access rules before synthesis.

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

## P0: Add a Calibrated Reviewer Assessment Contract

Keep Reviewer concise and conversational by default, but make its internal reasoning reproducible:

```text
Establish review scope
        |
        v
Construct a neutral claim map without deciding
        |
        v
Select only the relevant review lens or lenses
        |
        v
Compare each claim with required and supplied evidence
        |
        v
Classify findings by type, consequence, and confidence
        |
        v
Give a proportionate judgment and state what would resolve uncertainty
```

### Review scope and evidence availability

Before making a consequential judgment, determine:

- whether the source is a public paper, preprint, partial excerpt, or unpublished manuscript;
- which sections, appendices, figures, supplements, code, data, or prior reviews are available;
- the user's question and desired review depth;
- the relevant field, study type, and methodology;
- the target venue or review standard, if the user supplied one;
- which issues exceed the reviewer's competence or available evidence.

Never infer missing content. Distinguish explicitly among:

- **contradicted:** available evidence conflicts with the claim;
- **unsupported:** the supplied evidence does not establish the claim;
- **not reported:** the paper does not supply required information;
- **not available for review:** the relevant artifact was not provided or accessible;
- **not assessed:** the issue is outside the requested scope or available competence.

For partial material, answer the requested question but disclose the incomplete scope and lower confidence. For unpublished material, confirm authorization and applicable venue rules before using external services; default to local-only processing when permission is unclear.

### Neutral orientation before judgment

Create a compact internal map of:

- research question and target quantity;
- principal claims;
- design, method, or proof strategy;
- comparators and baselines;
- outcomes and uncertainty;
- evidence needed for each consequential claim.

Do not decide whether the paper is convincing until this map exists.

### Reviewer lenses

Keep one Reviewer role and route the task to one or more internal lenses:

| Task or question | Primary lens |
|---|---|
| `assess`, general judgment | claim–evidence alignment and significance |
| `claims`, `does this follow?` | logical and evidential validity |
| `methods` | design, assumptions, controls, and statistics |
| `novelty` | related literature and differentiation |
| `evaluation` | whether experiments or proofs test the central claims |
| `reproducibility` | specification, artifacts, code, data, and execution requirements |
| `ethics` | applicable ethics, safety, consent, privacy, and dual-use issues |
| `re-review` | whether specified prior concerns were actually resolved |
| `attack` | strongest counterargument, failure mode, or alternative explanation |

Use external literature only when the requested lens needs it, such as novelty, citation support, or a disputed methodological standard. Do not search merely to make an ordinary question-focused answer look comprehensive.

### Review finding record

Represent both merits and concerns with the same evidence-bearing schema:

```yaml
review_finding:
  owner: {alias: <alias>, paper_id: <paper_id>}
  role: reviewer
  lens: claims | methods | theory | novelty | evaluation | reproducibility | ethics
  finding_type: strength | concern | limitation | question
  claim_id:
  location:
  observation:
  criterion:
  supporting_evidence: []
  counterevidence: []
  alternative_explanations: []
  consequence:
  severity: critical | major | minor | clarification | observation
  requested_action:
  confidence:
  not_assessed_reason:
```

Reviewer findings are role-specific artifacts or ephemeral task state. They must not enter the shared paper model as paper facts and must never be written into author research.

### Severity and proportionality

Assign severity by consequence rather than rhetorical intensity:

- **Critical:** invalidates or makes a central conclusion uninterpretable.
- **Major:** materially changes a central claim, its scope, or confidence and requires substantial new analysis, evidence, or reframing.
- **Minor:** improves rigor, clarity, or completeness without changing the main conclusion.
- **Clarification:** missing information prevents a bounded assessment; it is not yet evidence of a defect.
- **Observation:** a relevant strength, limitation, tradeoff, or question that does not require correction.

Every concern should state its location, observation, criterion or evidence, why it matters, and the smallest proportionate action that would resolve or bound it. Request new experiments only when they are necessary for a central claim; otherwise prefer clarification, narrower claims, sensitivity analysis, correction, or explicit limitation language.

Reviewer evaluates the paper but does not impersonate an assigned referee or issue an editorial acceptance decision. If venue-level adjudication becomes useful, introduce a separate explicitly requested Editor role later.

### Default Reviewer response

Preserve the existing one-to-three-paragraph conversational contract. A normal answer should compress the internal assessment into:

```text
my judgment
→ strongest evidence supporting it
→ most material reservation or missing evidence, if relevant
→ how much that changes the conclusion
```

Do not force a concern into a strong paper or praise into a weak one. When there is no material concern at the requested scope, say so directly and identify the scope limitation.

## P1: Make Researcher Genuinely Paper-Blind

Researcher should reconstruct possible paths as though the paper's later choices were not yet known. When the task is `reconstruct`, `alternatives`, or a section-bounded continuation, freeze the permitted paper cutoff before generating candidates and do not expose later sections, author research, or the paper's chosen answer until the independent pass is complete.

Use this workflow:

```text
Freeze the paper at the requested cutoff
        |
        v
Extract the unresolved problem, constraints, and available tools
        |
        v
Generate several independent candidate approaches
        |
        v
Expose assumptions, mechanisms, predictions, and failure modes
        |
        v
Identify evidence or experiments that distinguish the candidates
        |
        v
Check relevant literature when needed and reopen ideation once
        |
        v
Only then reveal and evaluate the paper's actual choice
```

Represent each serious candidate as:

```yaml
research_candidate:
  owner: {alias: <alias>, paper_id: <paper_id>}
  idea_id:
  stage: independent | post-literature | compared-with-paper
  premise:
  proposed_mechanism:
  assumptions: []
  expected_advantage:
  discriminating_prediction:
  falsifying_observation:
  feasibility:
  likely_failure_mode:
  value_if_null:
  related_evidence: []
  evidence_status: idea | assumption | prediction | located-evidence | decision
```

Researcher tasks should include:

- `reconstruct`: continue from a paper cutoff without hindsight;
- `alternatives`: generate distinct routes to the same goal;
- `extend`: derive next questions from unresolved constraints, failure modes, or missing evidence;
- `design-experiment`: propose the smallest test that distinguishes explanations;
- `falsify`: search for a counterexample or observation that would defeat a claim;
- `compare`: contrast candidates on stable, predeclared criteria.

Do not automatically choose a winner. Preserve minority candidates, negative evidence, uncertainty, and rejected alternatives. Define evaluation criteria before scoring, do not hide veto conditions inside averages, and never treat absence from a bounded literature search as proof of novelty.

## P1: Make Panel Independent and Traceable

The initial-response freezing and targeted interaction subset is now implemented. `$papertalk panel` persists independently generated initial turns, while `$papertalk panel_continue @alias responder:target [guidance]` lets one role answer the selected role's newest turn from that paper's latest Panel. Each paper retains older Panels as non-selectable read-only history; there are no user-facing Panel IDs. The continuation helper reuses role-safe artifact contexts, marks peer turns as claims rather than evidence, and rejects stale context tokens.

Moderator synthesis and the richer disagreement classification below remain future work.

Panel is a composition of role outputs over one owned paper model, not a blended persona and not a vote. Use this protocol:

```text
Resolve one paper and freeze the shared facts
        |
        v
Construct each role's permitted context independently
        |
        v
Produce and freeze every initial response without peer visibility
        |
        v
Load only the frozen role outputs into synthesis
        |
        v
Report agreement, disagreement, decisive evidence, and unresolved questions
```

Only Author receives the Composite Author. Reviewer and Researcher receive the shared paper model and their independently permitted task evidence. If isolated contexts are unavailable, produce and freeze non-Author responses before loading author research, exactly as required by the existing PaperTalk access boundary.

Panel synthesis must:

- trace every synthesized point to one or more frozen role outputs;
- never invent a finding that no role produced;
- distinguish corroborated observations from merely repeated wording;
- preserve a role's strongest dissent even when the other roles agree;
- disclose that same-model role separation is not evidence of independent error processes;
- avoid majority voting as a substitute for evidence;
- leave a disagreement unresolved when the available evidence cannot settle it;
- state what observation, source, derivation, or experiment would resolve a material disagreement.

Classify disagreements as:

- **Corroborated observation:** roles independently reach a compatible conclusion through permitted evidence or distinct reasoning.
- **Value or priority tension:** both positions may be valid under different research goals.
- **Error catch:** one role identifies a factual, logical, or evidential defect missed by others.
- **Role-dependent answer:** the roles differ because they intentionally answer different questions.
- **Unresolved disagreement:** evidence is insufficient to adjudicate.

Keep the default panel conversational: normally one short initial turn per role. Targeted continuation produces exactly one named responder turn without synthesis. A future moderator mode may add a compact synthesis stating what the roles agree on, where they differ, and what would settle it.

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

#### Author and Composite Author

- Withhold a paper section and test whether the author model reconstructs the actual decision from earlier evidence.
- Ask about an issue the authors have never publicly addressed and require explicit uncertainty.
- Remove one author's distillate and measure which composite conclusions change.
- Change or disable ordering priors and inspect sensitivity.
- Test single-author, co-first, corresponding-author, alphabetical, mixed-order, and large-consortium papers.

#### Reviewer

- Test that a strong paper does not receive invented criticism and a weak paper does not receive unsupported praise.
- Give the Reviewer a central flaw and a peripheral flaw, then verify that severity follows consequences for the main claims.
- Remove a necessary appendix, baseline, or artifact and verify that the result is `not available for review`, `not reported`, or conditional rather than an accusation.
- Compare partial-material and full-paper reviews and require the confidence and scope statements to change.
- Verify that every concern identifies its location, criterion or evidence, consequence, and smallest proportionate action.
- Verify that new experiments are requested only when needed to support a central claim.
- Confirm that novelty or citation questions trigger bounded literature work while ordinary paper-local questions do not.
- In re-review mode, verify the revised artifact against the prior concern rather than accepting the response letter's assertion.
- Confirm that Reviewer does not issue a venue acceptance decision unless a separate Editor role is explicitly requested in a later version.
- For an unpublished manuscript, verify that external browsing or retention is not used without authorization and applicable venue-policy checks.

#### Researcher and Panel

- Withhold the paper after a chosen cutoff and verify that Researcher cannot use later decisions or author research during candidate generation.
- Require several mechanism-distinct candidates with assumptions, predictions, falsifiers, feasibility limits, and likely failure modes.
- Verify that absence from a bounded literature search is never reported as proof of novelty.
- Compare the independent Researcher candidates with the revealed paper choice only after the candidate set is frozen.
- Verify that Panel produces each role response under its permitted context before synthesis.
- Require every Panel synthesis claim to trace to at least one frozen role response, with no newly invented finding.
- Test that Panel preserves consequential dissent, distinguishes role-dependent answers from factual conflicts, and does not use majority vote as truth.
- Verify that Panel discloses the limits of same-model role separation rather than claiming independent corroboration merely because roles agree.

#### Isolation and comparative value

- Verify that Reviewer and Researcher cannot reproduce `[AW]` or `[AS]` information available only to Author.
- Register papers sharing an author, terminology, or source URL and test for cross-alias leakage.
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

## P2: Add Teacher and Implementer After the Core Roles Stabilize

Teacher and Implementer are useful extensions, but they should not expand the P0–P1 scope before the existing roles are evidence-safe and behaviorally evaluated.

### Teacher

Teacher should receive the shared paper model but no author research. It should calibrate to the learner's goal and prior knowledge, lead with motivation and intuition, use a small example before formalism, ask the learner to predict an outcome, test boundaries with counterexamples, and use teach-back before claiming understanding. It must distinguish a fluent explanation from demonstrated learner mastery.

### Implementer

Implementer should make reproduction status explicit by separating:

- what the paper specifies;
- what official code or artifacts implement;
- what must be inferred;
- what defaults PaperTalk chooses;
- what was actually executed and observed.

Its output should include a paper-to-code map, an assumption and ambiguity ledger, the smallest useful reproduction path, environment and data requirements, expected versus observed results, deviations, and one of three bounded outcomes: reproduced, failed, or inconclusive. It must never claim reproduction when no implementation was run.

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
- editorial acceptance or rejection decisions inside the default Reviewer role;
- a full multi-reviewer simulation for every casual question;
- forced Devil's-advocate criticism or synthetic praise;
- majority voting or confidence averaging as a substitute for Panel evidence;
- claims that same-model role separation creates genuinely independent evidence;
- claims of learner mastery without demonstrated understanding;
- claims of successful reproduction when no implementation was executed.

A limited research-communication signature may help Author responses feel natural, but it should describe professional explanatory habits rather than attempt identity imitation.

## Suggested Delivery Sequence

### Milestone 1: Evidence and Reviewer foundation

- add source and claim schemas
- add the review-finding schema and evidence-availability states
- add owner-aware validators
- convert the existing TCAB distillate into the structured representation
- test claim-to-source and role-boundary failures
- enforce unpublished-manuscript authorization and venue-policy checks

### Milestone 2: Native distillation pipeline

- implement research tiers
- implement candidate-claim filtering
- add coverage, contradiction, and stopping reports
- add the research-quality checkpoint

### Milestone 3: Composite and Reviewer calibration

- implement decision-level contribution records
- add multi-author fixtures covering different ordering conventions
- add ordering-ablation and author-ablation tests
- implement Reviewer scope, neutral claim mapping, task lenses, severity, and proportional actions
- test partial evidence, positive and negative findings, and re-review behavior

### Milestone 4: Paper-blind Researcher and traceable Panel

- implement cutoff-frozen Researcher candidate generation
- add assumptions, predictions, falsifiers, and comparison records
- generate and freeze role-isolated Panel responses before synthesis
- add traceable agreement, dissent, and unresolved-disagreement handling

### Milestone 5: Behavioral evaluation and versioning

- add reconstruction, uncertainty, conversational, leakage, and baseline tests
- add Reviewer calibration plus Researcher and Panel independence tests
- store repeatable evaluation results
- gate promotion of new distillate versions on regression results
- add correction, promotion, rejection, rollback, and audit history

### Milestone 6: P2 retrieval, adapters, and future roles

- add lazy retrieval indexes
- define and test the external-distillation adapter contract
- add Teacher and Implementer only after the P0–P1 gates pass

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
10. Reviewer findings apply the same evidence standard to strengths and concerns, calibrate severity to central-claim impact, and request proportionate action.
11. Missing or partial evidence produces explicit availability states, bounded conclusions, and adjusted confidence rather than invented defects.
12. Researcher candidates are generated without hindsight, expose assumptions and falsifiers, and remain distinct from located evidence and the paper's actual choice.
13. Panel synthesis is traceable to frozen role outputs, preserves material dissent, and never treats vote count or same-model agreement as truth.
14. Unpublished manuscripts respect authorization, confidentiality, external-service, retention, and venue-policy constraints.
