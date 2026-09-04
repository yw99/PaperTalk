# Author research and Composite Author

Read this reference only for Author perspective or the Author section of a Panel. Do not read or retrieve author-research state for Reviewer or Researcher.

## Purpose

Most papers have several authors. Build a separate, target-conditioned distillate for every named author, then synthesize a paper-specific Composite Author. The composite represents the collaboration's plausible research logic for this paper; it is not a personality profile, literal group consciousness, or simple average.

## Per-author research

First verify identities using the target paper, affiliations, ORCID or comparable identifiers, topics, and publication history. Do not merge people with similar names.

Search relevant public scholarly and professional evidence in roughly this order:

1. target paper, appendices, supplements, code, rebuttals, project pages, and explicit contribution statements
2. related papers by that author, prioritizing topical and temporal proximity
3. public talks, lectures, interviews, technical blogs, and project pages
4. scholarly profiles as discovery aids

Retain research-relevant signals: recurring questions and framings, methods, abstractions, evidence standards, tradeoffs, limitations, changes over time, and supported connections to target-paper decisions. Exclude private or sensitive details, personal trivia, demographic or personality inference, and prestige signals. Authorship order may inform the contribution prior below, but must not be presented as direct evidence that a particular person supplied an idea.

For long author lists, make a breadth-first pass across every author before deepening any profile. Report coverage gaps; never silently omit an author because someone else has a larger public footprint.

Store each distillate only under the resolved paper namespace and include:

```yaml
owner: {alias: <alias>, paper_id: <paper_id>}
author:
identity_evidence: []
authorship_metadata:
  position:
  author_count:
  equal_contribution_group:
  is_corresponding_author:
  corresponding_author_evidence:
  ordering_convention: contribution-ordered | alphabetical | mixed | unknown
  ordering_convention_confidence:
source_coverage: {searched: [], included: [], gaps: []}
mindset_claims:
  - claim:
    dimension:
    evidence_level: E | I | H
    source_origin: P | AW | AS | D
    source:
    source_date:
    relevance_to_target_paper:
    counterevidence:
target_paper_connections: []
explicit_contribution_evidence: []
```

If a maintained distillation skill is available, it may be used, but normalize its result to this schema and retain PaperTalk's evidence and access rules. Otherwise distill natively. Do not require or copy an external skill in v0.1.

## Composite synthesis

Synthesize only after independent distillates exist. Identify:

- tendencies supported across authors
- complementary expertise that may explain different paper choices
- conflicts and alternative interpretations
- explicit contribution evidence
- coverage limits and uncertainty

Use a decision-specific contribution prior rather than one global author weight:

1. **Direct contribution evidence dominates.** Apply explicit contribution statements, CRediT roles, author interviews, project documentation, and clearly attributable artifacts before any ordering heuristic.
2. **First and explicitly co-first authors get the strongest general default prior, especially for execution-facing decisions.** This includes technical conception, method development, derivations, experiments, implementation, and drafting. They may also have originated or strongly shaped the topic, motivation, problem framing, and project conception; never exclude that possibility. Give authors marked as equal contributors the same first-author prior.
3. **Explicitly identified corresponding authors get an additional strong prior for direction-facing decisions.** This includes topic selection, problem framing, motivation, project conception, coordination, and research direction. This prior is not exclusive and must not suppress first/co-first author influence when their record or direct evidence supports it. Do not automatically call a corresponding author an advisor; treat advising or supervision as a separate claim requiring evidence.
4. **Last-author or senior-author position is field-dependent.** Use it as a project-direction prior only when the paper's field convention or explicit evidence supports that interpretation. Never assume the last author is corresponding or supervisory merely from position.
5. **Other authors retain a nonzero neutral prior.** Their direct evidence or highly relevant research record can outweigh positional priors for a particular decision.

Authorship-role priors may overlap. For a mixed decision, both first/co-first and corresponding authors can receive strong influence, with direct evidence determining the final balance.

Before applying order, classify the paper's ordering convention as contribution-ordered, alphabetical, mixed, or unknown. Disable the first-author ordering prior for clearly alphabetical authorship. Weaken all ordering priors for consortia, very large collaborations, or unknown conventions. If corresponding authors are not explicitly marked in the paper or reliable metadata, record them as unknown rather than guessing.

Then weight the underlying evidence by target-paper relevance, source quality, recency, and consistency. Preserve disagreement instead of forcing consensus. An authorship position is `[E][P]`; a contribution inferred from that position is normally `[H]` unless corroborating evidence justifies `[I]`.

For every major paper decision, record which prior was applied:

```yaml
decision_influence:
  decision:
  decision_type: execution | direction | mixed
  authors:
    - author:
      direct_contribution_evidence: []
      authorship_role_prior: first | co-first | corresponding | field-specific-senior | neutral
      relevant_mindset_evidence: []
      inferred_influence:
      evidence_level:
  ordering_convention:
  uncertainty:
```

Every composite claim must link to the supporting and contradicting individual distillates and disclose when ordering changed the synthesis. Rebuild it when a distillate or authorship-role interpretation materially changes. Begin the composite file with the same `(alias, paper_id)` owner and reject any mismatched input.

## Answering

Combine the Composite Author with the shared paper model only after both owners match. Speak as `I` for a single author and `we` for a multi-author composite, while naturally hedging inferred or hypothetical intent. Reflect author-derived evidence in the compact evidence footer; include a coverage count only when incomplete or uneven coverage materially affects confidence. Attribute `[E][AW]` or `[E][AS]` claims to their actual source, do not imply they were stated in the target paper, and offer the per-author support instead of listing it in an ordinary concise answer.
