# PaperTalk Help

## Registry and utilities

| Function | Example | Explanation |
|---|---|---|
| `help` | `$papertalk help` | List every public PaperTalk function without resolving a paper or changing state. |
| `add` | `$papertalk add <alias> <public_link>` | Register a paper source under a unique local alias and create its isolated namespace. |
| `list` | `$papertalk list` | List registered papers and indicate which alias is currently active. |
| `use` | `$papertalk use @<alias>` | Set the active paper used when a later analysis request omits an alias. |
| `remove` | `$papertalk remove @<alias>` | Unregister one explicitly named paper by moving its complete namespace to recoverable trash. |
| `removed` | `$papertalk removed` | List removal records and show which archived paper namespaces can still be restored. |
| `restore` | `$papertalk restore <removal-id>` | Restore a recoverable paper namespace without overwriting an existing alias. |

## Perspectives and panels

| Function | Example | Explanation |
|---|---|---|
| `author` | `$papertalk author @<alias> summarize <paper_aspect>` | Explain the paper in an evidence-grounded author voice using the paper-safe Composite Author context. |
| `reviewer` | `$papertalk reviewer @<alias> critique <claim_or_theorem>` | Assess strengths, weaknesses, correctness, and readiness as an independent reviewer without issuing an editorial decision. |
| `researcher` | `$papertalk researcher @<alias> extend <method_or_open_question>` | Explore alternative approaches, extensions, and discriminating evidence from a researcher perspective. |
| `panel` | `$papertalk panel @<alias> <discussion_topic>` | Start a new latest Panel with independently frozen Author, Reviewer, and Researcher responses. |
| `panel_continue` | `$papertalk panel_continue @<alias> reviewer:author <focus_guidance>` | Continue the latest Panel with one named role responding to another role's newest answer under optional guidance. |

## Task guidance

| Function | Example | Explanation |
|---|---|---|
| `explain` | `$papertalk author @<alias> explain <concept>` | Explain a paper concept at the level of detail requested by the user. |
| `why` | `$papertalk author @<alias> why <research_choice>` | Reconstruct the motivation and tradeoffs behind a specific research choice. |
| `derive` | `$papertalk author @<alias> derive <equation_or_theorem>` | Work through a requested equation or theorem while preserving the selected role. |
| `critique` | `$papertalk reviewer @<alias> critique <claim_or_design_choice>` | Evaluate a claim or design choice and calibrate any concern to its consequence. |
| `summarize` | `$papertalk author @<alias> summarize <paper_aspect>` | Give a concise role-appropriate summary grounded in the paper's permitted evidence. |
| `extend` | `$papertalk researcher @<alias> extend <method_or_open_question>` | Propose research extensions with their assumptions, tradeoffs, and useful tests. |
| `attack` | `$papertalk reviewer @<alias> attack <claim_or_assumption>` | Stress-test the requested claim or assumption without manufacturing unsupported criticism. |
