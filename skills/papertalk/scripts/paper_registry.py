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
REMOVAL_ID_RE = re.compile(
    r"^[0-9]{8}T[0-9]{12}Z--[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?--[a-f0-9]{12}$"
)


class RegistryError(Exception):
    """A user-facing registry or ownership error."""


def emit(payload: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, indent=2, sort_keys=True)
    stream.write("\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_removal_id(alias: str, paper_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fingerprint = paper_id.removeprefix("sha256:")[:12]
    return f"{timestamp}--{alias}--{fingerprint}"


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


def removal_archive_for(root: Path, removal_id: str) -> Path:
    if not REMOVAL_ID_RE.fullmatch(removal_id):
        raise RegistryError("Invalid removal_id.")
    trash = (root / "trash").resolve()
    archive = (trash / removal_id).resolve()
    if archive.parent != trash:
        raise RegistryError("Resolved removal archive escaped the trash directory.")
    return archive


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
        "---\n"
        "owner:\n"
        f"  alias: {entry['alias']}\n"
        f"  paper_id: {entry['paper_id']}\n"
        "---\n\n"
        "# Shared Paper Model\n\n"
        "Status: not built. Populate lazily from the registered source.\n"
    )
    (namespace / "paper-model.md").write_text(model, encoding="utf-8")
    from paper_artifacts import initialize_artifact_scaffold

    initialize_artifact_scaffold(namespace, owner_payload(entry))
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


def validate_archived_entry(
    archived_namespace: Path, alias: str, entry: dict[str, Any]
) -> None:
    expected_relative = f"papers/{alias}"
    paper_id = entry.get("paper_id")
    if entry.get("alias") != alias or entry.get("namespace") != expected_relative:
        raise RegistryError(f"Archived registry entry mismatch for @{alias}.")
    if not isinstance(paper_id, str) or not paper_id.startswith("sha256:"):
        raise RegistryError(f"Invalid archived paper_id for @{alias}.")

    identity = read_json(archived_namespace / "identity.json")
    if identity.get("alias") != alias or identity.get("paper_id") != paper_id:
        raise RegistryError(f"Archived namespace owner mismatch for @{alias}.")
    if identity.get("source_fingerprint") != entry.get("source_fingerprint"):
        raise RegistryError(f"Archived source fingerprint mismatch for @{alias}.")

    source = read_json(archived_namespace / "source.json")
    if source.get("owner") != {"alias": alias, "paper_id": paper_id}:
        raise RegistryError(f"Archived source owner mismatch for @{alias}.")


def command_remove(
    root: Path, raw_alias: str, expected_paper_id: str
) -> dict[str, Any]:
    """Move one verified namespace to recoverable trash, then unregister it."""
    alias = normalize_alias(raw_alias)
    registry = load_registry(root)
    if alias not in registry["papers"]:
        raise RegistryError(f"Alias @{alias} is not registered.")
    entry = registry["papers"][alias]
    resolved = validate_entry(root, alias, entry)
    if expected_paper_id != resolved["paper_id"]:
        raise RegistryError(
            f"paper_id confirmation mismatch for @{alias}; no state was changed."
        )

    namespace = namespace_for(root, alias)
    removal_id = new_removal_id(alias, resolved["paper_id"])
    archive = removal_archive_for(root, removal_id)
    archived_namespace = archive / "namespace"
    try:
        archive.mkdir(parents=True, exist_ok=False)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "removal_id": removal_id,
            "status": "pending",
            "owner": owner_payload(entry),
            "removed_at": now_utc(),
            "previously_active": registry["active_paper"] == alias,
            "original_entry": entry,
            "original_namespace": entry["namespace"],
        }
        atomic_write_json(archive / "removal.json", manifest)
        os.replace(namespace, archived_namespace)
    except OSError as exc:
        if archive.exists():
            try:
                failed_manifest = locals().get("manifest", {})
                if isinstance(failed_manifest, dict) and failed_manifest:
                    failed_manifest["status"] = "aborted"
                    failed_manifest["error"] = str(exc)
                    atomic_write_json(archive / "removal.json", failed_manifest)
            except OSError:
                pass
        raise RegistryError(f"Could not archive @{alias}; no registry entry was removed: {exc}") from exc

    del registry["papers"][alias]
    if registry["active_paper"] == alias:
        registry["active_paper"] = None
    try:
        atomic_write_json(registry_path(root), registry)
    except OSError as exc:
        try:
            os.replace(archived_namespace, namespace)
            manifest["status"] = "aborted"
            manifest["error"] = f"Registry update failed and namespace was restored: {exc}"
            atomic_write_json(archive / "removal.json", manifest)
        except OSError as rollback_exc:
            raise RegistryError(
                f"Registry update and automatic rollback failed for @{alias}. "
                f"Recovery archive: {archive}. Error: {rollback_exc}"
            ) from exc
        raise RegistryError(
            f"Registry update failed for @{alias}; the namespace was restored."
        ) from exc

    warning = None
    manifest["status"] = "removed"
    manifest["active_paper_after"] = registry["active_paper"]
    try:
        atomic_write_json(archive / "removal.json", manifest)
    except OSError as exc:
        warning = f"Removal succeeded, but the journal remained pending: {exc}"

    result = {
        "status": "removed",
        "owner": owner_payload(entry),
        "active_paper": registry["active_paper"],
        "removal_id": removal_id,
        "archive": str(archive),
        "recoverable": archived_namespace.is_dir(),
    }
    if warning:
        result["warning"] = warning
    return result


def command_removed(root: Path) -> dict[str, Any]:
    trash = (root / "trash").resolve()
    removals = []
    if trash.is_dir():
        for archive in sorted(path for path in trash.iterdir() if path.is_dir()):
            manifest = read_json(archive / "removal.json")
            removal_id = manifest.get("removal_id")
            if archive.name != removal_id or not isinstance(removal_id, str):
                raise RegistryError(f"Removal journal mismatch in {archive}.")
            removal_archive_for(root, removal_id)
            removals.append(
                {
                    "removal_id": removal_id,
                    "status": manifest.get("status"),
                    "owner": manifest.get("owner"),
                    "removed_at": manifest.get("removed_at"),
                    "restored_at": manifest.get("restored_at"),
                    "restorable": (archive / "namespace").is_dir()
                    and manifest.get("status") in {"pending", "removed"},
                }
            )
    return {"removals": removals}


def command_restore(root: Path, removal_id: str, *, activate: bool) -> dict[str, Any]:
    """Restore one archived namespace without overwriting a current alias."""
    archive = removal_archive_for(root, removal_id)
    manifest_path = archive / "removal.json"
    manifest = read_json(manifest_path)
    if manifest.get("removal_id") != removal_id:
        raise RegistryError("Removal journal does not match the requested removal_id.")
    if manifest.get("status") not in {"pending", "removed"}:
        raise RegistryError(f"Removal {removal_id} is not restorable.")
    owner = manifest.get("owner")
    entry = manifest.get("original_entry")
    if not isinstance(owner, dict) or not isinstance(entry, dict):
        raise RegistryError("Removal journal is missing its owner or original entry.")
    if not isinstance(owner.get("alias"), str):
        raise RegistryError("Removal journal owner has an invalid alias.")
    alias = normalize_alias(owner["alias"])
    expected_owner = {"alias": entry.get("alias"), "paper_id": entry.get("paper_id")}
    if expected_owner != owner:
        raise RegistryError("Removal journal owner does not match its original entry.")

    target = namespace_for(root, alias)
    registry = load_registry(root)
    existing = registry["papers"].get(alias)
    archived_namespace = archive / "namespace"
    archived_exists = archived_namespace.is_dir()
    target_exists = target.is_dir()

    if existing is not None and existing != entry:
        raise RegistryError(
            f"Alias @{alias} is already registered; refusing to overwrite it during restore."
        )
    if archived_exists and target_exists:
        raise RegistryError(
            f"Both live and archived namespaces exist for @{alias}; refusing to merge them."
        )
    if target.exists() and not target_exists:
        raise RegistryError(
            f"A non-directory namespace exists for @{alias}; refusing to overwrite it."
        )

    recovered_interrupted_transaction = False
    moved_from_archive = False
    if target_exists:
        validate_archived_entry(target, alias, entry)
        recovered_interrupted_transaction = True
    elif archived_exists:
        validate_archived_entry(archived_namespace, alias, entry)
        try:
            os.replace(archived_namespace, target)
            moved_from_archive = True
        except OSError as exc:
            raise RegistryError(f"Could not restore @{alias}: {exc}") from exc
    else:
        raise RegistryError(f"Removal {removal_id} has no namespace to restore.")

    if existing is None:
        registry["papers"][alias] = entry
    if activate:
        registry["active_paper"] = alias
    try:
        atomic_write_json(registry_path(root), registry)
    except OSError as exc:
        if moved_from_archive:
            try:
                os.replace(target, archived_namespace)
            except OSError as rollback_exc:
                raise RegistryError(
                    f"Restore registry update and automatic rollback failed for @{alias}. "
                    f"Namespace location: {target}. Error: {rollback_exc}"
                ) from exc
        raise RegistryError(
            f"Restore registry update failed for @{alias}; "
            + (
                "the namespace was returned to trash."
                if moved_from_archive
                else "the recovered namespace remains in place for another retry."
            )
        ) from exc

    warning = None
    manifest["status"] = "restored"
    manifest["restored_at"] = now_utc()
    manifest["activated"] = activate
    manifest["active_paper_after"] = registry["active_paper"]
    try:
        atomic_write_json(manifest_path, manifest)
    except OSError as exc:
        warning = f"Restore succeeded, but the journal could not be finalized: {exc}"

    result = {
        "status": "restored",
        "owner": owner,
        "active_paper": registry["active_paper"],
        "removal_id": removal_id,
        "namespace": str(target),
        "recovered_interrupted_transaction": recovered_interrupted_transaction,
    }
    if warning:
        result["warning"] = warning
    return result


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

    remove_parser = subparsers.add_parser(
        "remove", help="Archive one exact paper namespace and unregister its alias"
    )
    remove_parser.add_argument("alias")
    remove_parser.add_argument(
        "--paper-id",
        required=True,
        help="Exact paper_id returned by resolve; prevents stale-alias removal",
    )

    subparsers.add_parser("removed", help="List recoverable removal archives")

    restore_parser = subparsers.add_parser(
        "restore", help="Restore one removal archive without overwriting an alias"
    )
    restore_parser.add_argument("removal_id")
    restore_parser.add_argument(
        "--activate", action="store_true", help="Make the restored paper active"
    )

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
        elif args.command == "remove":
            result = command_remove(root, args.alias, args.paper_id)
        elif args.command == "removed":
            result = command_removed(root)
        elif args.command == "restore":
            result = command_restore(root, args.removal_id, activate=args.activate)
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
