#!/usr/bin/env python3
"""Manage the latest interactive PaperTalk panel for one registered paper."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from paper_artifacts import atomic_write_json, command_context
from paper_registry import command_resolve, state_root


SCHEMA_VERSION = 1
ROLES = ("author", "reviewer", "researcher")
PANEL_STATUSES = {"initializing", "ready", "archived"}
TURN_KINDS = {"initial", "continuation"}
ROLE_PAIR_PATTERN = re.compile(
    r"^\s*(author|reviewer|researcher)\s*:\s*(author|reviewer|researcher)\s*$",
    re.IGNORECASE,
)


class PanelSessionError(Exception):
    """A user-facing panel-session contract error."""


def now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def content_hash(turn: dict[str, Any]) -> str:
    payload = {key: value for key, value in turn.items() if key != "content_hash"}
    return digest(payload)


def panel_hash(panel: dict[str, Any]) -> str:
    return digest(panel)


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise PanelSessionError(f"Expected one JSON object on stdin: {exc}") from exc
    if not isinstance(value, dict):
        raise PanelSessionError("Expected one JSON object on stdin.")
    return value


def resolve(raw_root: str | None, raw_alias: str | None) -> tuple[Path, dict[str, str]]:
    root = state_root(raw_root)
    resolved = command_resolve(root, raw_alias)
    namespace = Path(resolved["namespace"])
    owner = {"alias": resolved["alias"], "paper_id": resolved["paper_id"]}
    return namespace, owner


def state_path(namespace: Path) -> Path:
    return namespace / "conversation-state" / "panel-sessions.json"


@contextmanager
def state_lock(namespace: Path):
    """Serialize state mutations while keeping the JSON update atomic."""
    lock_path = namespace / "conversation-state" / "panel-sessions.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def empty_state(owner: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "owner": owner,
        "next_panel_generation": 1,
        "latest_panel": None,
        "history": [],
    }


def validate_turn(
    turn: Any,
    *,
    owner: dict[str, str],
    members: list[str],
    expected_sequence: int,
    earlier: dict[str, dict[str, Any]],
    location: str,
    errors: list[str],
) -> None:
    if not isinstance(turn, dict):
        errors.append(f"{location}: expected an object")
        return
    if turn.get("owner") != owner:
        errors.append(f"{location}: owner does not match resolved paper")
    expected_id = f"turn-{expected_sequence:04d}"
    if turn.get("turn_id") != expected_id:
        errors.append(f"{location}: turn_id must be '{expected_id}'")
    if turn.get("sequence") != expected_sequence:
        errors.append(f"{location}: sequence must be {expected_sequence}")
    role = turn.get("role")
    if role not in members:
        errors.append(f"{location}: role must be a panel member")
    kind = turn.get("kind")
    if kind not in TURN_KINDS:
        errors.append(f"{location}: invalid turn kind '{kind}'")
    if not nonempty_text(turn.get("body")):
        errors.append(f"{location}: body must be non-empty text")
    if not nonempty_text(turn.get("evidence_footer")):
        errors.append(f"{location}: evidence_footer must be non-empty text")
    if not nonempty_text(turn.get("created_at")):
        errors.append(f"{location}: created_at must be non-empty text")
    if not isinstance(turn.get("guidance"), str):
        errors.append(f"{location}: guidance must be text")
    visible = turn.get("visible_context_turn_ids")
    responds_to = turn.get("responds_to_turn_ids")
    if not isinstance(visible, list) or not all(isinstance(item, str) for item in visible):
        errors.append(f"{location}: visible_context_turn_ids must be a list of turn IDs")
        visible = []
    if not isinstance(responds_to, list) or not all(
        isinstance(item, str) for item in responds_to
    ):
        errors.append(f"{location}: responds_to_turn_ids must be a list of turn IDs")
        responds_to = []
    for referenced in set(visible + responds_to):
        if referenced not in earlier:
            errors.append(f"{location}: referenced turn '{referenced}' is not an earlier turn")
    if kind == "initial":
        if visible or responds_to:
            errors.append(f"{location}: initial turns cannot see or respond to peer turns")
        if turn.get("guidance") != "":
            errors.append(f"{location}: initial turns cannot carry continuation guidance")
    elif kind == "continuation":
        if len(responds_to) != 1 or visible != responds_to:
            errors.append(f"{location}: continuation must see and respond to exactly one turn")
        elif responds_to[0] in earlier and earlier[responds_to[0]].get("role") == role:
            errors.append(f"{location}: responder and target roles must be distinct")
    if turn.get("content_hash") != content_hash(turn):
        errors.append(f"{location}: content_hash does not match the frozen turn")


def validate_panel(
    panel: Any,
    *,
    owner: dict[str, str],
    archived: bool,
    location: str,
    errors: list[str],
) -> None:
    if not isinstance(panel, dict):
        errors.append(f"{location}: expected an object")
        return
    if panel.get("owner") != owner:
        errors.append(f"{location}: owner does not match resolved paper")
    if not isinstance(panel.get("generation"), int) or panel["generation"] < 1:
        errors.append(f"{location}: generation must be a positive integer")
    if not nonempty_text(panel.get("topic")):
        errors.append(f"{location}: topic must be non-empty text")
    members = panel.get("members")
    if (
        not isinstance(members, list)
        or not members
        or len(members) != len(set(members))
        or any(member not in ROLES for member in members)
    ):
        errors.append(f"{location}: members must be a non-empty unique list of panel roles")
        members = []
    status = panel.get("status")
    if status not in PANEL_STATUSES:
        errors.append(f"{location}: invalid status '{status}'")
    if archived and status != "archived":
        errors.append(f"{location}: historical panels must be archived")
    if not archived and status == "archived":
        errors.append(f"{location}: latest panel cannot be archived")
    if not nonempty_text(panel.get("created_at")) or not nonempty_text(panel.get("updated_at")):
        errors.append(f"{location}: created_at and updated_at must be non-empty text")
    if archived:
        if panel.get("archived_from_status") not in {"initializing", "ready"}:
            errors.append(f"{location}: archived_from_status must record the prior status")
        if not nonempty_text(panel.get("archived_at")):
            errors.append(f"{location}: archived_at must be non-empty text")
    turns = panel.get("turns")
    if not isinstance(turns, list):
        errors.append(f"{location}: turns must be a list")
        return
    earlier: dict[str, dict[str, Any]] = {}
    initial_roles: list[str] = []
    for sequence, turn in enumerate(turns, start=1):
        turn_location = f"{location}.turns[{sequence - 1}]"
        validate_turn(
            turn,
            owner=owner,
            members=members,
            expected_sequence=sequence,
            earlier=earlier,
            location=turn_location,
            errors=errors,
        )
        if isinstance(turn, dict):
            turn_id = turn.get("turn_id")
            if isinstance(turn_id, str):
                if turn_id in earlier:
                    errors.append(f"{turn_location}: duplicate turn_id '{turn_id}'")
                earlier[turn_id] = turn
            if turn.get("kind") == "initial" and isinstance(turn.get("role"), str):
                initial_roles.append(turn["role"])
    if len(initial_roles) != len(set(initial_roles)):
        errors.append(f"{location}: each role may have only one initial turn")
    initial_complete = bool(members) and set(initial_roles) == set(members)
    if not archived:
        expected_status = "ready" if initial_complete else "initializing"
        if status != expected_status:
            errors.append(f"{location}: status must be '{expected_status}' for its initial turns")
    if any(turn.get("kind") == "continuation" for turn in turns if isinstance(turn, dict)) and not initial_complete:
        errors.append(f"{location}: continuation turns require every initial member response")


def validate_state_value(state: Any, owner: dict[str, str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["panel state: expected an object"]
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"panel state: schema_version must be {SCHEMA_VERSION}")
    if state.get("owner") != owner:
        errors.append("panel state: owner does not match resolved paper")
    next_generation = state.get("next_panel_generation")
    if not isinstance(next_generation, int) or next_generation < 1:
        errors.append("panel state: next_panel_generation must be a positive integer")
    history = state.get("history")
    if not isinstance(history, list):
        errors.append("panel state: history must be a list")
        history = []
    for index, panel in enumerate(history):
        validate_panel(
            panel,
            owner=owner,
            archived=True,
            location=f"history[{index}]",
            errors=errors,
        )
    latest = state.get("latest_panel")
    if latest is not None:
        validate_panel(latest, owner=owner, archived=False, location="latest_panel", errors=errors)
    panels = [*history, *([latest] if isinstance(latest, dict) else [])]
    generations = [panel.get("generation") for panel in panels if isinstance(panel, dict)]
    if generations != sorted(generations) or len(generations) != len(set(generations)):
        errors.append("panel state: panel generations must be unique and increasing")
    if generations and isinstance(next_generation, int) and next_generation <= generations[-1]:
        errors.append("panel state: next_panel_generation must exceed every stored panel")
    return errors


def load_state(namespace: Path, owner: dict[str, str], *, required: bool) -> dict[str, Any]:
    path = state_path(namespace)
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if required:
            raise PanelSessionError("No latest panel exists for this paper. Start a panel first.")
        return empty_state(owner)
    except json.JSONDecodeError as exc:
        raise PanelSessionError(f"Panel state is invalid JSON: {exc}") from exc
    errors = validate_state_value(state, owner)
    if errors:
        raise PanelSessionError("Panel state validation failed: " + "; ".join(errors))
    return state


def latest_panel(state: dict[str, Any]) -> dict[str, Any]:
    panel = state.get("latest_panel")
    if not isinstance(panel, dict):
        raise PanelSessionError("No latest panel exists for this paper. Start a panel first.")
    return panel


def validate_role(role: str) -> str:
    normalized = role.lower()
    if normalized not in ROLES:
        raise PanelSessionError(f"Unknown panel role '{role}'.")
    return normalized


def parse_role_pair(value: str) -> tuple[str, str]:
    match = ROLE_PAIR_PATTERN.fullmatch(value)
    if match is None:
        raise PanelSessionError(
            "Role pair must be exactly '<responder>:<target>' using Author, Reviewer, or Researcher."
        )
    responder, target = (part.lower() for part in match.groups())
    if responder == target:
        raise PanelSessionError("Responder and target roles must be distinct.")
    return responder, target


def validate_members(value: Any) -> list[str]:
    members = list(ROLES) if value is None else value
    if not isinstance(members, list) or not members:
        raise PanelSessionError("members must be a non-empty list of panel roles.")
    normalized = [validate_role(member) if isinstance(member, str) else "" for member in members]
    if "" in normalized or len(normalized) != len(set(normalized)):
        raise PanelSessionError("members must be a unique list of panel roles.")
    return normalized


def base_role_context(raw_root: str | None, role: str, alias: str) -> dict[str, Any]:
    try:
        return command_context(raw_root, role, alias)
    except Exception as exc:
        if exc.__class__.__name__ in {"ArtifactError", "RegistryError"}:
            raise PanelSessionError(str(exc)) from exc
        raise


def make_context_token(
    panel: dict[str, Any], *, mode: str, role: str, target: str | None = None, guidance: str = ""
) -> str:
    if mode == "initial":
        # Initial roles may be generated in parallel. Other isolated initial
        # responses must not invalidate a role's already-issued token.
        panel_snapshot: Any = {
            "owner": panel["owner"],
            "generation": panel["generation"],
            "topic": panel["topic"],
            "members": panel["members"],
            "created_at": panel["created_at"],
        }
    else:
        panel_snapshot = panel_hash(panel)
    return digest(
        {
            "panel_snapshot": panel_snapshot,
            "mode": mode,
            "role": role,
            "target": target,
            "guidance": guidance,
        }
    )


def command_start(raw_root: str | None, raw_alias: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    topic = payload.get("topic")
    if not nonempty_text(topic):
        raise PanelSessionError("topic must be non-empty text.")
    members = validate_members(payload.get("members"))
    with state_lock(namespace):
        state = load_state(namespace, owner, required=False)
        timestamp = now_utc()
        generation = state["next_panel_generation"]
        current = state.get("latest_panel")
        if isinstance(current, dict):
            archived = copy.deepcopy(current)
            archived["archived_from_status"] = archived["status"]
            archived["status"] = "archived"
            archived["archived_at"] = timestamp
            archived["updated_at"] = timestamp
            state["history"].append(archived)
        state["latest_panel"] = {
            "owner": owner,
            "generation": generation,
            "topic": topic.strip(),
            "members": members,
            "status": "initializing",
            "created_at": timestamp,
            "updated_at": timestamp,
            "turns": [],
        }
        state["next_panel_generation"] = generation + 1
        atomic_write_json(state_path(namespace), state)
    return {
        "status": "started",
        "owner": owner,
        "topic": topic.strip(),
        "members": members,
        "archived_previous": isinstance(current, dict),
    }


def command_initial_context(raw_root: str | None, raw_alias: str | None, role: str) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    role = validate_role(role)
    state = load_state(namespace, owner, required=True)
    panel = latest_panel(state)
    if role not in panel["members"]:
        raise PanelSessionError(f"{role} is not a member of the latest panel.")
    if any(turn["kind"] == "initial" and turn["role"] == role for turn in panel["turns"]):
        raise PanelSessionError(f"{role} already has a frozen initial response.")
    context = base_role_context(raw_root, role, owner["alias"])
    return {
        "status": "allowed",
        "owner": owner,
        "mode": "initial",
        "role": role,
        "topic": panel["topic"],
        "peer_turns": [],
        "allowed_paths": context["allowed_paths"],
        "denied_paths": context["denied_paths"],
        "context_token": make_context_token(panel, mode="initial", role=role),
    }


def append_turn(
    panel: dict[str, Any],
    *,
    owner: dict[str, str],
    role: str,
    kind: str,
    body: Any,
    evidence_footer: Any,
    guidance: str,
    visible: list[str],
    responds_to: list[str],
) -> dict[str, Any]:
    if not nonempty_text(body):
        raise PanelSessionError("body must be non-empty text.")
    if not nonempty_text(evidence_footer):
        raise PanelSessionError("evidence_footer must be non-empty text.")
    sequence = len(panel["turns"]) + 1
    turn = {
        "owner": owner,
        "turn_id": f"turn-{sequence:04d}",
        "sequence": sequence,
        "role": role,
        "kind": kind,
        "body": body.strip(),
        "evidence_footer": evidence_footer.strip(),
        "guidance": guidance,
        "visible_context_turn_ids": visible,
        "responds_to_turn_ids": responds_to,
        "created_at": now_utc(),
    }
    turn["content_hash"] = content_hash(turn)
    panel["turns"].append(turn)
    panel["updated_at"] = turn["created_at"]
    return turn


def command_append_initial(
    raw_root: str | None, raw_alias: str | None, role: str, payload: dict[str, Any]
) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    role = validate_role(role)
    with state_lock(namespace):
        state = load_state(namespace, owner, required=True)
        panel = latest_panel(state)
        if role not in panel["members"]:
            raise PanelSessionError(f"{role} is not a member of the latest panel.")
        if any(turn["kind"] == "initial" and turn["role"] == role for turn in panel["turns"]):
            raise PanelSessionError(f"{role} already has a frozen initial response.")
        expected = make_context_token(panel, mode="initial", role=role)
        if payload.get("context_token") != expected:
            raise PanelSessionError("Initial context token is stale or invalid; reload the role context.")
        turn = append_turn(
            panel,
            owner=owner,
            role=role,
            kind="initial",
            body=payload.get("body"),
            evidence_footer=payload.get("evidence_footer"),
            guidance="",
            visible=[],
            responds_to=[],
        )
        initial_roles = {item["role"] for item in panel["turns"] if item["kind"] == "initial"}
        panel["status"] = "ready" if initial_roles == set(panel["members"]) else "initializing"
        atomic_write_json(state_path(namespace), state)
    return {
        "status": "appended",
        "owner": owner,
        "panel_status": panel["status"],
        "turn": turn,
        "missing_initial_roles": [member for member in panel["members"] if member not in initial_roles],
    }


def latest_role_turn(panel: dict[str, Any], role: str) -> dict[str, Any]:
    for turn in reversed(panel["turns"]):
        if turn["role"] == role:
            return turn
    raise PanelSessionError(f"The target role '{role}' has no answer in the latest panel.")


def continuation_request(payload: dict[str, Any], responder: str) -> tuple[str, str]:
    target = payload.get("target")
    if not isinstance(target, str):
        raise PanelSessionError("target must be one panel role.")
    target = validate_role(target)
    if target == responder:
        raise PanelSessionError("Responder and target roles must be distinct.")
    guidance = payload.get("guidance", "")
    if not isinstance(guidance, str):
        raise PanelSessionError("guidance must be text.")
    return target, guidance


def continuation_context(
    raw_root: str | None,
    raw_alias: str | None,
    responder: str,
    payload: dict[str, Any],
) -> tuple[Path, dict[str, str], dict[str, Any], dict[str, Any], str, str, dict[str, Any]]:
    if raw_alias is None:
        raise PanelSessionError("panel_continue requires an explicit paper alias.")
    namespace, owner = resolve(raw_root, raw_alias)
    responder = validate_role(responder)
    target, guidance = continuation_request(payload, responder)
    state = load_state(namespace, owner, required=True)
    panel = latest_panel(state)
    if panel["status"] != "ready":
        raise PanelSessionError("The latest panel is incomplete; finish all initial responses first.")
    if responder not in panel["members"] or target not in panel["members"]:
        raise PanelSessionError("Responder and target must both be members of the latest panel.")
    target_turn = latest_role_turn(panel, target)
    return namespace, owner, state, panel, target, guidance, target_turn


def command_continue_context(
    raw_root: str | None, raw_alias: str | None, responder: str, payload: dict[str, Any]
) -> dict[str, Any]:
    _, owner, _, panel, target, guidance, target_turn = continuation_context(
        raw_root, raw_alias, responder, payload
    )
    responder = validate_role(responder)
    context = base_role_context(raw_root, responder, owner["alias"])
    return {
        "status": "allowed",
        "owner": owner,
        "mode": "continuation",
        "responder": responder,
        "target": target,
        "topic": panel["topic"],
        "guidance": guidance,
        "peer_turn": {
            "turn_id": target_turn["turn_id"],
            "role": target_turn["role"],
            "body": target_turn["body"],
            "peer_claim_only": True,
        },
        "allowed_paths": context["allowed_paths"],
        "denied_paths": context["denied_paths"],
        "context_token": make_context_token(
            panel, mode="continuation", role=responder, target=target, guidance=guidance
        ),
    }


def command_append_continuation(
    raw_root: str | None, raw_alias: str | None, responder: str, payload: dict[str, Any]
) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    responder = validate_role(responder)
    with state_lock(namespace):
        _, locked_owner, state, panel, target, guidance, target_turn = continuation_context(
            raw_root, raw_alias, responder, payload
        )
        if locked_owner != owner:
            raise PanelSessionError("Panel owner changed while acquiring the state lock.")
        expected = make_context_token(
            panel, mode="continuation", role=responder, target=target, guidance=guidance
        )
        if payload.get("context_token") != expected:
            raise PanelSessionError("Continuation context token is stale or invalid; reload the context.")
        turn = append_turn(
            panel,
            owner=owner,
            role=responder,
            kind="continuation",
            body=payload.get("body"),
            evidence_footer=payload.get("evidence_footer"),
            guidance=guidance,
            visible=[target_turn["turn_id"]],
            responds_to=[target_turn["turn_id"]],
        )
        atomic_write_json(state_path(namespace), state)
    return {"status": "appended", "owner": owner, "target": target, "turn": turn}


def command_show(raw_root: str | None, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    state = load_state(namespace, owner, required=True)
    return {"status": "ok", "owner": owner, "latest_panel": latest_panel(state)}


def command_show_history(raw_root: str | None, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    state = load_state(namespace, owner, required=False)
    return {"status": "ok", "owner": owner, "history": state["history"]}


def command_validate(raw_root: str | None, raw_alias: str | None) -> dict[str, Any]:
    namespace, owner = resolve(raw_root, raw_alias)
    path = state_path(namespace)
    if not path.exists():
        return {"status": "valid", "owner": owner, "exists": False, "errors": []}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"status": "invalid", "owner": owner, "exists": True, "errors": [str(exc)]}
    errors = validate_state_value(state, owner)
    return {
        "status": "valid" if not errors else "invalid",
        "owner": owner,
        "exists": True,
        "history_count": len(state.get("history", [])) if isinstance(state, dict) else 0,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="State directory; defaults to .papertalk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_pair = subparsers.add_parser("parse-pair", help="Validate one responder:target pair")
    parse_pair.add_argument("pair")

    start = subparsers.add_parser("start", help="Start the latest panel; read topic JSON on stdin")
    start.add_argument("alias", nargs="?")

    initial_context = subparsers.add_parser("initial-context", help="Get isolated initial role context")
    initial_context.add_argument("role")
    initial_context.add_argument("alias", nargs="?")

    append_initial = subparsers.add_parser("append-initial", help="Freeze an initial role response")
    append_initial.add_argument("role")
    append_initial.add_argument("alias", nargs="?")

    continue_context = subparsers.add_parser(
        "continue-context", help="Get context for one responder:target continuation"
    )
    continue_context.add_argument("responder")
    continue_context.add_argument("alias")

    append_continuation = subparsers.add_parser(
        "append-continuation", help="Freeze one targeted continuation response"
    )
    append_continuation.add_argument("responder")
    append_continuation.add_argument("alias")

    show = subparsers.add_parser("show", help="Show the latest panel")
    show.add_argument("alias", nargs="?")

    show_history = subparsers.add_parser("show-history", help="Show read-only archived panels")
    show_history.add_argument("alias", nargs="?")

    validate = subparsers.add_parser("validate", help="Validate panel state")
    validate.add_argument("alias", nargs="?")
    return parser


def emit(value: dict[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True)
    stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "parse-pair":
            responder, target = parse_role_pair(args.pair)
            result = {"status": "valid", "responder": responder, "target": target}
        elif args.command == "start":
            result = command_start(args.root, args.alias, read_payload())
        elif args.command == "initial-context":
            result = command_initial_context(args.root, args.alias, args.role)
        elif args.command == "append-initial":
            result = command_append_initial(args.root, args.alias, args.role, read_payload())
        elif args.command == "continue-context":
            result = command_continue_context(args.root, args.alias, args.responder, read_payload())
        elif args.command == "append-continuation":
            result = command_append_continuation(
                args.root, args.alias, args.responder, read_payload()
            )
        elif args.command == "show":
            result = command_show(args.root, args.alias)
        elif args.command == "show-history":
            result = command_show_history(args.root, args.alias)
        elif args.command == "validate":
            result = command_validate(args.root, args.alias)
            if result["status"] != "valid":
                emit(result, stream=sys.stderr)
                return 2
        else:  # pragma: no cover
            raise PanelSessionError(f"Unsupported command: {args.command}")
    except Exception as exc:
        if not isinstance(exc, PanelSessionError) and exc.__class__.__name__ != "RegistryError":
            raise
        emit({"status": "error", "error": str(exc)}, stream=sys.stderr)
        return 2
    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
