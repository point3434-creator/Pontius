"""Exercise active diagnostic blueprint actions through the real session path.

This is a correctness experiment, not a trained strategy or strength evaluation.
Run with Python 3.14 and PYTHONPATH=src. One worker, 48 one-hand sessions,
180 seconds and a 3 GiB worker-job cap; retain one result and journal entry.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time
import uuid

from pontius.blueprint_artifact.codec import encode_blueprint
from pontius.execution import begin_run, finish_run
from pontius.holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
    passive_blueprint_action,
)
from pontius.no_limit_betting import CHECK, FOLD, NoLimitBettingState, raise_to

ROOT = Path(__file__).resolve().parents[1]
SEED = hashlib.sha256(b"pontius-active-blueprint-sessions-20260908").hexdigest()
SCENARIOS = ("bet", "reraise", "fold", "shove", "call_shove", "hit_then_miss")
REQUIRED = {
    "bet",
    "raise",
    "reraise",
    "fold",
    "all_in_raise",
    "all_in_call",
    "miss_after_hit",
    "side_pots",
    "uncalled_refund",
}


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def action_value(action):
    return dict(kind=action.kind.value, raise_to=action.raise_to)


def opponent_action(policy, state, legal):
    """Declared host policy semantics, evaluated without calling the host selector."""
    previous = [row for row in state.history if row.seat == state.acting_seat]
    first_on_street = not any(row.street == state.street for row in previous)
    if legal.can_raise:
        if policy == "min_raise_once" and first_on_street:
            return raise_to(legal.raise_bounds.minimum_raise_to)
        if policy == "shove_once" and not previous:
            return raise_to(legal.raise_bounds.maximum_raise_to)
    if policy == "fold_to_bet":
        return CHECK if legal.can_check else FOLD
    return passive_blueprint_action(legal)


def diagnostic_action(scenario, state, legal):
    previous = [
        row for row in state.history if row.seat == state.acting_seat and row.street == state.street
    ]
    if scenario == "fold":
        return FOLD if legal.can_fold and not legal.can_check else CHECK
    allowed_raises = 2 if scenario == "reraise" else 1
    raises = sum(row.action.kind.value == "raise" for row in previous)
    if scenario != "call_shove" and legal.can_raise and raises < allowed_raises:
        amount = (
            legal.raise_bounds.maximum_raise_to
            if scenario == "shove"
            else legal.raise_bounds.minimum_raise_to
        )
        return raise_to(amount)
    return passive_blueprint_action(legal)


def reference_payouts(state, deal):
    """Award contribution tiers independently of the engine's settlement methods.

    Betting transitions and hand ranking still use the existing library. Adjacent
    tiers with identical eligible players form one pot before splitting odd chips.
    """
    groups = []
    previous = 0
    for level in sorted(set(state.total_contributions) - {0}):
        contributors = [
            seat for seat, total in enumerate(state.total_contributions) if total >= level
        ]
        eligible = tuple(seat for seat in contributors if not state.folded[seat])
        amount = (level - previous) * len(contributors)
        if groups and groups[-1][0] == eligible:
            groups[-1] = (eligible, groups[-1][1] + amount)
        else:
            groups.append((eligible, amount))
        previous = level
    strengths = deal.showdown_strengths(state.live_seats) if state.showdown_ready else None
    payouts = [0] * 6
    for eligible, amount in groups:
        winners = (
            list(eligible)
            if strengths is None
            else [
                seat
                for seat in eligible
                if strengths[seat] == max(strengths[player] for player in eligible)
            ]
        )
        assert winners, "Pot without an eligible winner"
        share, remainder = divmod(amount, len(winners))
        for seat in winners:
            payouts[seat] += share
        order = sorted(winners, key=lambda seat: (seat - state.button - 1) % 6)
        for seat in order[:remainder]:
            payouts[seat] += 1
    assert sum(payouts) == sum(state.total_contributions)
    return payouts, len(groups)


def predict(raw, seat, stacks, opponents, scenario, arm):
    deal = SixSeatHoldemDeal(
        tuple(tuple(hand) for hand in raw["private_hands"]), tuple(raw["board_runout"])
    )
    state = NoLimitBettingState.new_hand(
        button=0, starting_stacks=stacks, small_blind=1, big_blind=2
    )
    entries, keys, actions, decisions = {}, [], [], []
    saw_hit = False
    coverage = Counter()
    while not state.is_terminal:
        if state.round_complete:
            state = state.advance_street()
            continue
        legal = state.legal_decision()
        controlled = state.acting_seat == seat
        if controlled:
            hit = arm == "diagnostic" and (scenario != "hit_then_miss" or not decisions)
            action = (
                diagnostic_action(scenario, state, legal)
                if hit
                else passive_blueprint_action(legal)
            )
            view = OneSeatCardState(
                seat, deal.hand(seat), state.street, deal.public_cards(state.street)
            )
            key = BlueprintDecisionKey.from_state(cards=view, betting=state, decision=legal)
            keys.append((key, hit))
            if hit:
                entries[key] = BlueprintActionEntry(key, action)
            labels = []
            if hit:
                kind = action.kind.value
                if kind == "raise":
                    labels.append("bet" if state.current_bet == 0 else "raise")
                    if any(
                        row.street == state.street and row.action.kind.value == "raise"
                        for row in state.history
                    ):
                        labels.append("reraise")
                    if action.raise_to == legal.raise_bounds.maximum_raise_to:
                        labels.append("all_in_raise")
                if kind == "fold":
                    labels.append("fold")
                if kind == "call" and legal.call_amount == legal.stack:
                    labels.append("all_in_call")
            elif saw_hit:
                labels.append("miss_after_hit")
            coverage.update(labels)
            decisions.append(
                dict(
                    reason="table_hit" if hit else "passive_default",
                    action=action_value(action),
                    labels=labels,
                )
            )
            saw_hit |= hit
        else:
            action = opponent_action(opponents[state.acting_seat], state, legal)
        actions.append(
            dict(
                index=len(actions),
                seat=state.acting_seat,
                street=state.street.value,
                action=action_value(action),
                origin="bot" if controlled else "opponent",
            )
        )
        state = state.apply_action(action)
        assert len(actions) < 300, "Unexpected unbounded betting trajectory"
    payouts, pots = reference_payouts(state, deal)
    final = [state.stacks[player] + payouts[player] for player in range(6)]
    assert sum(final) == sum(stacks)
    assert all(chips >= 0 for chips in final)
    coverage["side_pots"] += int(pots > 1)
    coverage["uncalled_refund"] += int(any(row.uncalled_return_chips for row in state.history))
    return (
        entries,
        keys,
        dict(
            starting_stacks=list(stacks),
            button=0,
            actions=actions,
            final_stacks=final,
            payouts=payouts,
            decisions=decisions,
            coverage=dict(coverage),
        ),
    )


def build_inputs(controller, directory):
    dealer = controller.load_tool("seeded_deals")
    identities, expected, cells, entries, key_checks = {}, {}, [], {}, []

    def retain(name, value):
        raw = value if isinstance(value, bytes) else encode(value)
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        identities[name] = hashlib.sha256(raw).hexdigest()
        return len(raw)

    for scenario_index, scenario in enumerate(SCENARIOS):
        for seat in (0, 3):
            for repetition in range(2):
                case = scenario_index * 4 + (2 if seat == 3 else 0) + repetition
                raw = dealer.deal_for_hand(SEED, case)
                stacks = (
                    (200, 80, 120, 200, 60, 160)
                    if scenario in ("shove", "call_shove")
                    else (200,) * 6
                )
                opponents = ["passive"] * 6
                if scenario == "bet":
                    opponents[(seat + 2) % 6] = "fold_to_bet"
                else:
                    opponents[3 if seat == 0 else 4] = (
                        "shove_once" if scenario == "call_shove" else "min_raise_once"
                    )
                if scenario == "shove":
                    opponents[3 if seat == 0 else 0] = "fold_to_bet"
                    opponents[4] = "min_raise_once"
                opponents[seat] = None
                session = dict(
                    version="pontius-v0a-table-session-v1",
                    button=0,
                    controlled_seat=seat,
                    starting_stacks=list(stacks),
                    small_blind=1,
                    big_blind=2,
                    opponents=opponents,
                    hands=[raw],
                )
                assert retain(f"sessions/d{case}-s{seat}-l0.json", session) <= 16_384
                order = ("empty", "diagnostic") if case % 2 == 0 else ("diagnostic", "empty")
                for arm in order:
                    selected, keys, prediction = predict(
                        raw, seat, stacks, opponents, scenario, arm
                    )
                    for key, entry in selected.items():
                        assert key not in entries or entries[key] == entry, (
                            "Conflicting table actions"
                        )
                        entries[key] = entry
                    if arm == "diagnostic":
                        key_checks.extend(keys)
                    label = f"active-{case}-{arm}"
                    expected[label] = prediction
                    cells.append(
                        dict(
                            id=label,
                            runtime="3.14",
                            kind="session",
                            size=0,
                            argv=[],
                            parameters=dict(
                                deal=case,
                                seat=seat,
                                lineup=0,
                                arm=arm,
                                scenario=scenario,
                                strategy="blueprint-v1",
                                diagnostic=False,
                                session_id="pontius-v0a-table-session-v1-correctness-" + label,
                            ),
                        )
                    )
    for key, hit in key_checks:
        assert (key in entries) == hit, "Unexpected hit in a planned sparse-table miss"
    metadata = []
    for arm, selected in (("empty", []), ("diagnostic", list(entries.values()))):
        raw = encode_blueprint(
            ImmutableBlueprintActionSource("active-session-diagnostic", tuple(selected))
        )
        assert len(raw) <= 1_048_576
        retain(f"artifacts/{len(selected)}.json", raw)
        metadata.append(dict(arm=arm, size=len(selected), wire_bytes=len(raw)))
        for cell in cells:
            if cell["parameters"]["arm"] == arm:
                cell["size"] = len(selected)
    predicted_coverage = Counter()
    for cell in cells:
        if cell["parameters"]["arm"] == "diagnostic":
            predicted_coverage.update(expected[cell["id"]]["coverage"])
    assert all(predicted_coverage[label] > 0 for label in REQUIRED), dict(predicted_coverage)
    design = dict(
        seed=SEED,
        scenarios=SCENARIOS,
        cells=cells,
        expected=expected,
        artifacts=metadata,
        required_coverage=sorted(REQUIRED),
        predicted_coverage=dict(predicted_coverage),
        minimum_changed_pairs=20,
        limitation=(
            "Diagnostic actions; shared betting engine and hand ranker; "
            "independent contribution-tier payout calculation; "
            "no strength or tail-latency inference."
        ),
    )
    retain("design.json", design)
    return dict(
        population_root=str(directory),
        population={"artifacts": metadata},
        selections={},
        input_hashes=identities,
        cells=cells,
    ), design


def assess(report, design):
    errors, groups, coverage, paired = [], {}, Counter(), {}
    definitions = {cell["id"]: cell for cell in design["cells"]}
    for cell in report.get("cells", []):
        parameters = definitions[cell["id"]]["parameters"]
        arm = parameters["arm"]
        group = groups.setdefault(
            arm,
            dict(
                sessions=0,
                decisions=0,
                hits=0,
                misses=0,
                actions=Counter(),
                response_ms=[],
                compute_ms=[],
                hand_compute_ms=[],
            ),
        )
        session = cell["observation"]["session"]
        if session["status"] != "completed" or session["completed_hands"] != 1:
            errors.append(cell["id"] + ": incomplete session")
            continue
        hand = session["hands"][0]
        result = hand["result"]
        expected = design["expected"][cell["id"]]
        actual = dict(
            starting_stacks=hand["starting_stacks"],
            button=hand["button"],
            actions=result["applied_actions"],
            final_stacks=result["settlement"]["final_stacks"],
            payouts=result["settlement"]["payouts"],
        )
        if actual != {name: expected[name] for name in actual}:
            errors.append(cell["id"] + ": action/state/settlement mismatch")
        paired.setdefault(parameters["deal"], {})[arm] = actual["actions"]
        events = [
            json.loads(line)
            for line in base64.b64decode(result["child_stdout_base64"], validate=True).splitlines()
        ]
        decisions = [event["decision"] for event in events if event.get("decision")]
        ledger = next(event for event in events if event["type"] == "hand_result")
        closing = next(event for event in events if event["type"] == "session_result")
        if not ledger["accounting_complete"] or not closing["accounting_complete"]:
            errors.append(cell["id"] + ": incomplete accounting")
        if [decision["selection_reason"] for decision in decisions] != [
            decision["reason"] for decision in expected["decisions"]
        ]:
            errors.append(cell["id"] + ": hit/miss sequence mismatch")
        charged = ledger["preparation_compute_seconds"]
        for decision in decisions:
            timing = decision["timing"]
            if (
                timing["status"] != "completed"
                or timing["work_cutoff_crossed"]
                or timing["deadline_crossed"]
            ):
                errors.append(cell["id"] + ": response status/cutoff/deadline failure")
            group["decisions"] += 1
            group["hits"] += int(decision["selection_reason"] == "table_hit")
            group["misses"] += int(decision["selection_reason"] == "passive_default")
            group["response_ms"].append(timing["elapsed_ns"] / 1e6)
            group["compute_ms"].append(timing["response_compute_seconds"] * 1000)
            charged += timing["response_compute_seconds"]
        group["sessions"] += 1
        group["actions"].update(
            action["action"]["kind"] for action in actual["actions"] if action["origin"] == "bot"
        )
        group["hand_compute_ms"].append(charged * 1000)
        if arm == "diagnostic":
            coverage.update(expected["coverage"])
    changed = sum(
        len(pair) == 2 and pair["empty"] != pair["diagnostic"] for pair in paired.values()
    )
    if changed < design["minimum_changed_pairs"]:
        errors.append("Too few pairs show the intended changed trajectory")
    for label in design["required_coverage"]:
        if not coverage[label]:
            errors.append("Missing coverage: " + label)
    return dict(
        passed=not errors and report.get("completed") == len(design["cells"]),
        errors=errors,
        groups=groups,
        coverage=dict(coverage),
        changed_pairs=changed,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=180)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14) or args.seconds <= 0:
        parser.error("use Python 3.14 and a positive budget")
    started = time.perf_counter()
    context = begin_run(ROOT)
    run = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    run.mkdir(parents=True)
    context["output_directory"] = run.relative_to(ROOT).as_posix()
    driver_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (run / "runtimes.json").write_bytes(
        encode(
            [
                dict(
                    python=sys.version,
                    executable=sys.executable,
                    source_commit=context["commit"],
                    source_sha256=context["source_sha256"],
                    source_verified=context["verified"],
                    experiment_sha256=driver_hash,
                    clocks={
                        name: vars(time.get_clock_info(name))
                        for name in ("monotonic", "perf_counter")
                    },
                )
            ]
        )
    )
    report = dict(status="failed", planned=48)
    try:
        spec = importlib.util.spec_from_file_location(
            "active_session_controller", ROOT / "tools/v0a_blueprint_workload.py"
        )
        controller = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(controller)
        request, design = build_inputs(controller, run / "inputs")
        report.update(design=design, input_hashes=request["input_hashes"])
        setup = time.perf_counter() - started
        if setup >= args.seconds:
            raise TimeoutError("Input preparation exhausted the budget")
        report.update(
            controller.supervise(request, context, args.seconds - setup, 3072 * 1024 * 1024)
        )
        report["setup_seconds"] = setup
        report["assessment"] = assess(report, design)
        report["execution_status"] = report["status"]
        if not report["assessment"]["passed"]:
            report["status"] = "failed"
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    report.update(
        experiment_sha256=driver_hash,
        source_verified=context["verified"],
        source_sha256=context["source_sha256"],
        total_seconds=time.perf_counter() - started,
    )
    report["summary"] = (
        f"{report.get('completed', 0)}/48 active diagnostic session cells; "
        f"{report['status']}; {report['total_seconds']:.3f}s"
    )
    finish_run(context, "2026-09-08-blueprint-active-sessions", report, report["total_seconds"])
    print(
        json.dumps(
            dict(
                result=str(run / "result.json"),
                summary=report["summary"],
                error=report.get("error"),
                assessment_errors=report.get("assessment", {}).get("errors"),
            )
        )
    )
    for arm, group in report.get("assessment", {}).get("groups", {}).items():
        print(
            arm,
            group["sessions"],
            "sessions",
            group["hits"],
            "hits",
            group["misses"],
            "misses",
            "median hand compute ms",
            statistics.median(group["hand_compute_ms"]),
        )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
