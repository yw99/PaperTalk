# Registry and paper isolation

Read this reference for registry commands, persistent paper state, ambiguous scope, active-paper changes, or cross-paper work.

## Helper

Run the helper relative to the skill directory:

```text
python3 scripts/paper_registry.py [--root <state-dir>] <command>
```

The default state directory is `.papertalk` under the current working directory. `PAPERTALK_STATE_DIR` may override it. Commands emit JSON.

```text
add <alias> <source>     Register a unique alias and create its namespace
list                     List papers and the active alias
use <alias>              Change only the active alias pointer
remove <alias> --paper-id <paper_id>
                         Archive one exact namespace and unregister it
removed                  List removal journals and recovery availability
restore <removal_id> [--activate]
                         Restore without overwriting a current alias
resolve [alias]          Resolve an explicit alias, active alias, or sole paper
verify [alias]           Verify registry and namespace ownership
```

The registry helper verifies alias ownership. The P0 artifact helper separately scaffolds, validates, and authorizes role-visible evidence:

```text
python3 scripts/paper_artifacts.py [--root <state-dir>] scaffold [alias]
python3 scripts/paper_artifacts.py [--root <state-dir>] validate [alias]
python3 scripts/paper_artifacts.py [--root <state-dir>] context <author|reviewer|researcher> [alias]
```

Read [artifact-contract.md](artifact-contract.md) before writing these files. Run `context` before loading persisted analysis state; use only the returned paths.

Interactive Panel state is managed separately by `scripts/panel_sessions.py`; read [panel-sessions.md](panel-sessions.md) before using it. The helper owns `conversation-state/panel-sessions.json`, delegates role-visible evidence to `paper_artifacts.py context`, and exposes only the latest Panel for continuation.

Aliases may be written with or without `@`. They normalize to lowercase and must contain only letters, digits, and internal hyphens. `add` rejects collisions.

For a local file, v0.1 fingerprints its bytes. For a URL, v0.1 fingerprints the normalized URL string; remote-content refresh is deferred. The helper creates:

```text
.papertalk/
├── registry.json
├── papers/<alias>/
│   ├── identity.json
│   ├── source.json
│   ├── paper-model.md
│   ├── author-research/
│   │   ├── sources.jsonl
│   │   ├── claims.jsonl
│   │   ├── research-status.json
│   │   ├── individuals/
│   │   ├── composite.json
│   │   └── validation.json
│   ├── role-state/reviewer/
│   ├── conversation-state/
│   │   ├── panel-sessions.json    Created lazily by the first Panel
│   │   └── panel-sessions.lock    Internal mutation lock
│   └── cache/
└── trash/<removal-id>/
    ├── removal.json
    └── namespace/         Present only while the removal is restorable
```

## Required isolation

Every derived object is owned by `(alias, paper_id)`. Always call `resolve` or `verify` before writing persistent paper state, and call `paper_artifacts.py context` before reading analysis state. Use only paths returned by the helpers. Do not assemble a path from unvalidated user input.

Never retrieve all paper directories and filter afterward. Never key a derived object only by a symbol, author, theorem number, URL, or question. The active paper is only a pointer; it contains no paper content or conversation state.

An explicit `@alias` scopes one request and does not change the active paper. `use @alias` changes the pointer without importing working memory from the previously active paper. After a switch, unresolved phrases such as “that theorem” must resolve inside the new namespace or trigger clarification.

`panel_continue` is stricter than ordinary scope resolution: it always requires an explicit alias and reads only that namespace's latest Panel. Historical Panels remain inside that namespace for audit and are never candidates for continuation or role context.

The same author or source may occur in several papers. Raw immutable source bytes and verified identity metadata may be reused, but source selection, annotations, relevance judgments, distillates, and Composite Authors must be rebuilt and stored per paper.

## Safe removal and restoration

Treat removal as an explicit state-changing command. Never remove the active paper merely because the user said “this one”; require a named alias. Use this sequence:

1. Run `resolve @<alias>` and retain the returned `paper_id`.
2. Run `remove @<alias> --paper-id <exact-paper-id>`.
3. Report the returned `removal_id`, archive location, recovery status, and active-paper state.

The helper verifies registry and namespace ownership before mutation. It journals the original registry entry, moves the entire namespace to `.papertalk/trash/<removal-id>/namespace`, removes only that alias from the registry, and clears `active_paper` if it matched. It never auto-selects another paper. A stale or mismatched `paper_id` changes nothing.

Removal is recoverable:

```text
removed
restore <removal-id>
restore <removal-id> --activate
```

Restore revalidates the archived identity and source ownership. It refuses to overwrite an existing alias or merge with an existing namespace. By default it preserves the current active pointer; `--activate` explicitly selects the restored paper. The journal remains after restoration as an audit record, while the namespace moves back under `papers/<alias>`.

Do not manually delete trash archives. Permanent purging and automated retention are not implemented. Recovery remains possible only while the archive is retained.

## Comparison boundary

v0.1 does not implement cross-paper comparison. Resolve exactly one alias for every analysis request. If comparison is requested, explain that it is deferred to v0.2 rather than loading multiple namespaces into one context.

The future comparison workflow must resolve and verify each alias independently, compare labeled read-only snapshots, and never write normalized concepts into either namespace. Non-Author comparison modes must not access either paper's author research.

v0.1 does not automate replacement. Do not rebind an alias unless the user explicitly requests that state change and the implementation has a targeted, recoverable procedure. Removal and restoration must use the helper above rather than manual filesystem or registry edits.
