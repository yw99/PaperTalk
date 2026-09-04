#!/usr/bin/env python3
"""Minimal, fail-closed registry for PaperTalk v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 1
ALIAS_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class RegistryError(Exception):
    """A user-facing registry or ownership error."""


def emit(payload: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_alias(raw: str) -> str:
    alias = raw.strip()
    if alias.startswith("@"):
        alias = alias[1:]
    alias = alias.lower()
    if not ALIAS_RE.fullmatch(alias):
        raise RegistryError(
            "Alias must be 1-63 characters using lowercase letters, digits, "
            "and internal hyphens."
        )
    return alias


def hash_bytes(chunks: Any) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def fingerprint_file(path: Path) -> str:
    def chunks() -> Any:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    return hash_bytes(chunks())


def normalize_url(source: str) -> str:
    parts = urlsplit(source.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise RegistryError("URL sources must use http or https and include a host.")
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path or "/",
            parts.query,
            "",
        )
    )


def describe_source(source: str) -> dict[str, str]:
    stripped = source.strip()
    if stripped.lower().startswith(("http://", "https://")):
        normalized = normalize_url(stripped)
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return {
            "kind": "url",
            "source": stripped,
            "resolved_source": normalized,
            "fingerprint_method": "sha256-normalized-url-v1",
            "source_fingerprint": fingerprint,
        }

    if stripped.lower().startswith("doi:"):
        normalized = stripped[4:].strip().lower()
        if not normalized.startswith("10.") or "/" not in normalized:
            raise RegistryError("DOI sources must look like doi:10.<registrant>/<suffix>.")
        fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return {
            "kind": "doi",
            "source": stripped,
            "resolved_source": f"doi:{normalized}",
            "fingerprint_method": "sha256-normalized-doi-v1",
            "source_fingerprint": fingerprint,
        }

    path = Path(stripped).expanduser().resolve()
    if not path.is_file():
        raise RegistryError(
            "Source must be an existing local file, an HTTP(S) URL, or a DOI."
        )
    fingerprint = fingerprint_file(path)
    return {
        "kind": "file",
        "source": stripped,
        "resolved_source": str(path),
        "fingerprint_method": "sha256-file-bytes-v1",
        "source_fingerprint": fingerprint,
    }


def default_registry() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "active_paper": None, "papers": {}}


def state_root(raw_root: str | None) -> Path:
    configured = raw_root or os.environ.get("PAPERTALK_STATE_DIR") or ".papertalk"
    return Path(configured).expanduser().resolve()


def registry_path(root: Path) -> Path:
    return root / "registry.json"


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"Missing required state file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegistryError(f"Expected a JSON object in {path}.")
    return value


def load_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        return default_registry()
    registry = read_json(path)
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise RegistryError("Unsupported registry schema version.")
    if not isinstance(registry.get("papers"), dict):
        raise RegistryError("Registry field 'papers' must be an object.")
    active = registry.get("active_paper")
    if active is not None and active not in registry["papers"]:
        raise RegistryError("Active paper points to an unregistered alias.")
    return registry


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def namespace_for(root: Path, alias: str) -> Path:
    base = (root / "papers").resolve()
    namespace = (base / alias).resolve()
    if namespace.parent != base:
        raise RegistryError("Resolved namespace escaped the paper state directory.")
    return namespace


def owner_payload(entry: dict[str, Any]) -> dict[str, str]:
    return {"alias": entry["alias"], "paper_id": entry["paper_id"]}


def initialize_namespace(root: Path, entry: dict[str, Any]) -> Path:
    namespace = namespace_for(root, entry["alias"])
    if namespace.exists():
        raise RegistryError(
            f"Namespace already exists for @{entry['alias']}; refusing to merge state."
        )

    (namespace / "author-research" / "individuals").mkdir(parents=True)
    (namespace / "conversation-state").mkdir()
    (namespace / "cache").mkdir()

    identity = {
        "schema_version": SCHEMA_VERSION,
        **owner_payload(entry),
        "source_fingerprint": entry["source_fingerprint"],
    }
    source = {
        "schema_version": SCHEMA_VERSION,
        "owner": owner_payload(entry),
        "kind": entry["source_kind"],
        "source": entry["source"],
        "resolved_source": entry["resolved_source"],
        "fingerprint_method": entry["fingerprint_method"],
        "source_fingerprint": entry["source_fingerprint"],
    }
    atomic_write_json(namespace / "identity.json", identity)
    atomic_write_json(namespace / "source.json", source)

    model = (
        "# Shared Paper Model\n\n"
        f"Owner: `@{entry['alias']}` / `{entry['paper_id']}`\n\n"
        "Status: not built. Populate lazily from the registered source.\n"
    )
    (namespace / "paper-model.md").write_text(model, encoding="utf-8")
    return namespace


def validate_entry(root: Path, alias: str, entry: dict[str, Any]) -> dict[str, Any]:
    expected_namespace = namespace_for(root, alias)
    expected_relative = f"papers/{alias}"
    if entry.get("alias") != alias:
        raise RegistryError(f"Registry alias mismatch for @{alias}.")
    if entry.get("namespace") != expected_relative:
        raise RegistryError(f"Registry namespace mismatch for @{alias}.")
    paper_id = entry.get("paper_id")
    if not isinstance(paper_id, str) or not paper_id.startswith("sha256:"):
        raise RegistryError(f"Invalid paper_id for @{alias}.")

    identity = read_json(expected_namespace / "identity.json")
    if identity.get("alias") != alias or identity.get("paper_id") != paper_id:
        raise RegistryError(f"Namespace owner mismatch for @{alias}.")
    if identity.get("source_fingerprint") != entry.get("source_fingerprint"):
        raise RegistryError(f"Source fingerprint mismatch for @{alias}.")

    source = read_json(expected_namespace / "source.json")
    if source.get("owner") != {"alias": alias, "paper_id": paper_id}:
        raise RegistryError(f"Source owner mismatch for @{alias}.")

    return {
        "alias": alias,
        "paper_id": paper_id,
        "namespace": str(expected_namespace),
        "namespace_relative": expected_relative,
        "source": entry.get("source"),
        "resolved_source": entry.get("resolved_source"),
        "source_kind": entry.get("source_kind"),
    }


def command_add(root: Path, raw_alias: str, source: str) -> dict[str, Any]:
    alias = normalize_alias(raw_alias)
    registry = load_registry(root)
    if alias in registry["papers"]:
        raise RegistryError(f"Alias @{alias} is already registered.")

    descriptor = describe_source(source)
    entry = {
        "alias": alias,
        "paper_id": f"sha256:{descriptor['source_fingerprint']}",
        "namespace": f"papers/{alias}",
        "source": descriptor["source"],
        "resolved_source": descriptor["resolved_source"],
        "source_kind": descriptor["kind"],
        "fingerprint_method": descriptor["fingerprint_method"],
        "source_fingerprint": descriptor["source_fingerprint"],
        "added_at": now_utc(),
    }

    namespace = initialize_namespace(root, entry)
    registry["papers"][alias] = entry
    if registry["active_paper"] is None:
        registry["active_paper"] = alias
    atomic_write_json(registry_path(root), registry)
    return {
        "status": "added",
        "active_paper": registry["active_paper"],
        **validate_entry(root, alias, entry),
        "namespace": str(namespace),
    }


def command_list(root: Path) -> dict[str, Any]:
    registry = load_registry(root)
    papers = []
    for alias in sorted(registry["papers"]):
        entry = registry["papers"][alias]
        papers.append(
            {
                "alias": alias,
                "paper_id": entry.get("paper_id"),
                "source": entry.get("source"),
                "active": alias == registry["active_paper"],
            }
        )
    return {"active_paper": registry["active_paper"], "papers": papers}


def select_alias(registry: dict[str, Any], raw_alias: str | None) -> str:
    if raw_alias:
        alias = normalize_alias(raw_alias)
    elif registry["active_paper"]:
        alias = registry["active_paper"]
    elif len(registry["papers"]) == 1:
        alias = next(iter(registry["papers"]))
    elif not registry["papers"]:
        raise RegistryError("No papers are registered.")
    else:
        raise RegistryError("Paper scope is ambiguous; specify an alias.")
    if alias not in registry["papers"]:
        raise RegistryError(f"Alias @{alias} is not registered.")
    return alias


def command_resolve(root: Path, raw_alias: str | None) -> dict[str, Any]:
    registry = load_registry(root)
    alias = select_alias(registry, raw_alias)
    resolved = validate_entry(root, alias, registry["papers"][alias])
    return {"active_paper": registry["active_paper"], **resolved}


def command_use(root: Path, raw_alias: str) -> dict[str, Any]:
    registry = load_registry(root)
    alias = select_alias(registry, raw_alias)
    resolved = validate_entry(root, alias, registry["papers"][alias])
    registry["active_paper"] = alias
    atomic_write_json(registry_path(root), registry)
    return {"status": "active", "active_paper": alias, **resolved}


def command_verify(root: Path, raw_alias: str | None) -> dict[str, Any]:
    registry = load_registry(root)
    aliases = [select_alias(registry, raw_alias)] if raw_alias else sorted(registry["papers"])
    verified = [validate_entry(root, alias, registry["papers"][alias]) for alias in aliases]
    return {"status": "verified", "active_paper": registry["active_paper"], "papers": verified}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="State directory; defaults to .papertalk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Register a paper alias")
    add_parser.add_argument("alias")
    add_parser.add_argument("source")

    subparsers.add_parser("list", help="List registered papers")

    use_parser = subparsers.add_parser("use", help="Set the active paper")
    use_parser.add_argument("alias")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve paper scope")
    resolve_parser.add_argument("alias", nargs="?")

    verify_parser = subparsers.add_parser("verify", help="Verify namespace ownership")
    verify_parser.add_argument("alias", nargs="?")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = state_root(args.root)
    try:
        if args.command == "add":
            result = command_add(root, args.alias, args.source)
        elif args.command == "list":
            result = command_list(root)
        elif args.command == "use":
            result = command_use(root, args.alias)
        elif args.command == "resolve":
            result = command_resolve(root, args.alias)
        elif args.command == "verify":
            result = command_verify(root, args.alias)
        else:  # pragma: no cover - argparse enforces the command set.
            raise RegistryError(f"Unsupported command: {args.command}")
    except RegistryError as exc:
        emit({"error": str(exc), "status": "error"}, stream=sys.stderr)
        return 2
    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
