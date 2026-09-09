"""Compare passive table hits and fallback over 8-/16-hand sessions on Python 3.14.

Run from the repository root with PYTHONPATH=src. The filler artifact is an
existing retained workload input; generated inputs and one result stay together.
This is a diagnostic policy built for these deals, not a trained poker strategy.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
import uuid

from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
from pontius.execution import begin_run, finish_run
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
    passive_blueprint_action,
)
from pontius.holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from pontius.no_limit_betting import NoLimitBettingState


ROOT = Path(__file__).resolve().parents[1]
SEED = hashlib.sha256(b"pontius-blueprint-hit-sessions-20260908").hexdigest()
CAP = 1_048_576


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def predict(deals, controlled_seat):
    """Construct actor-visible keys along the declared all-passive trajectories."""
    stacks = (200,) * 6
    entries, hands = {}, []
    for ordinal, raw in enumerate(deals):
        deal = SixSeatHoldemDeal(
            tuple(tuple(hand) for hand in raw["private_hands"]), tuple(raw["board_runout"])
        )
        state = NoLimitBettingState.new_hand(
            button=ordinal % 6, starting_stacks=stacks, small_blind=1, big_blind=2
        )
        actions = []
        while not state.is_terminal:
            if state.round_complete:
                state = state.advance_street()
                continue
            decision = state.legal_decision()
            action = passive_blueprint_action(decision)
            if state.acting_seat == controlled_seat:
                view = OneSeatCardState(
                    controlled_seat, deal.hand(controlled_seat), state.street,
                    deal.public_cards(state.street),
                )
                key = BlueprintDecisionKey.from_state(cards=view, betting=state, decision=decision)
                entries[key] = BlueprintActionEntry(key, action)
            actions.append(dict(
                index=len(actions), seat=state.acting_seat, street=state.street.value,
                action=dict(kind=action.kind.value, raise_to=action.raise_to),
                origin="bot" if state.acting_seat == controlled_seat else "opponent",
            ))
            state = state.apply_action(action)
        strengths = deal.showdown_strengths(state.live_seats) if state.showdown_ready else None
        settled = state.settle(strengths)
        hands.append(dict(
            starting_stacks=list(stacks), button=ordinal % 6, actions=actions,
            final_stacks=list(settled.final_stacks), payouts=list(settled.payouts),
        ))
        stacks = settled.final_stacks
        if min(stacks) < 2:
            raise ValueError("declared passive schedule cannot complete all hands")
    return entries, hands


def artifact(entries):
    source = ImmutableBlueprintActionSource("hit-session-diagnostic", tuple(entries))
    return encode_blueprint(source)


def build_inputs(controller, directory, filler_path):
    dealer = controller.load_tool("seeded_deals")
    deals = [dealer.deal_for_hand(SEED, ordinal) for ordinal in range(16)]
    entries, expected = {}, {}
    for seat in (0, 3):
        seat_entries, expected[seat] = predict(deals, seat)
        entries.update(seat_entries)
    hits = list(entries.values())
    filler_raw = filler_path.read_bytes()
    filler = [entry for entry in decode_blueprint(filler_raw).entries if entry.key not in entries]
    lower, upper = 0, len(filler)
    while lower < upper:
        middle = (lower + upper + 1) // 2
        if len(artifact(hits + filler[:middle])) <= CAP:
            lower = middle
        else:
            upper = middle - 1
    arms = [("empty", []), ("small_hit", hits), ("near_cap_hit", hits + filler[:lower])]
    identities, metadata, sizes = {}, [], {}

    def retain(name, raw):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        identities[name] = hashlib.sha256(raw).hexdigest()

    for arm, selected in arms:
        raw = artifact(selected)
        if len(raw) > CAP:
            raise ValueError("diagnostic hit keys exceed the session artifact cap")
        size = len(selected)
        if size in sizes.values():
            raise ValueError("artifact arms need distinct entry counts")
        sizes[arm] = size
        retain(f"artifacts/{size}.json", raw)
        metadata.append(dict(size=size, arm=arm, wire_bytes=len(raw)))
    cells = []
    for schedule_index, hand_count in enumerate((8, 16)):
        for seat in (0, 3):
            opponents = ["passive"] * 6
            opponents[seat] = None
            session = dict(
                version="pontius-v0a-table-session-v1", button=0, controlled_seat=seat,
                starting_stacks=[200] * 6, small_blind=1, big_blind=2,
                opponents=opponents, hands=deals[:hand_count],
            )
            raw = encode(session)
            if len(raw) > 16_384:
                raise ValueError("session input exceeds the existing interface cap")
            retain(f"sessions/d{hand_count}-s{seat}-l0.json", raw)
            order = list(sizes) if (schedule_index + seat) % 2 == 0 else list(reversed(sizes))
            for arm in order:
                label = f"hits-h{hand_count}-s{seat}-{arm.replace('_', '-')}"
                cells.append(dict(
                    id=label, runtime="3.14", kind="session", size=sizes[arm], argv=[],
                    parameters=dict(
                        deal=hand_count, seat=seat, lineup=0, hand_count=hand_count, arm=arm,
                        strategy="blueprint-v1", diagnostic=False,
                        session_id="pontius-v0a-table-session-v1-correctness-" + label,
                    ),
                ))
    design = dict(
        seed=SEED, hand_lengths=[8, 16], seats=[0, 3], all_opponents="passive",
        expected=expected, artifacts=metadata, cells=cells,
        filler_path=str(filler_path), filler_sha256=hashlib.sha256(filler_raw).hexdigest(),
        filler_entries_used=lower,
        next_filler_bytes=len(artifact(hits + filler[:lower + 1])) if lower < len(filler) else None,
        limitation="Keys deliberately cover these passive deals; no strategy-quality inference.",
    )
    retain("design.json", encode(design))
    request = dict(
        population_root=str(directory), population={"artifacts": metadata},
        selections={}, input_hashes=identities, cells=cells,
    )
    return request, design


def assess(report, design):
    definitions = {cell["id"]: cell for cell in design["cells"]}
    groups, errors = {}, []
    for cell in report.get("cells", []):
        parameters = definitions[cell["id"]]["parameters"]
        arm, seat = parameters["arm"], parameters["seat"]
        group = groups.setdefault(arm, dict(
            sessions=0, hands=0, decisions=0, hits=0, misses=0, seconds=[],
            response_ms=[], compute_ms=[], hand_compute_ms=[], per_hand=[],
        ))
        session = cell["observation"]["session"]
        group["sessions"] += 1
        group["seconds"].append(cell["elapsed_seconds"])
        if session["completed_hands"] != parameters["hand_count"]:
            errors.append(cell["id"] + ": incomplete session")
        for ordinal, hand in enumerate(session["hands"]):
            result = hand["result"]
            expected = design["expected"][seat][ordinal]
            actual = dict(
                starting_stacks=hand["starting_stacks"], button=hand["button"],
                actions=result["applied_actions"],
                final_stacks=result["settlement"]["final_stacks"],
                payouts=result["settlement"]["payouts"],
            )
            if actual != expected:
                errors.append(f"{cell['id']}: hand {ordinal + 1} trajectory mismatch")
            events = [json.loads(line) for line in base64.b64decode(
                result["child_stdout_base64"], validate=True
            ).splitlines()]
            decisions = [event["decision"] for event in events if event.get("decision")]
            ledger = next(event for event in events if event["type"] == "hand_result")
            closing = next(event for event in events if event["type"] == "session_result")
            if not ledger["accounting_complete"] or not closing["accounting_complete"]:
                errors.append(cell["id"] + ": incomplete accounting")
            if len(decisions) != 4:
                errors.append(cell["id"] + ": expected four passive decisions per hand")
            group["hands"] += 1
            charged = ledger["preparation_compute_seconds"]
            for decision in decisions:
                timing = decision["timing"]
                reason = decision["selection_reason"]
                wanted = "passive_default" if arm == "empty" else "table_hit"
                if reason != wanted:
                    errors.append(cell["id"] + ": unexpected lookup outcome " + reason)
                if timing["status"] != "completed" or timing["work_cutoff_crossed"]:
                    errors.append(cell["id"] + ": response status or cutoff failure")
                if timing["deadline_crossed"]:
                    errors.append(cell["id"] + ": deadline crossing")
                group["decisions"] += 1
                group["hits"] += int(reason == "table_hit")
                group["misses"] += int(reason == "passive_default")
                group["response_ms"].append(timing["elapsed_ns"] / 1e6)
                group["compute_ms"].append(timing["response_compute_seconds"] * 1000)
                charged += timing["response_compute_seconds"]
            group["hand_compute_ms"].append(charged * 1000)
            group["per_hand"].append(dict(cell=cell["id"], ordinal=ordinal + 1,
                                         charged_ms=charged * 1000))
    return dict(passed=not errors and report.get("completed") == 12, errors=errors, groups=groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filler", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=180)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14) or args.seconds <= 0:
        parser.error("use Python 3.14 and a positive time budget")
    started = time.perf_counter()
    context = begin_run(ROOT)
    run = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    run.mkdir(parents=True)
    context["output_directory"] = run.relative_to(ROOT).as_posix()
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    clocks = {name: vars(time.get_clock_info(name)) for name in ("monotonic", "perf_counter")}
    (run / "runtimes.json").write_bytes(encode([dict(
        python=sys.version, executable=sys.executable, source_commit=context["commit"],
        source_sha256=context["source_sha256"], source_verified=context["verified"],
        experiment_sha256=script_hash, clocks=clocks,
    )]))
    report = dict(status="failed", planned=12)
    try:
        spec = importlib.util.spec_from_file_location(
            "hit_session_controller", ROOT / "tools/v0a_blueprint_workload.py"
        )
        controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        request, design = build_inputs(controller, run / "inputs", args.filler.resolve())
        report.update(design=design, input_hashes=request["input_hashes"])
        preparation = time.perf_counter() - started
        if preparation >= args.seconds:
            raise TimeoutError("budget exhausted during input preparation")
        report.update(controller.supervise(
            request, context, args.seconds - preparation, 3072 * 1024 * 1024
        ))
        report["preparation_seconds"] = preparation
        report["assessment"] = assess(report, design)
        report["execution_status"] = report["status"]
        if not report["assessment"]["passed"]:
            report["status"] = "failed"
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    report.update(
        runtime="3.14", experiment_sha256=script_hash, source_verified=context["verified"],
        source_sha256=context["source_sha256"], clocks=clocks,
        total_seconds=time.perf_counter() - started,
        memory_scope="cumulative worker-job peak; no per-hand memory series",
    )
    report["summary"] = (
        f"{report.get('completed', 0)}/12 hit/multi-hand session cells; {report['status']}; "
        f"{report['total_seconds']:.3f}s total"
    )
    finish_run(context, "2026-09-08-blueprint-hit-sessions", report, report["total_seconds"])
    print(json.dumps(dict(result=str(run / "result.json"), summary=report["summary"],
                          error=report.get("error"), errors=report.get("errors"),
                          assessment_errors=report.get("assessment", {}).get("errors"))))
    for arm, group in report.get("assessment", {}).get("groups", {}).items():
        print(arm, group["hands"], "hands", group["hits"], "hits", group["misses"], "misses",
              "median charged ms", statistics.median(group["hand_compute_ms"]))
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
