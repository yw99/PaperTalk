# Evidence and shared paper model

Read this reference when ingesting a paper, building or refreshing its model, or answering a question whose support is uncertain.

## Epistemic labels

- `[E] Explicit`: directly stated in an identified source.
- `[I] Inferred`: strongly supported by structure, equations, proofs, experiments, or related discussion.
- `[H] Hypothesized`: a useful reconstruction that is not documented strongly enough to attribute to the authors.

Never present `[H]` as historical fact. Prefer language such as “a plausible reconstruction is” or “the paper does not state this directly, but.”

Track source origin separately:

- `[P]`: target paper or an official artifact such as its appendix, supplement, code, rebuttal, or project page
- `[AW]`: another scholarly work by an author
- `[AS]`: a public professional statement by an author
- `[D]`: discovery metadata such as a profile or index

The shared paper model may contain `[P]` evidence only. Extra-paper `[AW]`, `[AS]`, and author-profile `[D]` material belongs to author research and must not enter the shared model. Role-specific related literature used by Reviewer or Researcher is temporary task evidence, not author-profile state.

## Build lazily

Read the strongest version of the source available. Extract only the detail needed for current and likely follow-up questions; enrich the model as the conversation develops. The paper remains authoritative over cached interpretation.

Record locations for consequential evidence: page, section, equation, theorem, figure, table, appendix, or stable source fragment. Do not use a paper summary as a substitute for checking the primary paper when the source is available.

## Shared paper model

Keep the model under the namespace returned by the registry helper. Begin the persisted file with its owner:

```yaml
owner:
  alias: <alias>
  paper_id: <paper_id>
```

Useful fields are:

```yaml
identity:
  title:
  authors: []
  year:
  source:

central_problem:
  what:
  why_it_matters:
  existing_gap:

starting_point:
  available:
  preserved:
  missing:

notation: {}
assumptions: []
design_constraints: []
reasoning_chain: []
major_decisions: []
claims: []
theorem_roles: {}
experiment_roles: {}
implementation_notes: []
likely_alternatives: []
unresolved_questions: []
```

For each major decision, capture its goal, obstacle, desired property, alternatives, choice, downstream consequences, evidence level, and paper location. For each theorem or experiment, capture the question or doubt it is intended to address—not only its statement or result.

## Response grounding

Facts, notation, theorem statements, and experimental results do not change with perspective. If the requested answer exceeds the evidence, state the gap.

Keep ordinary answers conversational: express uncertainty naturally in the prose and end with one compact evidence footer rather than attaching labels to every sentence. A typical footer is `Evidence: [E] paper §1 · [I] author synthesis · confidence: moderate.` Include source locations that support consequential claims; reserve extensive citations and source inventories for requests that need them. Never hide an important evidence gap merely to stay concise.

First-person Author language is a presentation layer over this evidence model. `[E]` may be stated directly in role voice, while `[I]` and `[H]` must remain visibly hedged so the conversation does not turn a reconstruction into purported testimony.
