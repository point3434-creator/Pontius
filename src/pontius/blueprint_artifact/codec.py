"""Strict deterministic byte codec for immutable blueprint action sources."""

from __future__ import annotations

import json

from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
)
from pontius.no_limit_betting import (
    BettingAction,
    BettingActionKind,
    BettingActionRecord,
    BettingStreet,
)


_ARTIFACT_VERSION = "pontius-v0a-blueprint-artifact-v1"
_KEY_VERSION = "blueprint-decision-key-v1"
_INTEGER_LIMIT = 10**640
_ROOT_FIELDS = frozenset({"version", "source_id", "entries"})
_ENTRY_FIELDS = frozenset({"key", "action"})
_ACTION_FIELDS = frozenset({"kind", "raise_to"})
_KEY_FIELDS = frozenset({
    "version", "controlled_seat", "private_hand", "board", "button",
    "small_blind", "big_blind", "street", "starting_stacks", "stacks",
    "total_contributions", "street_contributions", "folded", "pending_seats",
    "last_full_raise_size", "acted_at_bet", "public_history",
})


class BlueprintArtifactError(ValueError):
    """The complete external artifact or exact source graph was refused."""


def _refuse(path: str, reason: str) -> None:
    raise BlueprintArtifactError(f"{path}: {reason}")


def _object(value: object, fields: frozenset[str], path: str) -> dict[str, object]:
    if type(value) is not dict:
        _refuse(path, "must be an object")
    assert isinstance(value, dict)
    if set(value) != fields:
        _refuse(path, "has missing or unknown members")
    return value


def _sequence(value: object, path: str, *, wire: bool,
              width: int | None = None) -> list[object] | tuple[object, ...]:
    expected = list if wire else tuple
    if type(value) is not expected:
        _refuse(path, "must be an array" if wire else "must be an exact tuple")
    assert isinstance(value, (list, tuple))
    if width is not None and len(value) != width:
        _refuse(path, "has the wrong width")
    return value


def _text(value: object, path: str) -> str:
    if type(value) is not str:
        _refuse(path, "must be a string")
    assert isinstance(value, str)
    if any("\ud800" <= character <= "\udfff" for character in value):
        _refuse(path, "must contain only Unicode scalar values")
    return value


def _integer(value: object, path: str, *, lower: int = 0,
             upper: int | None = None) -> int:
    if type(value) is not int:
        _refuse(path, "must be an exact integer")
    assert isinstance(value, int)
    if value < lower or value >= _INTEGER_LIMIT or (upper is not None and value >= upper):
        _refuse(path, "is outside the admitted integer range")
    return value


def _label(value: object, kind: type[BettingStreet] | type[BettingActionKind],
           path: str) -> BettingStreet | BettingActionKind:
    text = _text(value, path)
    try:
        return kind(text)
    except ValueError as error:
        raise BlueprintArtifactError(f"{path}: unsupported label") from error


def _integers(value: object, path: str, *, wire: bool, width: int | None = None,
              lower: int = 0, upper: int | None = None) -> tuple[int, ...]:
    items = _sequence(value, path, wire=wire, width=width)
    return tuple(_integer(item, f"{path}[{index}]", lower=lower, upper=upper)
                 for index, item in enumerate(items))


def _history(value: object, path: str, *, wire: bool) -> tuple[tuple[object, ...], ...]:
    rows = _sequence(value, path, wire=wire)
    admitted = []
    for index, raw in enumerate(rows):
        item = f"{path}[{index}]"
        row = _sequence(raw, item, wire=wire, width=8)
        street = _label(row[0], BettingStreet, f"{item}[0]")
        seat = _integer(row[1], f"{item}[1]", upper=6)
        kind = _label(row[2], BettingActionKind, f"{item}[2]")
        raise_to = (None if row[3] is None else
                    _integer(row[3], f"{item}[3]", lower=1))
        chips = _integer(row[4], f"{item}[4]")
        if type(row[5]) is not bool:
            _refuse(f"{item}[5]", "must be an exact boolean")
        return_seat = (None if row[6] is None else
                       _integer(row[6], f"{item}[6]", upper=6))
        return_chips = _integer(row[7], f"{item}[7]")
        action = BettingAction(kind, raise_to)
        BettingActionRecord(street, seat, action, chips, row[5], return_seat, return_chips)
        admitted.append((street.value, seat, kind.value, raise_to, chips,
                         row[5], return_seat, return_chips))
    return tuple(admitted)


def _key(value: object, path: str, *, wire: bool) -> tuple[BlueprintDecisionKey, dict]:
    if wire:
        data = _object(value, _KEY_FIELDS, path)
        get = data.__getitem__
    else:
        if type(value) is not BlueprintDecisionKey:
            _refuse(path, "must be an exact BlueprintDecisionKey")
        get = lambda name: getattr(value, name)
    if _text(get("version"), f"{path}.version") != _KEY_VERSION if wire else False:
        _refuse(f"{path}.version", "unsupported version")
    street_value = get("street")
    if wire:
        street = _label(street_value, BettingStreet, f"{path}.street")
    elif type(street_value) is BettingStreet:
        street = street_value
    else:
        _refuse(f"{path}.street", "must be an exact BettingStreet")
    private = _integers(get("private_hand"), f"{path}.private_hand", wire=wire,
                        width=2, upper=52)
    board = _integers(get("board"), f"{path}.board", wire=wire, upper=52)
    six_positive = {
        name: _integers(get(name), f"{path}.{name}", wire=wire, width=6, lower=1)
        for name in ("starting_stacks",)
    }
    six_nonnegative = {
        name: _integers(get(name), f"{path}.{name}", wire=wire, width=6)
        for name in ("stacks", "total_contributions", "street_contributions")
    }
    folded_raw = _sequence(get("folded"), f"{path}.folded", wire=wire, width=6)
    if any(type(item) is not bool for item in folded_raw):
        _refuse(f"{path}.folded", "must contain exact booleans")
    acted_raw = _sequence(get("acted_at_bet"), f"{path}.acted_at_bet",
                          wire=wire, width=6)
    acted = tuple(None if item is None else _integer(item, f"{path}.acted_at_bet")
                  for item in acted_raw)
    values = dict(
        controlled_seat=_integer(get("controlled_seat"), f"{path}.controlled_seat", upper=6),
        private_hand=private, board=board,
        button=_integer(get("button"), f"{path}.button", upper=6),
        small_blind=_integer(get("small_blind"), f"{path}.small_blind", lower=1),
        big_blind=_integer(get("big_blind"), f"{path}.big_blind", lower=1),
        street=street, **six_positive, **six_nonnegative, folded=tuple(folded_raw),
        pending_seats=_integers(get("pending_seats"), f"{path}.pending_seats",
                                wire=wire, upper=6),
        last_full_raise_size=_integer(get("last_full_raise_size"),
                                      f"{path}.last_full_raise_size", lower=1),
        acted_at_bet=acted,
        public_history=_history(get("public_history"), f"{path}.public_history", wire=wire),
    )
    rebuilt = BlueprintDecisionKey(**values)
    if not wire and rebuilt != value:
        _refuse(path, "is not a canonical exact key graph")
    document = {"version": _KEY_VERSION, **{
        name: (item.value if isinstance(item, BettingStreet) else item)
        for name, item in values.items()
    }}
    return rebuilt, document


def _action(value: object, path: str, *, wire: bool) -> tuple[BettingAction, dict]:
    if wire:
        data = _object(value, _ACTION_FIELDS, path)
        kind = _label(data["kind"], BettingActionKind, f"{path}.kind")
        raw_raise = data["raise_to"]
    else:
        if type(value) is not BettingAction:
            _refuse(path, "must be an exact BettingAction")
        kind, raw_raise = value.kind, value.raise_to
        if type(kind) is not BettingActionKind:
            _refuse(f"{path}.kind", "must be an exact BettingActionKind")
    raise_amount = (None if raw_raise is None else
                    _integer(raw_raise, f"{path}.raise_to", lower=1))
    rebuilt = BettingAction(kind, raise_amount)
    if not wire and rebuilt != value:
        _refuse(path, "is not a canonical exact action graph")
    return rebuilt, {"kind": kind.value, "raise_to": raise_amount}


def _admit(document: object, *, wire: bool) -> tuple[ImmutableBlueprintActionSource, dict]:
    if wire:
        root = _object(document, _ROOT_FIELDS, "root")
        if _text(root["version"], "root.version") != _ARTIFACT_VERSION:
            _refuse("root.version", "unsupported version")
        source_id, raw_entries = _text(root["source_id"], "root.source_id"), root["entries"]
    else:
        if type(document) is not ImmutableBlueprintActionSource:
            _refuse("source", "must be an exact ImmutableBlueprintActionSource")
        source_id = _text(document.source_id, "source.source_id")
        raw_entries = document.entries
    if not source_id.strip():
        _refuse("source_id", "must contain a non-whitespace character")
    entries = _sequence(raw_entries, "entries", wire=wire)
    admitted, serialized = [], []
    for index, raw in enumerate(entries):
        path = f"entries[{index}]"
        if wire:
            item = _object(raw, _ENTRY_FIELDS, path)
            raw_key, raw_action = item["key"], item["action"]
        else:
            if type(raw) is not BlueprintActionEntry:
                _refuse(path, "must be an exact BlueprintActionEntry")
            raw_key, raw_action = raw.key, raw.action
        key, key_document = _key(raw_key, f"{path}.key", wire=wire)
        action, action_document = _action(raw_action, f"{path}.action", wire=wire)
        admitted.append(BlueprintActionEntry(key, action))
        serialized.append((key, {"key": key_document, "action": action_document}))
    source = ImmutableBlueprintActionSource(source_id, tuple(admitted))
    if not wire and source != document:
        _refuse("source", "is not a canonical exact source graph")
    ordered = [item for _, item in sorted(serialized, key=lambda pair: pair[0].canonical_bytes())]
    return source, {"version": _ARTIFACT_VERSION, "source_id": source_id, "entries": ordered}


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for name, value in pairs:
        if name in result:
            _refuse("JSON object", "contains a duplicate member name")
        result[name] = value
    return result


def _parse_integer(token: str) -> int:
    if len(token.removeprefix("-")) > 640:
        _refuse("JSON integer", "has more than 640 decimal digits")
    return int(token)


def _reject_number(token: str) -> None:
    _refuse("JSON number", "floats and nonfinite constants are not admitted")


def decode_blueprint(raw: bytes) -> ImmutableBlueprintActionSource:
    """Decode strict UTF-8 JSON bytes into one completely admitted source."""
    if type(raw) is not bytes:
        _refuse("raw", "must be exact bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        _refuse("raw", "UTF-8 BOM is not admitted")
    try:
        text = raw.decode("utf-8")
        document = json.loads(text, object_pairs_hook=_pairs, parse_int=_parse_integer,
                              parse_float=_reject_number, parse_constant=_reject_number)
        return _admit(document, wire=True)[0]
    except BlueprintArtifactError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError,
            TypeError, ValueError) as error:
        raise BlueprintArtifactError(f"artifact refused: {error}") from error


def encode_blueprint(source: ImmutableBlueprintActionSource) -> bytes:
    """Validate an exact source graph and return deterministic ASCII JSON plus LF."""
    try:
        _, document = _admit(source, wire=False)
        return (json.dumps(document, allow_nan=False, ensure_ascii=True,
                           separators=(",", ":"), sort_keys=True) + "\n").encode("ascii")
    except BlueprintArtifactError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise BlueprintArtifactError(f"source refused: {error}") from error
