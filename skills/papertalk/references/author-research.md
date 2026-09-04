# Author research and Composite Author

Read this reference only for Author perspective or the Author section of a Panel. Do not read or retrieve author-research state for Reviewer or Researcher. Before persisting or loading author evidence, also read [artifact-contract.md](artifact-contract.md).

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

Choose and record a research tier:

- **Quick:** target paper and official artifacts, verified authorship and contribution metadata, and the closest useful related work for each author.
- **Standard:** breadth-first author coverage, several topically and temporally close works where available, public technical statements, counterevidence, alternative explanations, and a user-visible research-quality checkpoint.
- **Deep:** broader scholarly trajectories, talks, project histories, rebuttals, code history, temporal change, external technical perspectives, and behavioral validation.

These are depth definitions, not source quotas. For long author lists, make a breadth-first pass across every author before deepening any profile. Stop when additional sources no longer materially change high-confidence claims. Record the tier, searched coverage, gaps, quality checkpoint, and stopping reason in the P0 artifacts; never silently omit an author because someone else has a larger public footprint.

## Claim filter

Before a candidate mindset claim enters an individual distillate, test:

1. **Recurrence:** does it appear across relevant works, decisions, or source types?
2. **Target relevance:** does it explain a concrete choice, constraint, or tradeoff in this paper?
3. **Predictive value:** can it reconstruct a withheld decision or distinguish plausible alternatives?
4. **Specificity:** is it more informative than generic research competence or normal field practice?

Classify the claim as `durable`, `decision-heuristic`, `paper-specific-explicit`, or `omit`. A target-paper statement may remain as paper-specific `[E]` evidence without recurrence. Keep omitted candidates in the claim ledger for auditability, but never link them into an individual distillate or Composite Author. Preserve supporting locations, counterevidence, alternative explanations, rationale, temporal scope, and confidence.

Store sources, candidate claims, coverage, and each individual distillate under the resolved namespace using [artifact-contract.md](artifact-contract.md), then run the validator. If a maintained distillation skill is available, it may help collect candidates, but normalize the result to PaperTalk's contract and retain its evidence and access rules. Otherwise distill natively.

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

For every major paper decision, record the decision type, candidate explanations, each author's direct contribution sources, overlapping role priors, relevant included claim IDs, supporting and contradicting weights, inferred influence, evidence level, ordering convention, ordering effect, and unresolved uncertainty. Use the exact machine-readable structure in [artifact-contract.md](artifact-contract.md).

Every composite claim must link to supporting individual claim IDs and any contradicting claim IDs. Rebuild it when a distillate or authorship-role interpretation materially changes. Run `paper_artifacts.py validate`, and obtain an allowed Author context with `paper_artifacts.py context author`; do not load a draft, untraceable, or owner-mismatched composite.

## Answering

Combine the Composite Author with the shared paper model only after both owners match. In the role body, speak as `I` for a single author and `we` for a multi-author composite; never narrate the public research, distillation, or synthesis process as if the author were describing it. Phrase supported content in a way the author could plausibly say in conversation, and carry `[E]`, `[I]`, `[H]`, confidence, and any material coverage limit in the compact footer. Attribute `[E][AW]` or `[E][AS]` correctly in the evidence layer, do not imply that it appeared in the target paper, and offer the per-author support instead of listing it in an ordinary concise answer. Omit unsupported private project history.
