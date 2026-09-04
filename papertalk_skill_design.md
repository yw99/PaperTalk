# PaperTalk Skill — Design & Implementation Note

## Executive Summary

**PaperTalk** is an evidence-grounded paper-reading skill designed to explain the research reasoning behind a paper—not just summarize its contents. It builds a shared model of each paper's facts, notation, assumptions, claims, theorems, and experiments for every perspective. Separately, it distills each coauthor's relevant public research record and synthesizes the individual distillates into one evidence-grounded **Composite Author** model used only by the Author perspective. The synthesis uses authorship ordering as a calibrated, decision-specific prior: first and co-first authors usually receive more influence, especially for execution-facing choices, but may also be central to topic selection, motivation, and project conception. Explicitly identified corresponding authors receive an additional direction-facing prior without excluding first authors from those decisions.

The default Author perspective combines the shared paper model with the Composite Author model to reconstruct the path from goal and obstacle to design choice and consequence. It clearly separates what sources state **[E]**, what the evidence strongly supports **[I]**, and what is only a plausible reconstruction **[H]**. Reviewer, Researcher, Teacher, Implementer, and Field perspectives receive the shared paper model but never the author distillates or composite mindset. This prevents both invented author intent and cross-role contamination while still answering the central question: *Why did the paper have to look this way?*

The default interaction is concise and conversational. Author speaks in first person (`I` for a single author and `we` for a multi-author Composite Author), while Reviewer speaks as an independent `I` and may discuss strengths as well as concerns. Researcher is the only role that may retain a third-person analytical style. Ordinary answers use one to three short paragraphs and a compact evidence footer; technical detail is deferred until the user requests it.

PaperTalk supports natural-language questions, compact `$papertalk` commands, active-paper context, and a registry of multiple papers with strict alias isolation. Every paper-derived artifact—including working memory, author research, retrieval indexes, and caches—belongs to exactly one paper namespace. It should reuse maintained distillation skills where available through a stable adapter, while keeping a small native fallback and preserving source provenance. Development is staged: validate per-author distillation, Composite Author synthesis, core alias isolation, and the Author–Reviewer–Researcher experience first; then add advanced comparisons, persistence, specialized perspectives, distribution assets, and only later optional integrations or a plugin wrapper.

Its defining experience is a three-way research conversation:

```text
Author: Why this choice?
Reviewer: Does it hold?
Researcher: What else could work?
```

---

## 1. Goal

Build a reusable **paper-reading skill** that helps users understand research papers by reconstructing the **research reasoning behind the paper**, rather than merely summarizing the text.

The primary interaction should be centered on an **evidence-grounded composite author mindset**:

> Do not only explain *what the paper says*. Reconstruct *why the paper had to look this way*.

The skill should also support optional alternative perspectives such as:

- Reviewer
- Researcher / Inventor
- Teacher
- Implementer
- Field / Historian
- Multi-perspective Panel

The core design principle is:

```text
Target-paper evidence ───────────────→ Shared paper model
                                              │
                                              ├─→ Reviewer / Researcher
                                              ├─→ Teacher / Implementer / Field
                                              └─→ Panel non-Author sections

Relevant public evidence for each author
    ↓
Individual author distillates
    ↓
Composite Author model ──┐
                         ├─→ Author perspective
Shared paper model ──────┘
```

All perspectives should **share the same underlying paper facts**. Only the Author perspective may additionally access the individual author distillates and Composite Author model. In a Panel, each section must be evaluated with its own allowed context so that author-derived information does not leak into the other roles.

---

# 2. Primary Product Idea

A normal paper-reading assistant usually does:

```text
Paper
  ↓
Problem
Method
Theorem
Experiments
Results
Limitations
```

PaperTalk should instead reconstruct:

```text
Paper
  ↓
Explicit evidence + inferred reasoning
  ↓
Research reasoning model
  ↓
Why this problem?
Why this formulation?
Why this assumption?
Why this method?
Why this theorem?
Why this experiment?
Why not an alternative?
```

The most important user question is often not:

> What does Eq. (7) mean?

but:

> Why would the authors ever formulate Eq. (7) in the first place?

This skill should explicitly optimize for the second kind of understanding.

---

# 3. Canonical Skill Name

Recommended name:

```text
papertalk
```

Canonical Codex invocation:

```text
$papertalk ...
```

For ChatGPT Project usage, a lightweight convention can be:

```text
/paper ...
```

The `/paper` syntax does not need to be a real slash command; it can simply be a protocol defined in Project instructions.

---

# 4. Interaction Grammar

Recommended syntax:

```text
$papertalk [perspective] [@paper] [task] <question>
```

All parts except the question are optional.

Examples:

```text
$papertalk author @opd why Why do they introduce r?
```

```text
$papertalk reviewer @opd critique Is Assumption 4 really necessary?
```

```text
$papertalk researcher @sapo extend Stop after Section 3. What would you try next?
```

```text
$papertalk teacher @gate explain Why does the e-value appear here?
```

```text
$papertalk implementer @opd trace How is rho actually computed?
```

```text
$papertalk panel @opd Is Theorem 2 actually interesting?
```

The syntax should be treated as a **convenience grammar, not a rigid parser**.

Natural-language equivalents must also work:

```text
$papertalk From a reviewer perspective, is their KL guarantee actually meaningful?
```

```text
$papertalk Give me an author/reviewer panel on Eq. 5.
```

```text
$papertalk I still do not buy why they need r. First explain the authors' logic, then tell me whether a reviewer should accept it.
```

---

# 5. Defaults

If no paper is explicitly specified:

```text
paper = active_paper
```

If no perspective is explicitly specified:

```text
perspective = author
```

If no task is explicitly specified:

```text
task = infer from user intent
```

So:

```text
$papertalk Why do they introduce rho?
```

means approximately:

```text
paper = active_paper
perspective = author
task = why
```

---

# 6. Perspective vs Task

Do **not** mix roles and tasks into one flat list.

There are two orthogonal axes.

## 6.1 Perspective

Supported perspectives:

```text
author
reviewer
researcher
teacher
implementer
field
panel
```

## 6.2 Task

Suggested task verbs:

```text
explain
why
derive
critique
compare
trace
summarize
extend
attack
```

Examples:

```text
author + derive
teacher + derive
reviewer + critique
researcher + extend
implementer + trace
field + compare
```

The same mathematical object may therefore be explored differently:

```text
$papertalk author derive Eq. 7
```

means:

> Explain the conceptual path that motivates Eq. 7, then derive it.

Whereas:

```text
$papertalk teacher derive Eq. 7
```

means:

> Diagnose the reader's missing prerequisites and derive Eq. 7 pedagogically.

And:

```text
$papertalk reviewer derive Eq. 7
```

means:

> Check the derivation and identify hidden assumptions or unjustified steps.

---

# 7. Perspective Definitions

## 7.1 Author — Default Composite Perspective

The Author perspective is the core identity of the skill.

Most papers have multiple authors. Do **not** assume the first or senior author alone represents the group, treat the author list as a homogeneous voice, or confuse a first-person role voice with literal testimony about a private research process.

Instead:

> Distill each author's relevant research mindset, combine those distillates into a contribution-aware Composite Author, and use that representative together with the shared paper model to reconstruct the strongest evidence-grounded account of the research reasoning that could have produced the paper.

Deliver that reconstruction as a direct conversation. Use `I` for a single-author paper and `we` for a multi-author Composite Author. Explicit evidence may be stated directly in this voice; inferred or hypothetical intent must be hedged naturally with “My best reconstruction is...” for one author or “Our best reconstruction is...” for several. Default to one to three short, high-level paragraphs and expand only when the user asks for technical detail.

Focus on:

- What problem are the authors trying to solve?
- Why does this problem matter?
- What is the starting point?
- What obstacle prevents a simpler solution?
- Why is this formulation introduced?
- Why is this assumption useful?
- Why this mathematical object?
- Why this theorem?
- Why this experiment?
- What alternative choices were available?
- What downstream result depends on the choice?

The preferred explanatory pattern is:

```text
Goal
  ↓
Obstacle
  ↓
Desired property
  ↓
Design choice
  ↓
Mathematical consequence
  ↓
Theorem / experiment
```

For example, do not only say:

> r is an auxiliary distribution.

Instead try to explain:

```text
We want a better policy
    ↓
directly optimizing the deployed policy entangles selection and optimization
    ↓
we want an ideal intermediate target
    ↓
introduce r
    ↓
policy learning becomes a projection / fitting problem
```

Never claim reconstructed reasoning was literally the historical reasoning of the authors unless the paper explicitly says so.

### 7.1.1 Per-Author Distillation

Create a separate distillate for every named author before constructing the composite. Each distillate should focus on research-relevant signals such as:

- recurring research questions and problem framings
- methodological preferences and recurring technical tools
- favored assumptions, abstractions, and evaluation standards
- characteristic ways of motivating contributions
- recurring tradeoffs, limitations, and failure modes
- changes in research direction over time
- evidence about the author's contribution to the paper, when explicitly available
- connections between the author's prior work and decisions in the target paper

Search broadly enough to capture the author's relevant scholarly trajectory, but retain only public professional or research information that can improve the reconstruction. Do not collect private, sensitive, personal, or merely biographical details, and do not infer research mindset from prestige, affiliation, demographics, or personality stereotypes. Author order may inform the contribution prior defined below, but is not direct evidence that a particular person supplied an idea.

Prefer sources in roughly this order:

1. the target paper and its supplements, appendices, code, and author statements
2. the author's related papers, especially work close in topic and time
3. public talks, interviews, lectures, technical blogs, and project pages
4. public scholarly profiles and other professional sources useful for discovery

Coverage should be relevance-driven rather than an exhaustive crawl of everything ever published about an author. Record the searched scope and important gaps so that sparse evidence is not mistaken for absence of a tendency.

For large author lists, use a breadth-first pass across every author before deepening any one profile. Then deepen the authors whose evidence is most relevant, ambiguous, or potentially explanatory for the target paper. Never silently omit an author because another author has a larger public footprint; expose per-author coverage and any resource-driven limits.

### 7.1.2 Distillation-Skill Reuse

Treat author and paper distillation as a replaceable capability with a stable input/output contract.

When the runtime provides a suitable maintained distillation skill, prefer invoking it and normalize its output into PaperTalk's schema. Keep a small native fallback so PaperTalk remains usable without optional dependencies. If implementation later vendors or adapts material from another skill, copy only the necessary parts, verify that reuse is permitted, retain attribution and license information, record the source version, and adapt the material to PaperTalk's evidence and access-control rules.

Do not make the core skill depend on the name or private implementation of a distillation skill that may not exist in another runtime.

Suggested contract:

```yaml
distillation_request:
  subject: target_paper | author
  sources: []
  focus: research_mindset
  target_paper_context:

distillation_result:
  claims:
    - statement:
      source:
      source_type:
      evidence_level:
      relevance_to_target_paper:
  coverage:
  conflicts:
  unknowns:
```

### 7.1.3 Composite Author Synthesis

The Composite Author is a paper-specific representative of the collaboration's research mindset, not a biography, personality profile, literal group consciousness, or simple average of the authors.

Synthesize the individual distillates by:

1. identifying tendencies supported across several authors
2. identifying complementary expertise that explains different parts of the paper
3. preserving meaningful disagreements or alternative interpretations
4. weighting evidence by relevance to the target paper, recency, source quality, explicit contribution evidence, and the authorship-role prior
5. connecting composite claims back to both the target paper and the contributing author distillates

Use a **decision-specific contribution prior**, not one global weight per author:

1. **Direct contribution evidence dominates.** Apply explicit contribution statements, CRediT roles, author interviews, project documentation, and clearly attributable artifacts before ordering heuristics.
2. **First and explicitly co-first authors receive the strongest general default prior, especially for execution-facing decisions.** This includes technical conception, method development, derivations, experiments, implementation, and drafting. They may also have originated or strongly shaped the topic, motivation, problem framing, and project conception; never exclude that possibility. Equal-contribution markers give each named co-first author the same prior.
3. **Explicitly identified corresponding authors receive an additional strong prior for direction-facing decisions.** This includes topic selection, problem framing, motivation, project conception, coordination, and research direction. This prior is not exclusive and must not suppress first/co-first author influence when their record or direct evidence supports it. Corresponding status does not by itself prove that someone was an advisor; advising or supervision requires separate evidence.
4. **Last-author or senior-author position is field-dependent.** Use it as a project-direction prior only when the field's convention or explicit evidence supports that interpretation. Do not assume the last author is corresponding or supervisory from position alone.
5. **Other authors retain a nonzero neutral prior.** Direct contribution evidence or a highly relevant research record may outweigh positional priors for a particular decision.

Authorship-role priors may overlap. For a mixed decision, both first/co-first and corresponding authors can receive strong influence, with direct evidence determining the final balance.

Before applying ordering, classify the paper's convention as contribution-ordered, alphabetical, mixed, or unknown. Disable the first-author prior for clearly alphabetical lists, and weaken all order-based priors for consortia, very large collaborations, and unknown conventions. Identify corresponding authors only from explicit paper marks or reliable metadata.

Then weight the underlying evidence by target-paper relevance, source quality, recency, and consistency. Preserve conflict instead of forcing consensus. The authorship position itself is `[E][P]`; a contribution inferred from position is normally `[H]` unless corroborating evidence supports `[I]`.

Every composite claim should disclose when authorship ordering materially affected the synthesis.

The resulting representative should answer:

```text
Given this paper and the relevant research records of all its authors,
what collective research logic best explains the paper's choices?
```

### 7.1.4 Hard Role Boundary

The individual author distillates and Composite Author model are privileged inputs for the Author perspective only.

- **Author** receives the shared paper model plus the Composite Author model and may inspect individual distillates when needed.
- **Reviewer, Researcher, Teacher, Implementer, and Field** start from the shared paper model. They may use role-appropriate sources when their task genuinely requires them—for example, related literature for novelty review—but must not load, cite, or silently use author-distillation sources, author profiles, or the Composite Author model.
- **Panel** runs each requested role in an isolated context. Its Author section may use the Composite Author model; every other section must use only the shared paper model and sources independently permitted for that role.

Information explicitly contained in the target paper remains part of the shared paper model even when it is an author statement. The boundary applies to extra-paper author research and all mindset information derived from it.

### 7.1.5 Author Perspective Workflow

```text
Resolve and distill the target paper
    ↓
Verify the complete author list and disambiguate identities
    ↓
Collect relevant public research sources for every author
    ↓
Produce one independent, provenance-rich distillate per author
    ↓
Synthesize the paper-specific Composite Author
    ↓
Combine Composite Author + Shared Paper Model
    ↓
Answer with calibrated evidence and uncertainty
```

Keep the individual distillation step independent so the emerging composite does not bias what is extracted from later authors. Rebuild or refresh the composite when an individual distillate materially changes.

---

## 7.2 Reviewer

Purpose:

> Give an independent, evidence-driven evaluation of what the paper does well, what could be improved, and how much those points matter.

Reviewer speaks as `I` in direct conversation with the user. It may appreciate a convincing argument, elegant construction, important contribution, clear experiment, or well-scoped limitation just as readily as it may raise a concern. Do not invent praise or criticism to manufacture balance, and do not default to fault-finding.

Questions to ask:

- Is this choice really necessary?
- Is the claimed novelty actually novel?
- Is a simpler baseline sufficient?
- Is the formulation stronger than what the theorem requires?
- Is an assumption doing hidden heavy lifting?
- Does the theorem support the stated motivation?
- Do the experiments distinguish the claimed mechanism from alternatives?
- Are important baselines missing?
- Is the contribution conceptual, technical, empirical, or mostly packaging?
- Are there gaps between theory and implementation?
- Are conclusions stronger than the evidence?

Reviewer mode should be discriminating rather than reflexively skeptical. Default to one to three short, high-level paragraphs, and provide technical detail only when requested or when the task is explicitly technical.

---

## 7.3 Researcher / Inventor

Purpose:

> Reconstruct the problem-solving process as if the rest of the paper were not known.

Researcher is the only role that may retain a third-person analytical or conventionally structured explanatory style. It still defaults to a concise, high-level response and expands only when the user asks for technical depth.

Useful commands:

```text
Stop after Eq. 4. What would you try next?
```

```text
Pretend Section 5 does not exist. What are the plausible next approaches?
```

Expected output:

- plausible next directions
- advantages and drawbacks of each
- what evidence would distinguish them
- which direction the actual paper chose
- why that direction may have been attractive

This mode is especially important for active learning and for helping the user "rediscover" the paper.

---

## 7.4 Teacher

Purpose:

> Diagnose what conceptual layer the reader is missing and explain from that layer.

Do not simply repeat the same derivation more slowly.

Instead identify the missing prerequisite.

Example:

```text
constrained optimization over distributions
    ↓
KL-regularized projection
    ↓
Lagrangian
    ↓
pointwise density-ratio optimization
    ↓
exponential tilting
```

The Teacher should determine where the reader is stuck and explain from there.

---

## 7.5 Implementer

Purpose:

> Translate theory into actual implementation requirements.

Focus on:

- what is computed exactly
- what is estimated
- what needs samples
- what needs a neural network
- which quantities are unavailable in practice
- what is differentiated through
- what uses stop-gradient
- what happens per token / step / trajectory / batch
- normalization constants
- sampling procedures
- numerical stability
- hidden engineering assumptions
- mismatches between theory and code
- ambiguity in pseudocode

Typical question:

```text
How would I actually implement Algorithm 1?
```

---

## 7.6 Field / Historian

Purpose:

> Place the paper in the broader research lineage.

Focus on:

- what prior problem this paper inherits
- what unresolved tension motivates it
- which earlier methods it combines or departs from
- what conceptual shift it represents
- whether the contribution is incremental or directional
- how it differs from closely related approaches

This mode may require external literature search if tools are available.

---

## 7.7 Panel

Panel is a multi-perspective answer over the **same underlying paper model**, with role-specific context isolation.

The Author section may additionally use the Composite Author model. Non-Author sections must be generated without that model or any individual author distillates. Do not generate one blended analysis and relabel fragments as different roles.

Default panel:

```text
Author
Reviewer
Researcher
```

This is the core triangle:

```text
             Author
          Why we did it
           /         \
          /           \
   Reviewer  ←────  Researcher
 Does it hold?       What else?
```

Example:

```text
$papertalk panel @opd Is Theorem 2 really interesting?
```

Possible output structure:

```text
AUTHOR
...

REVIEWER
...

RESEARCHER
...
```

The user should also be able to request a custom panel:

```text
$papertalk panel author reviewer implementer @opd Is Eq. 7 necessary?
```

Use exactly the requested perspectives when explicitly specified.

Keep each voice distinct in the assembled response: Author uses `I` or `we`, Reviewer uses `I`, and Researcher remains third-person. Normally give each member one short paragraph plus a shared compact evidence footer.

---

# 8. Evidence / Epistemic Protocol

This is critical.

The assistant must not casually invent author intent or blur claims from different sources.

Use three evidence levels:

```text
[E] Explicit
[I] Inferred
[H] Hypothesized / reconstructed
```

Definitions:

### [E] Explicit
Directly stated in an identified source.

Examples:

- the authors explicitly motivate a design choice
- the paper explicitly defines a symbol
- a theorem explicitly states a bound
- an experiment explicitly reports a result
- an author explicitly describes a research preference in a public talk

### [I] Inferred
Strongly supported by paper structure, equations, proofs, experiments, related work, or public research statements.

Example:

> The reverse KL choice appears to be important for obtaining the exponential-tilt form.

### [H] Hypothesized
A plausible researcher-level reconstruction, but not supported strongly enough to attribute to the authors.

Example:

> A plausible development path is that the authors first considered direct policy optimization, then introduced r to separate selection from fitting.

Never present [H] as a documented historical fact.

Avoid language like:

```text
The authors definitely first tried X and failed.
```

unless explicitly documented.

Preferred language:

```text
A plausible reconstruction is...
```

```text
The paper does not state this directly, but...
```

```text
This is strongly suggested by...
```

The skill may use labels visibly when ambiguity matters, but does not need to clutter every simple answer.

Evidence level and source origin are separate dimensions. Internally, provenance should also identify where a claim came from:

```text
[P]  target paper or its official artifacts
[AW] another scholarly work by an author
[AS] public professional statement by an author
[D]  discovery-only metadata or profile
```

An `[E][AS]` claim is explicit in a public author statement but not explicit in the target paper. It may inform the Composite Author model, but it must not enter non-Author perspectives. Discovery-only sources may locate stronger evidence but should rarely support mindset claims by themselves.

Every author-derived claim should retain its author, source, date, evidence level, source origin, and relevance to the target paper. Claims synthesized across authors should also record which individual distillates support or contradict them.

---

# 9. Two-Model Architecture and Access Boundaries

All perspectives must operate on the same shared paper representation.

Do not let each role independently "reread" and invent its own version of the paper.

Conceptual structure:

```text
TARGET-PAPER LAYER — shared by every role

Target paper and official artifacts
                │
                ▼
       Shared Paper Model
 facts / notation / assumptions / claims
 theorems / experiments / paper statements
                │
       ┌────────┼───────────────┐
       ▼        ▼               ▼
  Reviewer   Researcher   Teacher / Implementer / Field
       │
       └──────────────────────────────→ Panel non-Author sections

AUTHOR-RESEARCH LAYER — private to Author perspective

Author A sources ─→ distillate A ─┐
Author B sources ─→ distillate B ─┼─→ Composite Author Model
Author C sources ─→ distillate C ─┘            │
                                                 │
Shared Paper Model ──────────────────────────────┼─→ Author
                                                 └─→ Panel Author section only
```

Role changes:

```text
interpretation objective
```

Role does **not** change:

```text
facts
notation
paper claims
theorem statements
experimental evidence
```

Role changes do not automatically grant access to additional source classes. The router must construct the allowed context before answering, rather than relying on a prompt reminder after all data has already been loaded.

Role-appropriate retrieval can still occur after this boundary is applied. For example, Reviewer may inspect a baseline paper and Field may search the literature, but neither may retrieve from the author-research store or use sources selected for profiling an author's mindset.

The shared paper model must not contain fields derived from author profiling. The author-research model may reference facts from the shared paper model, but the dependency is one-way: no synthesized author-mindset claim may be written back into shared state.

---

# 10. Suggested Paper Model Schema

The implementation does not have to literally serialize this exact YAML, but the conceptual fields should exist.

```yaml
paper_model:

  identity:
    title:
    authors:
    year:
    source:
    alias:
    paper_id:
    source_fingerprint:

  central_problem:
    what:
    why_it_matters:
    existing_gap:

  starting_point:
    what_is_available:
    what_is_preserved:
    what_is_missing:

  notation:
    symbol:
      meaning:
      defined_at:
      notes:

  assumptions:
    - id:
      statement:
      role:
      downstream_dependencies:

  design_constraints:
    - constraint:

  key_beliefs:
    - belief:
      evidence_level:
      evidence:

  reasoning_chain:
    - observation:
      consequence:
      design_choice:

  major_decisions:
    - decision:
      motivation:
      alternatives:
      why_this_choice:
      downstream_consequences:
      evidence_level:

  claims:
    - claim:
      evidence:
      assumptions:
      strength:

  theorem_roles:
    theorem_id:
      statement:
      question_it_answers:
      why_needed:
      dependencies:

  experiment_roles:
    experiment_id:
      hypothesis:
      what_doubt_it_addresses:
      outcome:

  implementation_notes:
    - issue:

  likely_alternatives:
    - alternative:
      why_plausible:
      why_not_chosen:
      evidence_level:

  unresolved_questions:
    - question:

```

The author-research model is separate:

```yaml
author_research_model:

  target_paper_alias:
  target_paper_id:

  authors:
    - id:
      name:
      identity_disambiguation:
        evidence:
        confidence:
      authorship_metadata:
        position:
        author_count:
        equal_contribution_group:
        is_corresponding_author:
        corresponding_author_evidence:
        ordering_convention:
        ordering_convention_confidence:
      source_coverage:
        searched:
        included:
        gaps:
      mindset_claims:
        - claim:
          dimension:
          evidence_level:
          source_origin:
          source:
          source_date:
          relevance_to_target_paper:
          counterevidence:
      target_paper_connections:
        - paper_decision:
          possible_connection:
          evidence_level:
      explicit_contribution_evidence:

  composite_author:
    central_research_logic:
    shared_tendencies:
    complementary_expertise:
    unresolved_tensions:
    paper_choice_connections:
    decision_influence:
      - decision:
        decision_type:
        authorship_priors_applied:
        direct_contribution_evidence:
        ordering_effect:
        evidence_level:
    supporting_authors:
    contradicting_authors:
    synthesis_method:
    coverage_limits:
    uncertainty_notes:

  access_policy:
    allowed_perspectives:
      - author
    panel_author_section_only: true
```

---

# 11. Paper Registry

The skill must support multiple papers simultaneously.

Each paper gets an alias:

```text
@opd
@sapo
@gate
```

Commands:

```text
$papertalk add opd <paper source>
```

```text
$papertalk add sapo <paper source>
```

```text
$papertalk list
```

```text
$papertalk use @opd
```

```text
$papertalk remove @opd
```

Suggested registry:

```yaml
active: opd

papers:
  opd:
    source: papers/opd.pdf
    paper_id: sha256:<canonical-paper-fingerprint>
    namespace: papers/opd

  sapo:
    source: https://arxiv.org/abs/2608.19842
    paper_id: sha256:<canonical-paper-fingerprint>
    namespace: papers/sapo

  gate:
    source: https://arxiv.org/abs/2510.10232
    paper_id: sha256:<canonical-paper-fingerprint>
    namespace: papers/gate
```

Aliases must be unique after normalization. `add` must reject an existing alias rather than silently replacing or merging it. Rebinding an alias to another paper requires an explicit replace operation. Build the replacement under its new `paper_id`, then atomically swap the registry entry and invalidate only the old alias-owned derived state; never expose a partially mixed namespace.

`paper_id` identifies the resolved source content independently of its user-facing alias. Every stored record and retrieval operation must carry both the alias namespace and `paper_id`; a mismatch is an error, not a reason to search another paper.

When a paper is added, the skill should either:

1. immediately build a lightweight paper model, or
2. lazily build it when first queried.

Prefer avoiding expensive unnecessary preprocessing. Build author distillates and the Composite Author lazily on the first Author request, or when the user explicitly asks to prepare or refresh author research. A non-Author request must not trigger author profiling as a side effect.

---

# 12. Paper Source Resolution

A paper may be supplied as:

- uploaded PDF
- local PDF / file
- arXiv URL
- DOI / webpage URL
- current conversation attachment
- already active paper

Examples:

```text
$papertalk add opd ./papers/opd.pdf
```

```text
$papertalk add sapo https://arxiv.org/abs/2608.19842
```

```text
$papertalk add gate this paper
```

Use the strongest native capability available in the current runtime.

Do not hard-code Codex-only filesystem behavior into the core reasoning logic.

## 12.1 Author Source Resolution

Author research begins only after the paper's author list has been resolved. Disambiguate each author using evidence from the target paper, affiliation, ORCID or comparable identifiers, research topics, and publication history. Do not merge records for different people who share a name.

Use search, scholarly indexes, institutional pages, publication repositories, public talks, interviews, and author-provided sites according to the capabilities available in the runtime. Since profiles, affiliations, and publication lists can change, verify current public sources when building or refreshing a distillate and store retrieval dates.

The objective is not to summarize each author's entire career. It is to extract evidence relevant to the research mindset expressed by the target paper. Stop when additional sources no longer materially change the high-confidence mindset claims, while documenting important coverage gaps.

---

# 13. Multi-Paper Isolation

This is a critical requirement.

Multiple papers must be treated as separate namespaces.

Never transfer the following across paper namespaces. An explicit comparison may read labeled, read-only copies side by side, but still must not merge or write them across namespaces:

- source documents and extracted passages
- notation
- assumptions
- motivations
- theorem dependencies
- experiment results
- author distillates and Composite Author models
- author-source coverage and contribution evidence
- implementation details
- unresolved questions
- retrieval indexes and embeddings
- cached answers, summaries, and reasoning graphs
- conversation notes, follow-up referents, and unresolved pronouns
- role-specific working context

Strong rule:

```text
Paper is a namespace.
```

Conceptually:

```text
papers
│
├── opd
│   ├── identity
│   │   ├── alias
│   │   ├── paper_id
│   │   └── source_fingerprint
│   ├── paper_model
│   │   ├── evidence
│   │   ├── notation
│   │   ├── claims
│   │   └── reasoning_graph
│   ├── author_research
│   │   ├── individual_distillates
│   │   └── composite_author
│   ├── retrieval_index
│   ├── conversation_state
│   └── derived_cache
│
├── sapo
│   ├── identity
│   ├── paper_model
│   └── author_research
│
└── gate
    └── ...
```

An author may appear in several registered papers. Immutable raw public sources may be content-addressed and deduplicated internally, but they are not directly queryable as paper state. A source must be explicitly attached to a paper namespace before use. All selection, annotations, extracted claims, relevance scoring, author distillates, and Composite Author models remain paper-specific.

Especially isolate notation.

Example:

```yaml
opd:
  rho:
    meaning: incumbent distribution

gate:
  rho:
    meaning: target distribution
```

A question about `@opd` must never borrow the `rho` definition from `@gate`.

## 13.1 Namespace Invariant

Every paper-derived object must have exactly one owner:

```text
owner = (alias, paper_id)
```

Reads and writes require an exact owner match. Do not retrieve globally and filter afterward. Query the resolved namespace directly, and fail closed if the namespace, alias, or `paper_id` is missing or inconsistent.

No derived artifact may use a cache key based only on a symbol, author, theorem number, source URL, or user question. Cache keys should include at least:

```text
alias + paper_id + artifact type + source digest + schema/version
```

Perspective and task must also be included when the cached artifact depends on them.

## 13.2 Conversation Isolation

Paper scope must be resolved before interpreting paper-specific words such as “this,” “their method,” “the theorem,” or `rho`.

- An explicit `@alias` scopes only that request unless the user also runs `use @alias`.
- `use @alias` changes the active pointer but does not copy working memory from the previously active paper.
- Follow-up state, reader questions, provisional explanations, and cached conversational summaries are stored inside the resolved paper namespace.
- After a paper switch, do not use unresolved referents from the prior paper. Ask for clarification if the new request cannot be resolved from the new namespace.
- When no explicit or active paper exists and multiple papers are registered, require clarification. Never choose by semantic similarity.

## 13.3 Shared Authors and Sources

The same person, method, dataset, or cited work may occur in several papers. Shared identity does not imply shared derived meaning.

For example, if the same author appears in `@opd` and `@sapo`, build separate author distillates whose source selection and relevance judgments are conditioned on each target paper. A Composite Author from one alias must never seed or update the other. Reuse is limited to immutable raw source bytes and verified identity metadata; all interpretations must be recomputed or explicitly attached within the target namespace.

## 13.4 Isolation at the Tool Boundary

Any script, vector store, database query, or external distillation adapter must accept the resolved alias and `paper_id` as required inputs and return them with its result. Reject unscoped results. Temporary files and intermediate outputs must also live under an alias-specific directory.

Do not expose a tool operation that searches every registered paper for a normal single-paper question. A cross-paper search is a separate, explicitly invoked comparison operation.

---

# 14. Active Paper

The registry should contain:

```text
active_paper
```

Example:

```text
$papertalk use @opd
```

After that:

```text
$papertalk Why introduce r?
```

means:

```text
paper = @opd
perspective = author
```

Explicit `@paper` always overrides `active_paper`.

When ambiguity remains, prefer asking for paper clarification rather than silently using semantic similarity across multiple registered papers.

Resolving an explicit alias for one request must not mutate `active_paper`. The active pointer changes only through `use` or another explicit state-changing command. Before retrieval, confirm that the alias exists and that its stored `paper_id` matches the namespace metadata.

---

# 15. Cross-Paper Comparison

Cross-paper reasoning should only happen when explicitly requested.

Examples:

```text
$papertalk compare @opd @sapo How do the two papers conceptualize policy improvement?
```

```text
$papertalk panel @opd @gate Are these fundamentally solving the same kind of selection problem?
```

When comparing:

1. retrieve each paper model independently
2. preserve notation namespaces
3. normalize concepts only at comparison time
4. explicitly distinguish:
   - same notation / different meaning
   - different notation / same conceptual role
   - truly different assumptions or objectives

Do not merge the underlying paper models.

Run comparisons in an ephemeral comparison workspace whose inputs are read-only snapshots labeled by alias and `paper_id`. Normalized concepts, correspondence tables, and comparison conclusions belong to the comparison result, not to either paper namespace, and must never be written back into a source paper model or its author research.

For an Author-perspective comparison, load each paper's Composite Author separately and preserve the alias on every author-derived claim. Do not synthesize a cross-paper Composite Author unless the user explicitly asks for that analytical artifact; if requested, keep it ephemeral and outside all source namespaces. Non-Author comparison roles remain unable to access any Composite Author.

Mentioning two aliases is not by itself permission to merge them. Cross-paper retrieval requires an explicit comparison intent such as `compare`, “contrast,” or a direct question about the relationship between the named papers. If several aliases are present without a clear comparative task, ask what should be compared.

---

# 16. Response Scope Indicator

Every paper-specific response must show a lightweight scope marker. This is especially important when multiple papers are registered.

Examples:

```text
[Paper: OPD | Perspective: Author]
```

```text
[Paper: OPD | Panel: Author · Reviewer · Researcher]
```

```text
[Compare: OPD ↔ SAPO | Perspective: Researcher]
```

This should remain concise.

If the system cannot determine the scope marker with confidence, it should not answer the paper-specific question.

---

# 17. Continuous Conversation Behavior

The user should be able to continue asking questions about the same paper without repeating the source.

Example:

```text
$papertalk use @opd
```

then:

```text
$papertalk Why introduce rho?
```

then:

```text
$papertalk reviewer Is that actually necessary?
```

then:

```text
$papertalk panel What is the strongest weakness of this argument?
```

The paper remains fixed while the perspective changes.

If the user then runs `use @sapo`, subsequent follow-ups resolve only against `@sapo`. A phrase such as “does their theorem need that assumption?” must not inherit the theorem or assumption from `@opd`; if `@sapo` does not supply an unambiguous referent, ask the user rather than consulting the prior namespace.

Do not assume a skill remains implicitly active across turns in runtimes that require explicit skill invocation; however, the paper registry and active paper may persist if supported.

---

# 18. Recommended Skill Architecture

Suggested repository layout:

```text
papertalk/
│
├── README.md
├── LICENSE
│
├── skills/
│   └── papertalk/
│       ├── SKILL.md
│       │
│       ├── references/
│       │   ├── author.md
│       │   ├── author-distillation.md
│       │   ├── composite-author.md
│       │   ├── role-access-boundaries.md
│       │   ├── distillation-adapters.md
│       │   ├── reviewer.md
│       │   ├── researcher.md
│       │   ├── teacher.md
│       │   ├── implementer.md
│       │   ├── field.md
│       │   ├── panel.md
│       │   ├── evidence-protocol.md
│       │   ├── paper-model.md
│       │   ├── author-research-model.md
│       │   └── multi-paper-isolation.md
│       │
│       └── scripts/
│           └── optional helper scripts
│
├── chatgpt/
│   ├── PROJECT_INSTRUCTIONS.md
│   └── PAPERTALK.md
│
├── examples/
│   ├── single-paper.md
│   ├── multi-paper.md
│   ├── panel.md
│   └── compare.md
│
└── evals/
    ├── author-reasoning.yaml
    ├── reviewer-quality.yaml
    ├── hallucination.yaml
    ├── multi-author-synthesis.yaml
    ├── author-source-provenance.yaml
    ├── role-context-isolation.yaml
    ├── cross-paper-isolation.yaml
    ├── active-paper-switching.yaml
    ├── cache-namespace.yaml
    ├── comparison-nonmutation.yaml
    └── notation-isolation.yaml
```

---

# 19. SKILL.md Responsibilities

Keep `SKILL.md` relatively small.

It should mainly:

1. identify the paper source / active paper
2. resolve exactly one alias and `paper_id`, or an explicit comparison set
3. reject missing, conflicting, or ambiguous scope
4. parse the requested perspective
5. parse the requested task
6. load or build records only inside the resolved namespace
7. construct the role's allowed context
8. for Author only, load or build per-author distillates and the Composite Author model for that same owner
9. load the relevant reference instructions
10. answer using the permitted evidence models
11. enforce evidence labels / uncertainty
12. emit the resolved scope marker
13. enforce paper and role isolation on every read, write, cache, and tool call

Suggested high-level router:

```text
user message
    ↓
resolve paper
    ↓
validate alias + paper_id owner
    ↓
resolve perspective
    ↓
resolve task
    ↓
load paper model
    ↓
construct role-scoped context
    ↓
if Author: load/build Composite Author model
    ↓
load perspective instructions
    ↓
answer
```

Do not put all perspective instructions into the top-level `SKILL.md` if progressive disclosure is available.

---

# 20. Suggested Router Logic

Pseudo-logic:

```text
if command == add:
    normalize alias
    reject alias collision
    resolve source and compute paper_id
    create an empty alias-owned namespace
    register paper atomically
    optionally build lightweight paper model
    set active paper if first paper
    return alias and paper_id

elif command == list:
    show registered papers and active paper

elif command == use:
    require exact registered alias
    set active paper pointer only
    do not import prior paper conversation state

elif command == remove:
    resolve exact alias and paper_id
    remove only that namespace and registry entry
    if it was active, clear active paper
    do not mutate any other paper or auto-select a replacement

elif command == compare:
    resolve all requested papers
    validate each alias and paper_id independently
    load read-only snapshots from each namespace
    perform cross-paper reasoning in an ephemeral comparison workspace
    never write comparison artifacts into a source namespace

else:
    resolve paper:
        explicit @paper
        else active_paper
        else infer only if exactly one paper is registered
        else ask user

    validate scope:
        alias must exist
        namespace owner must equal (alias, paper_id)
        all retrieval and cache keys must include the owner
        on mismatch, fail closed

    resolve perspective:
        explicit perspective
        else author

    resolve task:
        explicit task token
        else infer from language

    build allowed context:
        always load shared paper model
        if perspective == author:
            discover an available distillation capability
            load or lazily build each author distillate
            synthesize or refresh Composite Author model
            add Composite Author model to context
        elif perspective == panel:
            construct a separate context for each panel role
            add Composite Author model only to Author context
        else:
            do not load author-research state or sources
            allow only task-relevant, non-author-profile retrieval

    load corresponding reference instructions

    answer from that paper namespace only
```

---

# 21. ChatGPT Project Compatibility

The same conceptual skill should be usable in ChatGPT Projects.

Because ChatGPT Project instructions may have practical length limits, use:

```text
Project instructions
    ↓
short router / activation rules

Project files
    ↓
PAPERTALK.md
author.md
reviewer.md
...
```

Suggested `PROJECT_INSTRUCTIONS.md`:

```text
You are operating under the PaperTalk protocol.

When the user uses /paper, follow the PaperTalk instructions
provided in the project files.

Default perspective: author.

Supported perspectives:
- author
- reviewer
- researcher
- teacher
- implementer
- field
- panel

Always distinguish:
[E] explicitly stated by the paper
[I] strongly inferred from the paper
[H] reconstructed or hypothesized reasoning

Never present [H] as documented author intent.

Build a separate, source-grounded distillate for every author and
synthesize a paper-specific Composite Author. Use that composite only
in the Author perspective.

Reviewer, Researcher, Teacher, Implementer, and Field perspectives
must share the paper model and may use task-relevant sources, but
never author profiles, extra-paper sources gathered for author
distillation, individual distillates, or composite mindset. Isolate
each section of a Panel accordingly.

Respect paper namespaces and never transfer notation, assumptions,
motivation, or conclusions across papers unless the user explicitly
requests comparison.

Resolve an exact paper alias before any paper-specific retrieval.
Namespace every model, author distillate, cache entry, and conversation
note by alias and paper identity. Never retrieve globally and filter
afterward. Switching the active paper must not carry unresolved
referents or working memory from the previous paper. Cross-paper
comparison uses labeled read-only inputs and must not modify either
paper's state.
```

The detailed protocol lives in project files.

---

# 22. Codex Compatibility

Canonical Codex use:

```text
$papertalk ...
```

The core skill should remain platform-neutral.

Codex-specific functionality can include:

- reading local PDFs/files
- storing registry state in the repo
- optional scripts
- persistent cached paper models
- integration with local research repositories

Avoid baking Codex-only shell commands into the conceptual core.

---

# 23. Persistent State

For Codex / repo usage, optionally store state locally. Even the minimal implementation should use one directory per alias so whole-directory retrieval cannot accidentally mix papers.

Suggested structure:

```text
.papertalk/
├── registry.yaml
└── papers/
    ├── opd/
    │   ├── identity.yaml
    │   ├── source.yaml
    │   ├── paper-model.md
    │   ├── author-research/
    │   │   ├── sources.yaml
    │   │   ├── individuals/
    │   │   │   └── <author-id>.md
    │   │   └── composite.md
    │   ├── retrieval-index/
    │   ├── conversation-state/
    │   └── cache/
    │
    └── sapo/
        └── ...
```

`identity.yaml` should repeat the alias and `paper_id`; loaders must verify both before accepting any file in that directory. Restrict aliases to a path-safe canonical form such as lowercase letters, digits, and internal hyphens. Do not interpolate unchecked aliases into filesystem paths or database collection names.

If storage deduplication is later needed, an optional content-addressed raw-object store may hold immutable source bytes. It must not hold paper-specific extraction, annotation, or interpretation, and normal retrieval must remain namespace-scoped.

Do not over-engineer caching before the interaction design is validated.

---

# 24. State Design Principles

Persistent state should be treated as **derived cache**, not authoritative truth.

The source paper remains authoritative.

If the cached model conflicts with the paper:

```text
paper source wins
```

Useful cache fields:

- identity
- notation
- central problem
- major decisions
- claims
- assumptions
- theorem roles
- open questions
- evidence references

Keep author-research cache fields in a separate store:

- verified author identities
- author position, equal-contribution marks, corresponding-author marks, and ordering-convention assessment
- source inventory and retrieval dates
- one distillate per author
- conflicts and coverage gaps
- explicit contribution evidence
- Composite Author synthesis and its supporting authors
- relevance and evidence levels for every mindset claim

Access separation is an invariant even when both stores are persisted in the same directory. Non-Author role execution should not retrieve the author-research files.

Paper separation is an independent invariant. Every cached object should carry its owner metadata, and readers should verify that metadata after retrieval. Invalidation, refresh, removal, and rebuild operations must target one exact `(alias, paper_id)` namespace; they must not use a broad paper-directory scan or an author identity as the mutation scope.

The active paper is only a registry pointer. Do not store paper content, notation, author state, or conversational summaries on the active pointer itself, because changing it would make that state appear to belong to the next paper.

Avoid caching speculative conclusions without their evidence level.

---

# 25. Suggested Output Style

Default Author answer for a multi-author paper:

```text
[Paper: OPD | Perspective: Composite Author]

We were trying to ..., but the main obstacle was .... That is why we chose ....
Our best reconstruction of the tradeoff is ...

Evidence: [E] paper §1 · [I] author synthesis · confidence: moderate
```

For a single-author paper, use `I` instead of `we`. First-person language is an evidence-grounded role voice, not a claim that inferred reasoning is literal author testimony.

Default to one to three short, colloquial paragraphs. Do not show the full goal-to-consequence outline, equations, derivations, implementation details, biographies, source inventories, or extensive citations unless requested. Use natural hedging in the prose and one compact evidence footer rather than forcing labels onto every sentence. Include author coverage only when it materially affects confidence.

Reviewer should speak as `I` and make an evidence-driven judgment. It may focus on an appreciated strength, a concern, or both, depending on what is relevant; do not force artificial balance.

Researcher may retain the current third-person analytical style. No other role may default to third-person narration.

Panel answers should preserve these role voices and stay concise enough that perspectives remain comparable.

When author research materially affects an answer, expose a compact provenance note or offer to show the supporting per-author evidence. Do not overwhelm ordinary answers with biographies or source inventories.

---

# 26. Important Failure Modes

The implementation should explicitly defend against these.

## 26.1 First-person Author voice becomes fabricated testimony

Bad:

```text
We first tried direct optimization and it failed.
```

unless the paper says so.

Good:

```text
My best reconstruction is that we may have considered direct
optimization first, because...

Evidence: [H] plausible reconstruction · confidence: low
```

The first-person voice should improve conversational immersion without weakening the evidence boundary.

---

## 26.2 Cross-paper state leakage

Bad:

```text
@paperA rho gets the definition from @paperB
```

The same prohibition applies to assumptions, theorem numbering, experiment results, retrieved passages, author distillates, cached answers, and conversational referents. It must never happen, even when papers share authors, terminology, citations, or source URLs.

---

## 26.3 Reviewer role invents different paper facts

Reviewer may challenge interpretation, but must share the same factual substrate.

---

## 26.4 "Teacher" simply repeats derivation

Teacher should diagnose the missing conceptual layer.

---

## 26.5 "Researcher" just predicts the paper's actual next step

Researcher should generate multiple plausible alternatives before revealing what the paper chose.

---

## 26.6 Panel produces redundant summaries

Each role should answer a distinct question:

- Author: why this choice
- Reviewer: does it hold
- Researcher: what else could be done

---

## 26.7 Over-caching

Do not spend a large amount of time building exhaustive paper state if the user only asks one small question.

Prefer lazy enrichment of the paper model.

---

## 26.8 Naive author averaging

Do not count repeated tendencies as votes or let authors with more indexed material dominate automatically. Synthesize by relevance, evidence quality, complementary expertise, and explicit contribution information.

---

## 26.9 Overconfident authorship-role inference

Do not ignore authorship order, but do not convert it into a factual attribution or force authors into exclusive role buckets. First/co-first authors may influence both execution and direction; corresponding-author status adds a direction-facing prior rather than monopolizing topic or motivation. Explicit contribution evidence can override every positional prior. Disable or weaken the priors for alphabetical lists, consortia, and fields with different conventions. Never weight by citation count, institution, fame, or assumed advisor status.

---

## 26.10 Author information leaks into other roles

A Reviewer answer that quietly uses an author's interview, or a Researcher answer shaped by the Composite Author model, violates the architecture even if the result sounds plausible. Enforce the restriction at retrieval and context construction time.

---

## 26.11 False composite consensus

Do not erase disagreement among individual distillates to create one smooth voice. The composite may contain shared tendencies, complementary roles, tensions, and unresolved uncertainty.

---

## 26.12 Irrelevant or invasive profiling

Do not use personal life details, protected characteristics, speculative psychology, or unrelated public trivia. Public availability does not make information relevant to research-mindset reconstruction.

---

## 26.13 Distillation dependency drift

An external distillation skill may change, disappear, or emit incompatible evidence claims. Normalize its output through PaperTalk's contract, record its version when possible, and validate the result before caching it.

---

# 27. Suggested Evals

The skill should have real evals, not only examples.

## 27.1 Author reasoning eval

Question:

```text
Why do the authors introduce r?
```

Check that the answer:

- identifies the role of `r`
- connects it to the optimization problem
- distinguishes `r` from the deployed policy
- explains motivation, not only definition
- uses `I` for a single author or `we` for a multi-author Composite Author
- defaults to one to three short, high-level paragraphs with a compact evidence footer
- does not invent historical intent

---

## 27.2 Reviewer eval

Question:

```text
Is Assumption 3 really necessary?
```

Check that the answer:

- identifies where the assumption is used
- distinguishes theorem necessity from modeling convenience
- identifies possible weaker alternatives
- speaks as `I` and acknowledges supported strengths as readily as concerns
- does not invent praise or criticism to appear balanced
- does not simply restate the assumption

---

## 27.3 Researcher eval

Prompt:

```text
Stop after Eq. 4. What would you try next?
```

Check that the answer:

- proposes multiple plausible directions
- does not immediately jump to the paper's actual solution
- explains tradeoffs
- retains third-person analytical narration and stays concise unless technical depth was requested

---

## 27.4 Cross-paper isolation eval

Load:

```text
Paper A:
rho = incumbent distribution
Assumption 3 = bounded rewards
Theorem 2 = convergence result
Shared author X has a target-paper-relevant optimization background

Paper B:
rho = target distribution
Assumption 3 = realizability
Theorem 2 = impossibility result
Shared author X has a target-paper-relevant evaluation background
```

Alternate requests across `@paperA` and `@paperB`, including explicit aliases, `use` switches, unscoped follow-ups, Author mode, and Reviewer mode.

Check that:

- every response shows the resolved alias
- notation, assumptions, theorem roles, and conversation referents come only from that alias
- the shared author receives separate target-conditioned distillates
- neither Composite Author includes the other paper's relevance judgments
- switching the active paper does not transfer unresolved context
- a missing referent causes clarification rather than cross-namespace search

---

## 27.5 Author-intent hallucination eval

Provide a paper that never explains why a choice was made.

Ask:

```text
Why did the authors choose method X?
```

The answer should separate:

```text
[E] none
[I] ...
[H] ...
```

and never fabricate an explicit statement.

---

## 27.6 Panel differentiation eval

Question:

```text
Is Theorem 2 actually interesting?
```

Require clearly distinct Author, Reviewer, and Researcher answers.

Also verify that only the Author section uses the Composite Author model.

Verify that Author uses `I` or `we`, Reviewer uses `I`, Researcher remains third-person, and each section is concise by default.

---

## 27.7 Multi-author synthesis eval

Provide three authors whose public research records show one shared tendency, one complementary specialization, and one genuine tension.

Check that the result:

- creates a separate sourced distillate for each author
- identifies the shared tendency without vote-counting
- uses complementary specialization to explain paper choices only when supported
- preserves the tension in the composite
- gives first/co-first authors more prior influence over execution-facing choices
- allows first/co-first authors strong influence over topic and motivation when supported
- gives explicitly identified corresponding authors more prior influence over direction-facing choices
- permits overlapping influence instead of assigning direction exclusively to corresponding authors
- lets direct contribution evidence override order
- disables the first-author prior for an explicitly alphabetical control case
- labels unsupported position-to-contribution attribution as `[H]`

---

## 27.8 Role-context isolation eval

Place a distinctive fact only in an author interview, not in the target paper. Ask the same question in Author, Reviewer, Researcher, and Panel modes.

Check that:

- Author may use the fact with `[AS]` provenance
- Reviewer and Researcher do not mention or rely on it
- only the Author section of Panel can access it

---

## 27.9 Sparse and conflicting author evidence eval

Give one author rich relevant evidence, one only an ambiguous name match, and one a source contradicting the apparent consensus.

Check that the skill:

- does not merge the ambiguous identity
- reports uneven coverage
- prevents the richly documented author from automatically dominating
- preserves the contradiction
- lowers confidence in the Composite Author accordingly

---

## 27.10 Distillation-adapter eval

Run the same source pack through the native fallback and an available external distillation skill. Both results should normalize to the required claim, provenance, coverage, conflict, and unknown fields without weakening PaperTalk's role-access boundary.

---

## 27.11 Cache and alias-rebinding isolation eval

Create two papers with the same symbol names, author, and question text so their naive cache keys would collide. Verify that each answer is cached and retrieved under its own `(alias, paper_id)` owner.

Then explicitly replace one alias with a different source. Check that all old derived state for that alias is invalidated, the new `paper_id` is required, and the other aliases remain byte-for-byte unchanged.

---

## 27.12 Comparison non-mutation eval

Compare two papers whose notation must be normalized to answer the question. Snapshot both namespaces before and after comparison.

Check that:

- the comparison reads labeled, read-only inputs
- normalization exists only in the comparison workspace or response
- neither paper model, author model, retrieval index, nor conversational state changes
- a later single-paper question returns the original paper-specific meaning

---

# 28. README Positioning

Do not position this as:

> A collection of prompts for paper reading.

Better:

> An evidence-grounded, multi-perspective environment for reconstructing research reasoning.

Potential tagline:

> Don't just ask what the paper says. Ask why the paper had to look this way.

Or:

> Read papers from the inside out.

The core product idea is:

```text
Target-paper evidence ─→ Shared Paper Model ─┬─→ Reviewer
                                             ├─→ Researcher
                                             ├─→ Teacher
                                             ├─→ Implementer
                                             └─→ Field

Per-author public evidence ─→ Individual distillates
                                      ↓
                             Composite Author Model
                                      │
Shared Paper Model ───────────────────┴─→ Author
```

---

# 29. Recommended Development Plan

## v0.1 — Core Skill

Implement:

- `SKILL.md`
- target-paper distillation and shared paper model
- one research-mindset distillate per author
- identity disambiguation and source provenance
- decision-specific first/co-first and corresponding-author priors
- Composite Author synthesis
- inventory and benchmark candidate maintained distillation skills
- distillation adapter plus native fallback
- Author perspective using the Composite Author
- Reviewer perspective
- Researcher perspective
- Panel
- evidence protocol
- hard role-context isolation
- `add`, `list`, `use`, and unique aliases
- per-alias `(alias, paper_id)` namespaces
- multi-paper state and conversation isolation
- active paper

Avoid backend complexity, but do not postpone namespace isolation; it is a correctness requirement from the first multi-paper implementation.

---

## v0.2 — Comparison and Persistence

Add:

- notation tables
- explicit cross-paper compare using read-only snapshots
- persistent per-alias retrieval indexes and caches
- explicit alias replacement with targeted invalidation
- saved comparison artifacts, if requested, outside source namespaces

---

## v0.3 — Additional Perspectives

Add:

- Teacher
- Implementer
- Field

Only after the core Author / Reviewer / Researcher experience is strong.

---

## v0.4 — Distribution

Publish GitHub repo.

Support:

- raw Codex skill
- ChatGPT Project instructions
- examples
- evals

---

## v1.0 — Optional Plugin Wrapper

Only after the workflow is validated.

A Plugin should be treated primarily as a **distribution layer**, not as the core implementation.

Potential future integrations:

- arXiv search
- Semantic Scholar
- citation graph
- Zotero
- local paper library
- MCP tools
- persistent literature database

---

# 30. Minimal Viable User Experience

The first version should already support this flow:

```text
$papertalk add opd ./papers/opd.pdf
```

```text
$papertalk Why do they introduce rho?
```

```text
$papertalk reviewer Is that construction actually necessary?
```

```text
$papertalk researcher Stop before Theorem 2. What would you try next?
```

```text
$papertalk panel Is Theorem 2 actually interesting?
```

Then:

```text
$papertalk add sapo https://arxiv.org/abs/2608.19842
```

```text
$papertalk use @sapo
```

```text
$papertalk Why do they use a shared actor/critic representation?
```

An explicit one-off query should remain isolated and should not change the active paper:

```text
$papertalk @opd What does rho mean here?
```

The answer uses only `@opd`. A subsequent unscoped question still uses active `@sapo`, with no notation, author state, or conversational referents carried over from `@opd`.

Then compare:

```text
$papertalk compare @opd @sapo
How do the two papers think about policy improvement?
```

If this interaction feels natural, the core design is working.

---

# 31. Non-Goals for v0.1

Do not attempt to solve all of these immediately:

- full literature management
- citation graph database
- automatic paper recommendation
- full PDF annotation UI
- external vector database
- cloud backend
- authentication
- collaborative annotations
- publication-ready review reports
- generic academic writing assistant
- exhaustive surveillance or archiving of everything public about an author
- personal, psychological, demographic, or non-research profiling
- automatic attribution of contributions when no explicit evidence exists

The first goal is much narrower:

> Make interactive paper understanding substantially better by reconstructing a paper-specific collective research mindset from relevant public research evidence, while keeping every non-Author perspective grounded only in the shared paper model.

---

# 32. Final Design Principle

The skill should not be framed as:

```text
AI treats its first-person role voice as literal author testimony.
```

It should be framed as:

```text
Evidence-grounded synthesis of each author's relevant research mindset
into a paper-specific representative that speaks conversationally while
keeping inference and reconstruction visibly calibrated.
```

And the core triad should remain:

```text
       Composite Author
       "Why would we do this?"
            /       \
           /         \
          ▼           ▼
    Reviewer  ←──  Researcher
 "Does it hold?"   "What else?"
```

This triangle gives the user three complementary abilities:

```text
Understand
Question
Invent
```

That should be the defining experience of PaperTalk.

The triangle shares paper understanding, not author mindset. Only the Composite Author vertex receives extra-paper author evidence; Reviewer and Researcher remain independent views of the paper itself.
