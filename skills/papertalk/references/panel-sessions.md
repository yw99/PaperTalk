# Interactive Panel sessions

Read this reference for every `panel` request that starts a discussion and every
`panel_continue` request. Interactive state exists only for registered papers and is
owned by the resolved `(alias, paper_id)`.

## User grammar

Start a new latest panel with the normal Panel form:

```text
$papertalk panel @<alias> <topic>
```

Continue it with exactly one responder and one target:

```text
$papertalk panel_continue @<alias> reviewer:author <optional focus guidance>
```

The alias is mandatory for `panel_continue`. Parse the role pair case-insensitively as
`<responder>:<target>`, allowing whitespace around the colon. Valid roles are `author`,
`reviewer`, and `researcher`. Reject a missing role, repeated role, multiple pairs,
unknown role, or alternate separator before writing state. Everything after the pair
is optional user guidance; it is an instruction, not evidence.

`reviewer:author` means that Reviewer responds to Author's most recent frozen turn in
the latest panel for that paper. One invocation produces one response. Older panels
have no public identifier and cannot be selected or continued.

## Helper

Run the helper relative to this skill directory. Mutation commands read one JSON
object from standard input and every command emits JSON:

```text
python3 scripts/panel_sessions.py parse-pair '<responder>:<target>'
python3 scripts/panel_sessions.py [--root <state-dir>] start [alias]
python3 scripts/panel_sessions.py [--root <state-dir>] initial-context <role> [alias]
python3 scripts/panel_sessions.py [--root <state-dir>] append-initial <role> [alias]
python3 scripts/panel_sessions.py [--root <state-dir>] continue-context <responder> <alias>
python3 scripts/panel_sessions.py [--root <state-dir>] append-continuation <responder> <alias>
python3 scripts/panel_sessions.py [--root <state-dir>] show [alias]
python3 scripts/panel_sessions.py [--root <state-dir>] show-history [alias]
python3 scripts/panel_sessions.py [--root <state-dir>] validate [alias]
```

Use `parse-pair` before resolving continuation context; do not approximate malformed
input or split a multi-pair expression yourself. Do not hand-edit
`conversation-state/panel-sessions.json`; `panel-sessions.lock` is an internal
coordination file. Context tokens bind a
generated answer to the state it saw. If append reports a stale token, discard that
draft, reload context, and generate again; never force the old answer into the new
state.

## Starting a Panel

1. Resolve and verify the paper normally, then call `start` with `topic` and optional
   `members`. Omit `members` for Author, Reviewer, and Researcher. Starting a new panel
   atomically archives the previous latest panel as read-only history.
2. Call `initial-context` separately for every member. Prefer isolated execution
   contexts. Initial contexts always have an empty `peer_turns` list, even if another
   initial answer has already been appended.
3. Generate each role from only its returned `allowed_paths`, the topic, and the
   applicable perspective contract. Apply the conversational pass independently.
4. Call `append-initial` with the unchanged `context_token`, body, and compact evidence
   footer. Tokens for different initial roles may be issued before any response is
   appended, so isolated roles may run in parallel.
5. Display each frozen role answer with its own compact evidence footer, in requested
   order. If one role fails, leave the
   panel incomplete and retry only its missing initial response. `panel_continue` is
   unavailable until every member has an initial turn.

## Continuing the latest Panel

1. Require the explicit alias, then validate the single role pair with `parse-pair`.
   Do not fall back to the active or sole paper for `panel_continue`.
2. Call `continue-context` for the responder with JSON fields `target` and `guidance`.
   The helper resolves only the latest panel and selects the target role's newest turn.
3. Give the responder only the returned original `topic`, `guidance`, `peer_turn`, and
   `allowed_paths`. `peer_turn` contains the target's role and body, not its evidence
   footer or source paths. Do not load the complete transcript or archived panels.
4. Treat `peer_turn` as an attributed conversational claim because it has
   `peer_claim_only: true`. The responder may quote, question, or rebut it, but must
   ground factual assertions in evidence allowed to that responder. User guidance is
   also not evidence.
5. Call `append-continuation` with the same responder, target, guidance, context token,
   final body, and evidence footer. A changed target turn or any intervening append
   makes the token stale and requires regeneration.
6. Return only:

```text
[Paper: <alias> | Perspective: Panel | Continuation: Reviewer→Author]

Reviewer
<response>

Evidence: <reviewer-permitted evidence and confidence>
```

Do not add a moderator summary or another role response.

## Role boundary

The helper delegates role access to `paper_artifacts.py context`. Author still requires
a ready validated Composite Author. Reviewer and Researcher never receive
`author-research` paths. Seeing an Author turn does not grant either role access to the
Author's sources or make the statement independent evidence. Do not persist a peer-only
claim as a Reviewer finding unless Reviewer independently supports it from permitted
evidence.

## State and recovery

`panel-sessions.json` contains its owner, one `latest_panel`, and ordered read-only
`history`. Panels contain their topic, members, status, timestamps, and frozen turns.
Each turn records its role, sequence, kind, body, evidence footer, guidance, visible and
responded-to turn IDs, timestamp, and canonical content hash.

The helper validates ownership, lifecycle, ordering, references, and hashes before
loading or writing. Historical panels are auditable through `show-history` but never
enter a role context. Paper removal and restoration preserve the file because the
registry archives the complete paper namespace.
