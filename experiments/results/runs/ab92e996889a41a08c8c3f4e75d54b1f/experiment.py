"""Train, evaluate and export a small river policy without changing production.

The current action codec is deterministic. Retain the mixed teacher and measure
argmax projection loss explicitly. Runtime checks use the direct HandRuntime
interface and real monotonic timing, not the subprocess session transport.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
from pontius.cfr import TabularCFR
from pontius.evaluation import collect_information_sets, evaluate_profile, expected_utilities
from pontius.execution import begin_run, finish_run
from pontius.holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
    passive_blueprint_action,
)
from pontius.no_limit_betting import CALL, CHECK, FOLD, NoLimitBettingState, raise_to
from pontius.river import RiverHoldem, make_hole, parse_cards
from pontius.v0a.model import (
    ActionMailbox,
    HandAction,
    HandStartedEvent,
    OpponentActionEvent,
    ShowdownResultEvent,
    StreetRevealedEvent,
)
from pontius.v0a.runtime import HandRuntime

ROOT = Path(__file__).resolve().parents[1]
BOARD = parse_cards("Ks", "Qh", "7d", "4c", "2s")
CHANGED_BOARD = parse_cards("Ks", "Qh", "7d", "4c", "2h")
HANDS = (
    tuple(make_hole(*hand.split()) for hand in ("As Ad", "7c 7s", "6h 5h", "3h 3d")),
    tuple(make_hole(*hand.split()) for hand in ("Jc Jd", "Tc Td", "9c 9d", "8c 8d")),
)
UNSUPPORTED = (make_hole("6c", "5c"), make_hole("Ts", "9s"))
BET = 4


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def game_for(weights=(1, 1, 1, 1)):
    return RiverHoldem.from_independent_ranges(
        board=BOARD,
        pot=8,
        stacks=(196, 196),
        bet_size=BET,
        player0_weights=dict(zip(HANDS[0], weights, strict=True)),
        player1_weights={hand: 1 for hand in HANDS[1]},
    )


def deterministic(policy):
    result = {}
    for key, distribution in policy.items():
        action = max(distribution, key=distribution.__getitem__)
        result[key] = {candidate: float(candidate == action) for candidate in distribution}
    return result


def fixed_policy(game, first, second):
    result = {}
    for player, action in enumerate((first, second)):
        for key, actions in collect_information_sets(game, player).items():
            result[key] = {candidate: float(candidate == action) for candidate in actions}
    return result


def action_for(game, policy, player, hand):
    deal = next(deal for deal, _ in game.deals if deal.hand(player) == hand)
    state = game.initial_state().apply_action(deal)
    if player == 1:
        state = state.apply_action("bet")
    key = state.information_state_key(player)
    return max(policy[key], key=policy[key].__getitem__)


def concrete(action):
    return {"bet": raise_to(BET), "check": CHECK, "call": CALL, "fold": FOLD}[action]


def base_state():
    return NoLimitBettingState.new_hand(
        button=0, starting_stacks=(200,) * 6, small_blind=1, big_blind=2
    )


def setup_action(state):
    if state.street.value == "preflop":
        if state.acting_seat not in (1, 2):
            return FOLD
        return raise_to(4) if state.acting_seat == 1 else CALL
    return CHECK


def river_state():
    state = base_state()
    while state.street.value != "river":
        state = (
            state.advance_street()
            if state.round_complete
            else state.apply_action(setup_action(state))
        )
    assert state.live_seats == (1, 2)
    assert state.pot == 8 and state.stacks[1:3] == (196, 196)
    return state


def key_for(state, seat, hand, board):
    view = OneSeatCardState(seat, hand, state.street, board)
    return BlueprintDecisionKey.from_state(
        cards=view, betting=state, decision=state.legal_decision()
    )


def export(game, projected):
    entries = {}
    state = base_state()
    for _ in range(4):
        state = state.apply_action(FOLD)
    for hand in (*HANDS[0], UNSUPPORTED[0]):
        key = key_for(state, 1, hand, ())
        entries[key] = BlueprintActionEntry(key, raise_to(4))
    opening = river_state()
    mapping = []
    for player in (0, 1):
        state = opening if player == 0 else opening.apply_action(raise_to(BET))
        for hand in HANDS[player]:
            abstract = action_for(game, projected, player, hand)
            action = concrete(abstract)
            key = key_for(state, player + 1, hand, BOARD)
            entries[key] = BlueprintActionEntry(key, action)
            mapping.append(
                dict(
                    player=player,
                    hand=hand,
                    abstract_action=abstract,
                    concrete_action=dict(kind=action.kind.value, raise_to=action.raise_to),
                )
            )
    raw = encode_blueprint(
        ImmutableBlueprintActionSource("trained-river-argmax-pilot", tuple(entries.values()))
    )
    assert len(raw) <= 1_048_576
    decoded = decode_blueprint(raw)
    assert encode_blueprint(decoded) == raw
    return raw, decoded, mapping


def complete_deal(first, second, board):
    reserved = set(BOARD) | set(CHANGED_BOARD)
    for collection in (*HANDS, UNSUPPORTED):
        for item in collection:
            reserved.update(item)
    available = [card for card in range(52) if card not in reserved]
    hands = [None] * 6
    hands[1], hands[2] = first, second
    for ordinal, seat in enumerate((0, 3, 4, 5)):
        hands[seat] = tuple(available[ordinal * 2 : ordinal * 2 + 2])
    return SixSeatHoldemDeal(tuple(hands), board)


def play(source, game, projected, first, second, player, mode, board, source_hash, supported):
    seat = player + 1
    deal = complete_deal(first, second, board)
    mailbox = ActionMailbox()
    runtime = HandRuntime(
        blueprint=source,
        mailbox=mailbox,
        clock=time.monotonic_ns,
        source_manifest_sha256=source_hash,
    )
    hand_id = "pontius-v0a-event-interface-v2-correctness-trained-" + uuid.uuid4().hex
    event_index = 0
    outcome = runtime.dispatch(
        HandStartedEvent(hand_id, event_index, 0, seat, (200,) * 6, 1, 2, deal.hand(seat))
    )
    assert outcome.status == "accepted"
    state = base_state()
    decisions, actions = [], []

    def send(event):
        outcome = runtime.dispatch(event)
        assert outcome.status in ("accepted", "decided", "completed"), repr(outcome)
        return outcome

    while not state.is_terminal:
        if state.round_complete:
            state = state.advance_street()
            if state.is_terminal:
                break
            cards = deal.public_cards(state.street)
            revealed = cards if state.street.value == "flop" else cards[-1:]
            event_index += 1
            outcome = send(StreetRevealedEvent(hand_id, event_index, state.street.value, revealed))
            continue
        controlled = state.acting_seat == seat
        modeled = state.street.value == "river" and (
            state.acting_seat == 1 or state.current_bet > 0
        )
        if state.street.value != "river":
            action = setup_action(state)
        elif controlled:
            action = (
                concrete(action_for(game, projected, player, deal.hand(seat)))
                if supported and modeled
                else passive_blueprint_action(state.legal_decision())
            )
        else:
            other = state.acting_seat - 1
            if not modeled:
                action = CHECK
            elif mode == "projected":
                action = concrete(action_for(game, projected, other, deal.hand(state.acting_seat)))
            elif other == 0:
                action = concrete("bet" if mode == "aggressive" else "check")
            else:
                action = concrete("call" if mode == "aggressive" else "fold")
        if controlled:
            assert outcome.decision is not None
            decision = outcome.decision
            assert decision.selected_action == HandAction.from_betting_action(action)
            assert decision.failure_reason is None
            delivered = mailbox.accepted[(hand_id, decision.action_index)]
            assert delivered.action == decision.selected_action
            hit_expected = (state.street.value == "preflop" and seat == 1) or (
                supported and modeled
            )
            assert decision.selection_reason == ("table_hit" if hit_expected else "passive_default")
            timing = decision.timing
            assert (
                timing.status == "completed"
                and not timing.work_cutoff_crossed
                and not timing.deadline_crossed
            )
            decisions.append(
                dict(
                    street=state.street.value,
                    modeled=modeled,
                    reason=decision.selection_reason,
                    action=asdict(decision.selected_action),
                    timing=asdict(timing),
                )
            )
            state = state.apply_action(action)
            assert runtime.state == state
        else:
            acting = state.acting_seat
            street = state.street.value
            state = state.apply_action(action)
            event_index += 1
            outcome = send(
                OpponentActionEvent(
                    hand_id, event_index, street, acting, HandAction.from_betting_action(action)
                )
            )
        actions.append(dict(kind=action.kind.value, raise_to=action.raise_to))
    strengths = deal.showdown_strengths(state.live_seats) if state.showdown_ready else None
    if strengths is not None:
        event_index += 1
        send(ShowdownResultEvent(hand_id, event_index, strengths))
    assert runtime.hand_complete
    settlement = runtime.settle()
    expected = state.settle(strengths)
    assert settlement.final_stacks == expected.final_stacks
    assert settlement.payouts == expected.payouts
    assert sum(settlement.final_stacks) == 1200
    runtime.finalize_accounting()
    assert runtime.accounting().complete
    assert len(mailbox.accepted) == len(decisions)
    return dict(
        player=player,
        opponent=mode,
        supported=supported,
        first=first,
        second=second,
        board=board,
        decisions=decisions,
        actions=actions,
        final_stacks=settlement.final_stacks,
        river_utility=settlement.final_stacks[seat] - 200,
        accounting=asdict(runtime.accounting()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=120)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14) or args.seconds <= 0:
        parser.error("Use Python 3.14 and a positive budget")
    started = time.perf_counter()
    context = begin_run(ROOT)
    directory = ROOT / "experiments/results/runs" / uuid.uuid4().hex
    directory.mkdir(parents=True)
    context["output_directory"] = directory.relative_to(ROOT).as_posix()
    driver = Path(__file__).read_bytes()
    driver_hash = hashlib.sha256(driver).hexdigest()
    (directory / "experiment.py").write_bytes(driver)
    retained = {}

    def retain(name, value):
        raw = value if isinstance(value, bytes) else encode(value)
        (directory / name).write_bytes(raw)
        retained[name] = hashlib.sha256(raw).hexdigest()

    retain(
        "runtimes.json",
        dict(
            python=sys.version,
            executable=sys.executable,
            source_commit=context["commit"],
            source_sha256=context["source_sha256"],
            source_verified=context["verified"],
            driver_sha256=driver_hash,
        ),
    )
    design = dict(
        board=BOARD,
        hands=HANDS,
        pot=8,
        bet=BET,
        stacks=[196, 196],
        trainer="dcfr",
        iterations=2000,
        checkpoints=[0, 200, 1000, 2000],
        projection="argmax probability; ties follow solver action order",
        teacher_nashconv_limit=0.02,
        maximum_export_nashconv_increase=0.08,
        range_probes={
            "training": [1, 1, 1, 1],
            "value_light": [1, 1, 3, 3],
            "value_heavy": [3, 3, 1, 1],
        },
        runtime_hands=100,
        setup="Seats 3,4,5,0 fold; SB raises to 4; BB calls; flop/turn check through",
        limitations=(
            "Restricted two-player river; no raise or check-back bet; "
            "exact known-domain evaluation; range probes are not unseen-hand "
            "training holdouts; direct runtime only"
        ),
    )
    retain("design.json", design)
    report = dict(
        status="failed", source_verified=context["verified"], experiment_sha256=driver_hash
    )
    try:
        game = game_for()
        solver = TabularCFR(game, variant="dcfr")
        history = []
        training_start = time.perf_counter()
        for checkpoint in design["checkpoints"]:
            while solver.iteration < checkpoint:
                solver.run(min(100, checkpoint - solver.iteration))
                if time.perf_counter() - started > args.seconds:
                    raise TimeoutError("Training budget exhausted")
            history.append(
                dict(
                    iteration=checkpoint,
                    evaluation=asdict(evaluate_profile(game, solver.average_strategy())),
                )
            )
        report["training_seconds"] = time.perf_counter() - training_start
        teacher = solver.average_strategy()
        projected = deterministic(teacher)
        passive = fixed_policy(game, "check", "call")
        retain("teacher.json", teacher)
        retain("projected-policy.json", projected)
        report["training_history"] = history
        evaluations = {}
        for name, weights in design["range_probes"].items():
            probe = game_for(weights)
            evaluations[name] = {
                label: asdict(evaluate_profile(probe, policy))
                for label, policy in (
                    ("teacher", teacher),
                    ("projected", projected),
                    ("passive", passive),
                )
            }
        report["evaluations"] = evaluations
        opponent_results = {}
        for label, opponent in (
            ("check_call", passive),
            ("bet_call", fixed_policy(game, "bet", "call")),
            ("bet_fold", fixed_policy(game, "bet", "fold")),
        ):
            opponent_results[label] = {}
            for player in (0, 1):
                keys = collect_information_sets(game, player)
                opponent_results[label][player] = {}
                for name, policy in (
                    ("teacher", teacher),
                    ("projected", projected),
                    ("passive", passive),
                ):
                    profile = {**opponent, **{key: policy[key] for key in keys}}
                    opponent_results[label][player][name] = expected_utilities(game, profile)[
                        player
                    ]
        report["fixed_opponent_values"] = opponent_results
        raw, source, mapping = export(game, projected)
        retain("blueprint.json", raw)
        retain("mapping.json", mapping)
        report.update(
            artifact_bytes=len(raw),
            artifact_entries=len(source.entries),
            learned_entries=len(mapping),
            setup_entries=len(source.entries) - len(mapping),
        )
        runtime_results = []
        for deal, _ in game.deals:
            for player in (0, 1):
                for mode in ("projected", "aggressive", "passive"):
                    runtime_results.append(
                        play(
                            source,
                            game,
                            projected,
                            deal.player0,
                            deal.player1,
                            player,
                            mode,
                            BOARD,
                            context["source_sha256"],
                            True,
                        )
                    )
                    if time.perf_counter() - started > args.seconds:
                        raise TimeoutError("Runtime verification budget exhausted")
        for player in (0, 1):
            first, second = HANDS[0][0], HANDS[1][0]
            runtime_results.append(
                play(
                    source,
                    game,
                    projected,
                    first,
                    second,
                    player,
                    "aggressive",
                    CHANGED_BOARD,
                    context["source_sha256"],
                    False,
                )
            )
            first, second = (UNSUPPORTED[0], second) if player == 0 else (first, UNSUPPORTED[1])
            runtime_results.append(
                play(
                    source,
                    game,
                    projected,
                    first,
                    second,
                    player,
                    "aggressive",
                    BOARD,
                    context["source_sha256"],
                    False,
                )
            )
        retain("runtime-hands.json", runtime_results)
        assert len(runtime_results) == design["runtime_hands"]
        supported_decisions = [
            decision
            for hand in runtime_results
            if hand["supported"]
            for decision in hand["decisions"]
            if decision["modeled"]
        ]
        unsupported_decisions = [
            decision
            for hand in runtime_results
            if not hand["supported"]
            for decision in hand["decisions"]
            if decision["modeled"]
        ]
        assert supported_decisions and all(
            decision["reason"] == "table_hit" for decision in supported_decisions
        )
        assert len(unsupported_decisions) == 4 and all(
            decision["reason"] == "passive_default" for decision in unsupported_decisions
        )
        # The concrete pot is even, so net full-hand chips equal microgame river utility.
        for player in (0, 1):
            for mode in ("projected", "aggressive", "passive"):
                observed = sum(
                    hand["river_utility"]
                    for hand in runtime_results
                    if hand["supported"] and hand["player"] == player and hand["opponent"] == mode
                ) / len(game.deals)
                opponent = (
                    projected
                    if mode == "projected"
                    else fixed_policy(
                        game,
                        "bet" if mode == "aggressive" else "check",
                        "call" if mode == "aggressive" else "fold",
                    )
                )
                profile = {
                    **opponent,
                    **{key: projected[key] for key in collect_information_sets(game, player)},
                }
                assert abs(observed - expected_utilities(game, profile)[player]) < 1e-10
        report["runtime"] = dict(
            hands=len(runtime_results),
            supported_modeled_decisions=len(supported_decisions),
            unsupported_modeled_decisions=len(unsupported_decisions),
            exact_payoff_comparisons=6,
            max_response_ms=max(
                decision["timing"]["elapsed_ns"] / 1e6
                for hand in runtime_results
                for decision in hand["decisions"]
            ),
        )
        metrics = evaluations["training"]
        loss = metrics["projected"]["nash_conv"] - metrics["teacher"]["nash_conv"]
        report["quality"] = dict(
            teacher_converged=metrics["teacher"]["nash_conv"] <= design["teacher_nashconv_limit"],
            projection_nashconv_increase=loss,
            export_preserves_quality=loss <= design["maximum_export_nashconv_increase"],
            projected_beats_passive_nashconv=metrics["projected"]["nash_conv"]
            < metrics["passive"]["nash_conv"],
        )
        report.update(
            status="completed",
            integration_passed=True,
            export_adoptable=report["quality"]["teacher_converged"]
            and report["quality"]["export_preserves_quality"],
        )
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}")
    report.update(retained_hashes=retained, total_seconds=time.perf_counter() - started)
    report["summary"] = (
        f"Trained river export pilot: {report['status']}; "
        f"integration={report.get('integration_passed')}; "
        f"export_adoptable={report.get('export_adoptable')}"
    )
    finish_run(context, "2026-09-08-trained-river-blueprint", report, report["total_seconds"])
    print(
        json.dumps(
            dict(
                result=str(directory / "result.json"),
                summary=report["summary"],
                error=report.get("error"),
                quality=report.get("quality"),
            )
        )
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
