# PaperTalk Implementation Stage Report

Status date: 2026-09-04

## Current stage

P0 is implemented. PaperTalk now has an executable evidence contract around its conversational skill instructions: new paper namespaces receive owned machine-readable artifacts, author research is filtered and coverage-aware, Composite Author decisions are traceable, Reviewer assessment has a calibrated contract, and a deterministic helper controls which persisted paths each role may load. The registry also supports exact, recoverable paper removal and collision-safe restoration. Post-P0 refinements add a bilingual conversational pass, an Author speaker-authenticity gate, owned interactive Panel continuation over the latest Panel for each paper, and a fixed state-free help catalog.

The implementation deliberately does not claim that schema validation proves a research interpretation is true. It proves ownership, provenance structure, reference integrity, evidence requirements, role access, and readiness; truth and behavioral quality still require the P1 evaluations.

## P0 implemented

| P0 requirement | Implementation | Status |
|---|---|---|
| Machine-readable evidence | Owned source and claim JSONL ledgers, per-author JSON, research status, Composite Author JSON, validation report, Reviewer scope, and Reviewer findings | Complete |
| Namespace initialization | `paper_registry.py add` creates the P0 scaffold for every new paper without changing registry identity behavior | Complete |
| Deterministic validation | `paper_artifacts.py validate` fails on owner mismatches, dangling or cross-author references, insufficient evidence, untraceable composite claims, omitted-claim use, shared-model author evidence, malformed Reviewer findings, and unpublished external-processing violations | Complete |
| Role-safe loading | `paper_artifacts.py context` returns allowed paths for Author, Reviewer, or Researcher; Author requires a ready validated composite, while non-Author roles never receive author-research paths | Complete |
| Paper-specific claim filter | Every candidate records recurrence, target relevance, predictive value, and specificity with rationale; classification is `durable`, `decision-heuristic`, `paper-specific-explicit`, or `omit` | Complete |
| Claim evidence discipline | `[E]` claims require direct sources and locations; `[I]` and `[H]` claims require supporting evidence and rationale; counterevidence and alternatives are retained | Complete |
| Research depth and stopping | Quick, Standard, and Deep tiers, breadth-first author coverage, gaps, quality checkpoint, and evidence-based stopping reason are represented and validated | Complete |
| Composite Author synthesis | Composite claims trace to accepted individual claims; major decisions record candidate explanations, direct contribution evidence, overlapping authorship priors, supporting and contradicting weights, ordering effects, and uncertainty | Complete |
| Calibrated Reviewer | Reviewer scope, neutral orientation, task lenses, evidence-availability states, symmetric strength/concern records, consequence-based severity, proportional remedies, and re-review behavior are specified | Complete |
| Reviewer boundary and confidentiality | Reviewer cannot persist editorial recommendations; unpublished external processing requires authorization, venue-policy confirmation, and retention-policy confirmation | Complete |
| Concise role voice | Existing one-to-three-paragraph conversational response policy remains in place; the richer contract is internal unless details are requested | Preserved |
| Alias isolation | Every new record carries `(alias, paper_id)` and the validator resolves one namespace before checking or authorizing access | Preserved and strengthened |
| Safe registry removal | Explicit alias plus exact `paper_id` guard, full-namespace trash archive, transaction journal, active-pointer clearing without replacement selection, collision-safe restore, and retained audit record | Complete |

## Post-P0 response-policy refinement

### 1. Lightweight conversational pass

Paper-analysis answers now receive one silent conversational edit after their evidence-grounded content is complete. The pass follows the user's current language, removes empty or repetitive framing, and softly reduces formulaic Chinese and English binary contrasts while retaining contrasts needed for scientific meaning or factual accuracy.

The pass is expression-only. Evidence, uncertainty, role voice, role-local access, requested technical depth, equations, quotations, scope markers, and evidence footers take precedence and cannot be rewritten away. Panel members are edited separately after their role-local responses are frozen. The implementation is instruction-based: it adds no blacklist, regex rewriter, external Humanizer dependency, persistent state, or schema migration.

The entry point routes analytical responses to `skills/papertalk/references/conversational-style.md`, which contains the editing priority, bilingual examples, exception criteria, and final role check.

### 2. Author speaker authenticity

Author bodies now use `I` or `we` for self-reference and must sound like something the author could plausibly say to a research colleague. Natural technical subjects remain allowed, while public-record research, Composite Author construction, author synthesis, evidence classification, confidence scoring, and reconstruction mechanics stay outside the role dialogue. Their epistemic status remains visible through the existing generic evidence footer.

The final conversational pass now includes a speaker-authenticity gate. It recasts, moves, or removes analyst narration instead of mechanically prefixing sentences with “we think.” Explicit questions about PaperTalk provenance receive a separately labeled `PaperTalk note`. The change adds no runtime rewriter, schema migration, or registry update, so existing papers do not need re-registration.

### 3. Interactive Panel continuation

`$papertalk panel` now persists independently generated initial role responses. `$papertalk panel_continue @alias responder:target [guidance]` continues only that paper's latest Panel with one targeted response; no Panel ID is exposed. Starting another Panel archives the previous latest Panel as read-only history.

`panel_sessions.py` stores the latest Panel and history in one atomically written, owner-bound document. It validates frozen turn hashes and response links, delegates every role context to `paper_artifacts.py`, marks peer turns as claims rather than evidence, and uses context tokens to reject stale continuations. Moderator synthesis remains deferred.

### 4. Fixed help catalog

`$papertalk help` returns a checked-in English Markdown memo verbatim. The catalog lists every public registry function, perspective, Panel operation, and task modifier with a concrete invocation and one-sentence explanation; it deliberately excludes internal maintenance helpers. Other languages are used only for generated paper-analysis responses when the user writes in or explicitly requests that language, and they are never persisted as documentation variants.

`papertalk_help.py` only reads `references/help-output.md`, so help output is independent of the registry, active paper, paper artifacts, Panel state, and model phrasing. A byte-for-byte test prevents accidental runtime variation.

## P0 files

### Skill entry point and routing

- `skills/papertalk/SKILL.md` routes persisted state through the context helper and marks P0 versus future stages.
- `skills/papertalk/references/evidence-and-models.md` connects epistemic labels to executable evidence checks.
- `skills/papertalk/references/author-research.md` defines research tiers, stopping, the four-gate filter, and validated Composite Author loading.
- `skills/papertalk/references/perspectives.md` routes Reviewer work to its detailed contract.
- `skills/papertalk/references/registry-and-isolation.md` documents the new namespace and helper commands.

### New P0 resources

- `skills/papertalk/references/artifact-contract.md` defines the artifact layout and record formats.
- `skills/papertalk/references/reviewer.md` defines Reviewer scope, lenses, evidence states, findings, severity, remedies, confidentiality, and voice.
- `skills/papertalk/scripts/paper_artifacts.py` scaffolds, validates, and authorizes role-specific contexts using only the Python standard library.
- `skills/papertalk/tests/test_paper_artifacts.py` tests the P0 contract and failure modes.

### Interactive Panel resources

- `skills/papertalk/references/panel-sessions.md` defines the latest-Panel grammar, orchestration, role boundary, state, and failure behavior.
- `skills/papertalk/scripts/panel_sessions.py` atomically manages the latest Panel, read-only history, isolated initial contexts, and targeted continuation.
- `skills/papertalk/tests/test_panel_sessions.py` covers ownership, isolation, target resolution, stale state, tampering, and registry recovery.

### Help resources

- `skills/papertalk/references/help-output.md` is the canonical fixed public command catalog.
- `skills/papertalk/scripts/papertalk_help.py` prints the memo verbatim without reading state.
- `skills/papertalk/tests/test_papertalk_help.py` checks completeness, byte stability, and state-free execution.

### Updated registry

- `skills/papertalk/scripts/paper_registry.py` gives every newly registered paper the P0 artifact scaffold and an owner-bearing shared-paper Markdown file. It also implements `remove`, `removed`, and `restore` with exact-target guards and rollback protection.

## Existing `@tcab` migration

The ignored local runtime namespace `.papertalk/papers/tcab` was migrated non-destructively:

- 5 owned source records;
- 5 filtered and included author-mindset claims;
- 1 independently represented author;
- 2 explicit decision-level Composite Author records;
- valid Author and Reviewer context checks.

The migration is recorded as Quick-tier `ready-with-gaps`. It explicitly notes that no public talk, interview, rebuttal, code history, or project-history account of the idea's origin was located in that pass. The `.papertalk` directory remains excluded from Git so personal runtime paper state is not committed with the reusable skill.

## Validation completed

- Skill package validation: passed with `quick_validate.py` using an isolated PyYAML install under `/tmp`.
- Automated tests: 37 passed, including 12 Panel session tests and 3 fixed-help tests.
- Python syntax compilation: passed with bytecode redirected to a temporary directory.
- Git whitespace validation: passed with `git diff --check`.
- Live `@tcab` artifact validation: passed with 5 sources, 5 included claims, 1 individual author, 2 composite decisions, and the documented coverage warning.
- Live role checks: Author context allowed only after readiness; Reviewer context excludes the full author-research directory.
- Independent temporary-workspace forward test: latest-Author targeting, peer isolation, claim-only projection, guidance preservation, role-safe paths, append, and no-ID continuation all passed.

## P1 future work

### Paper-blind Researcher

- Freeze an explicit paper cutoff before ideation.
- Generate several mechanism-distinct candidates before exposing later sections, author research, or the paper's actual choice.
- Record assumptions, predictions, falsifiers, feasibility, failure modes, value under null results, and discriminating evidence.
- Separate ideas, located evidence, and decisions; preserve minority and rejected candidates.
- Compare with the paper's actual choice only after the independent candidate set is frozen.
- Treat literature search as bounded evidence, never as proof of novelty.

### Remaining Panel synthesis work

- Trace every synthesis statement to one or more frozen outputs.
- Preserve consequential dissent and distinguish corroboration, value tension, error detection, role-dependent answers, and unresolved disagreement.
- Avoid majority voting and disclose that same-model role separation is not genuinely independent evidence.

### Behavioral and safety evaluation

- Add realistic answer-level tests for reconstruction fidelity, uncertainty, author-order sensitivity, partial-paper review, Reviewer severity and proportionality, Researcher hindsight resistance, Panel provenance, cross-alias leakage, and concise role voice.
- Compare with-skill behavior against a shared-paper-only baseline.
- Use independent evaluators where practical and record model, prompt, artifact version, rationale, token use, and runtime.
- Gate changes on regressions rather than validating only schemas and command behavior.

### Versioning and corrections

- Add draft, candidate, active, rejected, corrected, promoted, and rollback states.
- Preserve source, claim, author-identity, authorship-prior, composite-decision, and validation changes in an audit history.
- Prevent silent overwrites of active distillates.

## P2 future work

### Lazy retrieval and adapters

- Load only task-relevant shared decisions, author claims, Composite Author decisions, and compact uncertainty metadata after resolving `(alias, paper_id, role)`.
- Add paper-owned retrieval indexes without introducing cross-paper semantic caches.
- Define an adapter for maintained external distillation tools while preserving PaperTalk's owner, provenance, filtering, access, and uncertainty contract.
- Keep a native fallback so the skill has no hard dependency on a particular external distillation service.

### Teacher

- Calibrate to learner goals and prerequisites.
- Lead with motivation and intuition, then examples, predictions, formalism, counterexamples, and teach-back.
- Do not claim learner mastery without demonstrated understanding.
- Use the shared paper model only, never author research.

### Implementer

- Separate what the paper specifies, official code implements, PaperTalk infers, PaperTalk chooses as a default, and an actual run observes.
- Add a paper-to-code map, ambiguity ledger, minimal reproduction path, environment and data requirements, expected-versus-observed results, deviations, and a reproduced/failed/inconclusive verdict.
- Never claim reproduction when nothing was executed.

## Later or currently unscheduled

- A separate Editor role for venue-level recommendations or adjudication.
- Field/Historian perspective.
- Cross-paper comparison through independently verified read-only snapshots.
- Targeted alias replacement.
- Permanent removal-archive purging and retention policies.
- Remote-content fingerprint refresh.
- Persistent embeddings, reusable answer caches, and saved comparison workspaces.

## Current known limits

- Validation checks artifact structure, provenance links, and access boundaries; it cannot mechanically establish that a source was interpreted correctly.
- Shared-model leakage detection rejects explicit `[AW]` and `[AS]` markers. The role-context helper is the primary deterministic access boundary; semantic leakage testing remains P1.
- Quick-tier readiness may include documented gaps. Standard and Deep require an accepted research-quality checkpoint.
- Reviewer findings are supported, but multi-reviewer simulation and editorial decisions are intentionally absent.
- Researcher remains instruction-level pending P1 execution machinery. Panel has deterministic initial-turn and targeted-continuation state, while moderator synthesis and answer-level behavioral evaluation remain future work.
- The conversational pass is instruction-based; automated answer-level regression scoring remains part of the P1 behavioral evaluation work.
- Removed papers are recoverable only while their PaperTalk trash archive is retained; permanent purge is intentionally unavailable.
