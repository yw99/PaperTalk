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
resolve [alias]          Resolve an explicit alias, active alias, or sole paper
verify [alias]           Verify registry and namespace ownership
```

Aliases may be written with or without `@`. They normalize to lowercase and must contain only letters, digits, and internal hyphens. `add` rejects collisions.

For a local file, v0.1 fingerprints its bytes. For a URL, v0.1 fingerprints the normalized URL string; remote-content refresh is deferred. The helper creates:

```text
.papertalk/
├── registry.json
└── papers/<alias>/
    ├── identity.json
    ├── source.json
    ├── paper-model.md
    ├── author-research/individuals/
    ├── conversation-state/
    └── cache/
```

## Required isolation

Every derived object is owned by `(alias, paper_id)`. Always call `resolve` or `verify` before reading or writing persistent paper state, and use the namespace path returned by the helper. Do not assemble a path from unvalidated user input.

Never retrieve all paper directories and filter afterward. Never key a derived object only by a symbol, author, theorem number, URL, or question. The active paper is only a pointer; it contains no paper content or conversation state.

An explicit `@alias` scopes one request and does not change the active paper. `use @alias` changes the pointer without importing working memory from the previously active paper. After a switch, unresolved phrases such as “that theorem” must resolve inside the new namespace or trigger clarification.

The same author or source may occur in several papers. Raw immutable source bytes and verified identity metadata may be reused, but source selection, annotations, relevance judgments, distillates, and Composite Authors must be rebuilt and stored per paper.

## Comparison boundary

v0.1 does not implement cross-paper comparison. Resolve exactly one alias for every analysis request. If comparison is requested, explain that it is deferred to v0.2 rather than loading multiple namespaces into one context.

The future comparison workflow must resolve and verify each alias independently, compare labeled read-only snapshots, and never write normalized concepts into either namespace. Non-Author comparison modes must not access either paper's author research.

v0.1 does not automate removal or replacement. Do not delete or rebind an alias unless the user explicitly requests that state change and the implementation has a targeted, recoverable procedure.
