"""Train, evaluate and export a small river policy without changing production.

The current action codec is deterministic. Retain the mixed teacher and measure
argmax projection loss explicitly. Runtime checks use the direct HandRuntime
interface and real monotonic timing, not the subprocess session transport.
"""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import uuid

from pontius.blueprint_artifact.codec import decode_blueprint, encode_blueprint
from pontius.cfr import TabularCFR
from pontius.evaluation import collect_information_sets, evaluate_profile, expected_utilities
from pontius.execution import begin_run, finish_run
from pontius.full_width_reference_policy import RationalActionProbability
from pontius.holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from pontius.immutable_blueprint import (
    BlueprintActionEntry,
    BlueprintDecisionKey,
    ImmutableBlueprintActionSource,
    WeightedBlueprintAction,
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


def play(
    source,
    game,
    projected,
    first,
    second,
    player,
    mode,
    board,
    source_hash,
    supported,
    native=False,
):
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
            if native and supported and modeled:
                action = outcome.decision.selected_action.to_betting_action()
                key = key_for(state, seat, deal.hand(seat), board)
                entry = next(entry for entry in source.entries if entry.key == key)
                assert action in dict(entry.action.choices)
            else:
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


def quantize_policy(teacher, denominator):
    """Largest-remainder allocation; sorted names make ties reproducible."""
    rows = {}
    for key, distribution in sorted(teacher.items()):
        scaled = {action: probability * denominator for action, probability in distribution.items()}
        weights = {action: math.floor(value) for action, value in scaled.items()}
        remaining = denominator - sum(weights.values())
        order = sorted(weights, key=lambda action: (-(scaled[action] - weights[action]), action))
        for action in order[:remaining]:
            weights[action] += 1
        assert sum(weights.values()) == denominator
        rows[key] = weights
    return dict(denominator=denominator, rows=rows)


def choose_ticket(weights, ticket):
    for action, weight in sorted(weights.items()):
        if ticket < weight:
            return action
        ticket -= weight
    raise ValueError("Ticket outside distribution")


def sample_policy(weighted, nonce):
    """Research seed only: independently address each information key per hand.

    Never use this public seed as live, opponent-visible bot randomness.
    The power-of-two denominator avoids modulo bias for uniform digest bits.
    """
    policy = {}
    for key, weights in weighted["rows"].items():
        digest = hashlib.sha256(encode(["pontius-mixed-river-20260908", nonce, key])).digest()
        ticket = int.from_bytes(digest[:4], "big") & (weighted["denominator"] - 1)
        selected = choose_ticket(weights, ticket)
        policy[key] = {action: float(action == selected) for action in weights}
    return policy


def mixed_run(args, started, context, directory, driver_hash, retain, retained):
    design = dict(
        teacher_run="ab92e996889a41a08c8c3f4e75d54b1f",
        teacher_sha256="7874807b9523ee47ebd30a5c943a883a7dc7d6cde076bff76e8ade038ed54791",
        denominator=2**20,
        quantization="largest remainder; alphabetical action ties",
        maximum_probability_error=1 / 2**20,
        maximum_export_nashconv_increase=0.08,
        teacher_nashconv_limit=0.02,
        frequency_draws_per_key=20000,
        maximum_frequency_error=0.015,
        runtime_repetitions=8,
        runtime_hands=772,
        seed="pontius-mixed-river-20260908; separate frequency/runtime nonce domains",
        limitations=(
            "Research weighted JSON uses abstract game keys; it is not a production codec. "
            "Sample independent pure actions once per key per hand, export through existing "
            "deterministic codec, and exercise direct HandRuntime. This microgame has at most "
            "one learned decision per player per hand. No live mixed provider, subprocess "
            "session, unseen-board policy, larger game or win-rate claim."
        ),
    )
    retain("design.json", design)
    report = dict(
        status="failed", source_verified=context["verified"], experiment_sha256=driver_hash
    )
    hands = []
    try:
        teacher_raw = (
            ROOT / "experiments/results/runs" / design["teacher_run"] / "teacher.json"
        ).read_bytes()
        assert hashlib.sha256(teacher_raw).hexdigest() == design["teacher_sha256"]
        teacher = json.loads(teacher_raw)
        retain("teacher.json", teacher_raw)
        weighted_raw = encode(quantize_policy(teacher, design["denominator"]))
        retain("weighted-policy.json", weighted_raw)
        weighted = json.loads(weighted_raw)
        assert encode(weighted) == weighted_raw
        recovered = {}
        boundary_checks = 0
        for key, weights in weighted["rows"].items():
            assert sum(weights.values()) == weighted["denominator"]
            recovered[key] = {
                action: RationalActionProbability(weight, weighted["denominator"]).as_float
                for action, weight in weights.items()
            }
            offset = 0
            for action, weight in sorted(weights.items()):
                if weight:
                    for ticket in (offset, offset + weight - 1):
                        assert choose_ticket(weights, ticket) == action
                        boundary_checks += 1
                offset += weight
        retain("recovered-policy.json", recovered)
        probability_error = max(
            abs(recovered[key][action] - probability)
            for key, distribution in teacher.items()
            for action, probability in distribution.items()
        )
        assert probability_error <= design["maximum_probability_error"]
        game = game_for()
        evaluations = {}
        for name, weights in (
            ("training", (1, 1, 1, 1)),
            ("value_light", (1, 1, 3, 3)),
            ("value_heavy", (3, 3, 1, 1)),
        ):
            probe = game_for(weights)
            evaluations[name] = {
                label: asdict(evaluate_profile(probe, policy))
                for label, policy in (
                    ("teacher", teacher),
                    ("recovered", recovered),
                    ("argmax", deterministic(teacher)),
                    ("passive", fixed_policy(game, "check", "call")),
                )
            }
        report["evaluations"] = evaluations
        metrics = evaluations["training"]
        loss = metrics["recovered"]["nash_conv"] - metrics["teacher"]["nash_conv"]
        report["quality"] = dict(
            maximum_probability_error=probability_error,
            export_nashconv_increase=loss,
            teacher_converged=metrics["teacher"]["nash_conv"] <= design["teacher_nashconv_limit"],
            export_preserves_quality=loss <= design["maximum_export_nashconv_increase"],
        )
        counts = {key: dict.fromkeys(weights, 0) for key, weights in weighted["rows"].items()}
        for draw in range(design["frequency_draws_per_key"]):
            sampled = sample_policy(weighted, ["frequency", draw])
            for key, distribution in sampled.items():
                counts[key][max(distribution, key=distribution.__getitem__)] += 1
            if draw % 1000 == 0 and time.perf_counter() - started > args.seconds:
                raise TimeoutError("Frequency budget exhausted")
        frequencies = {
            key: {
                action: count / design["frequency_draws_per_key"]
                for action, count in distribution.items()
            }
            for key, distribution in counts.items()
        }
        frequency_error = max(
            abs(frequencies[key][action] - recovered[key][action])
            for key in recovered
            for action in recovered[key]
        )
        retain(
            "sampling.json",
            dict(counts=counts, frequencies=frequencies, maximum_error=frequency_error),
        )
        assert frequency_error <= design["maximum_frequency_error"]
        for key, distribution in recovered.items():
            for action, probability in distribution.items():
                if probability in (0, 1):
                    assert frequencies[key][action] == probability
        artifact_sizes = []
        replay_checks = 0
        for repetition in range(design["runtime_repetitions"]):
            for deal_index, (deal, _) in enumerate(game.deals):
                for player in (0, 1):
                    for mode in ("projected", "aggressive", "passive"):
                        nonce = ["runtime", repetition, deal_index, player, mode]
                        sampled = sample_policy(weighted, nonce)
                        raw, source, _ = export(game, sampled)
                        replay_raw, _, _ = export(game, sample_policy(weighted, nonce))
                        assert replay_raw == raw
                        artifact_sizes.append(len(raw))
                        hand = play(
                            source,
                            game,
                            sampled,
                            deal.player0,
                            deal.player1,
                            player,
                            mode,
                            BOARD,
                            context["source_sha256"],
                            True,
                        )
                        # Independent abstract terminal path verifies every concrete net payoff.
                        abstract = game.initial_state().apply_action(deal)
                        while not abstract.terminal:
                            acting = abstract.current_player
                            if acting == player or mode == "projected":
                                action = action_for(game, sampled, acting, deal.hand(acting))
                            else:
                                action = (
                                    ("bet" if mode == "aggressive" else "check")
                                    if acting == 0
                                    else ("call" if mode == "aggressive" else "fold")
                                )
                            abstract = abstract.apply_action(action)
                        assert hand["river_utility"] == abstract.returns()[player]
                        hand.update(nonce=nonce, sampled_policy=sampled)
                        # Replay one complete hand per role/opponent/repetition with same sample.
                        if deal_index == 0:
                            replay = play(
                                source,
                                game,
                                sampled,
                                deal.player0,
                                deal.player1,
                                player,
                                mode,
                                BOARD,
                                context["source_sha256"],
                                True,
                            )
                            assert replay["actions"] == hand["actions"]
                            assert replay["final_stacks"] == hand["final_stacks"]
                            replay_checks += 1
                        hands.append(hand)
                        if time.perf_counter() - started > args.seconds:
                            raise TimeoutError("Runtime budget exhausted")
        for player in (0, 1):
            for changed in ("board", "hand"):
                nonce = ["unsupported", player, changed]
                sampled = sample_policy(weighted, nonce)
                _, source, _ = export(game, sampled)
                first, second = HANDS[0][0], HANDS[1][0]
                board = CHANGED_BOARD if changed == "board" else BOARD
                if changed == "hand":
                    first, second = (
                        (UNSUPPORTED[0], second) if player == 0 else (first, UNSUPPORTED[1])
                    )
                hand = play(
                    source,
                    game,
                    sampled,
                    first,
                    second,
                    player,
                    "aggressive",
                    board,
                    context["source_sha256"],
                    False,
                )
                hand.update(nonce=nonce, sampled_policy=sampled)
                hands.append(hand)
        assert len(hands) == design["runtime_hands"]
        learned = [
            decision
            for hand in hands
            if hand["supported"]
            for decision in hand["decisions"]
            if decision["modeled"]
        ]
        unsupported = [
            decision
            for hand in hands
            if not hand["supported"]
            for decision in hand["decisions"]
            if decision["modeled"]
        ]
        assert len(unsupported) == 4
        action_counts = {}
        for decision in learned:
            name = decision["action"]["kind"]
            action_counts[name] = action_counts.get(name, 0) + 1
        report.update(
            status="completed",
            integration_passed=True,
            export_adoptable=all(
                report["quality"][name]
                for name in ("teacher_converged", "export_preserves_quality")
            ),
            weighted_policy_bytes=len(weighted_raw),
            sampled_artifact_bytes=dict(minimum=min(artifact_sizes), maximum=max(artifact_sizes)),
            sampling=dict(
                draws_per_key=design["frequency_draws_per_key"],
                maximum_frequency_error=frequency_error,
                interval_boundary_checks=boundary_checks,
            ),
            runtime=dict(
                hands=len(hands),
                additional_replay_hands=replay_checks,
                sampled_artifact_replay_checks=len(artifact_sizes),
                exact_payoff_comparisons=len(artifact_sizes),
                supported_modeled_decisions=len(learned),
                unsupported_modeled_decisions=len(unsupported),
                learned_actions=action_counts,
                max_response_ms=max(
                    decision["timing"]["elapsed_ns"] / 1e6
                    for hand in hands
                    for decision in hand["decisions"]
                ),
            ),
        )
    except Exception as error:
        report.update(status="failed", error=f"{type(error).__name__}: {error}")
    retain("runtime-hands.json", hands)
    report.update(retained_hashes=retained, total_seconds=time.perf_counter() - started)
    report["summary"] = (
        f"Mixed river export pilot: {report['status']}; "
        f"integration={report.get('integration_passed')}; "
        f"research_export_preserves_quality={report.get('export_adoptable')}"
    )
    finish_run(
        context, "2026-09-08-trained-river-blueprint --mixed", report, report["total_seconds"]
    )
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


def native_export(game, teacher):
    """Map the frozen teacher into production full-history keys and read it back."""
    weighted = quantize_policy(teacher, 2**20)
    _, base, _ = export(game, deterministic(teacher))
    entries = {entry.key: entry for entry in base.entries}
    mapping = {}
    opening = river_state()
    for player in (0, 1):
        state = opening if player == 0 else opening.apply_action(raise_to(BET))
        for hand in HANDS[player]:
            deal = next(deal for deal, _ in game.deals if deal.hand(player) == hand)
            abstract = game.initial_state().apply_action(deal)
            if player == 1:
                abstract = abstract.apply_action("bet")
            abstract_key = abstract.information_state_key(player)
            key = key_for(state, player + 1, hand, BOARD)
            action = WeightedBlueprintAction(
                tuple(
                    (concrete(name), weight)
                    for name, weight in weighted["rows"][abstract_key].items()
                    if weight
                )
            )
            entries[key] = BlueprintActionEntry(key, action)
            mapping[abstract_key] = key
    raw = encode_blueprint(
        ImmutableBlueprintActionSource("trained-river-mixed", tuple(entries.values()))
    )
    decoded = decode_blueprint(raw)
    assert encode_blueprint(decoded) == raw
    actual = {entry.key: entry.action for entry in decoded.entries}
    recovered = {}
    for abstract_key, key in mapping.items():
        choices = actual[key].choices
        total = sum(weight for _, weight in choices)
        masses = dict(choices)
        recovered[abstract_key] = {
            name: masses.get(concrete(name), 0) / total for name in teacher[abstract_key]
        }
    return raw, decoded, recovered, {name: actual[key] for name, key in mapping.items()}


def native_sessions(source, raw, context, directory, seconds):
    """Real subprocess sessions; passive BB and four folds reach the modeled river."""
    spec = importlib.util.spec_from_file_location(
        "native_river_controller", ROOT / "tools/v0a_blueprint_workload.py"
    )
    controller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controller)
    population = directory / "inputs"
    identities, cases, cells = {}, {}, []

    def save(name, value):
        content = value if isinstance(value, bytes) else encode(value)
        path = population / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        identities[name] = hashlib.sha256(content).hexdigest()

    save("artifacts/13.json", raw)
    deals = [
        (deal.player0, deal.player1, BOARD, True) for _ in range(2) for deal, _ in game_for().deals
    ]
    deals += [(HANDS[0][index], HANDS[1][index], CHANGED_BOARD, False) for index in (0, 1)]
    deals += [(UNSUPPORTED[0], HANDS[1][index], BOARD, False) for index in (0, 1)]
    for index, (first, second, board, supported) in enumerate(deals):
        deal = complete_deal(first, second, board)
        save(
            f"sessions/d{index}-s1-l0.json",
            dict(
                version="pontius-v0a-table-session-v1",
                button=0,
                controlled_seat=1,
                starting_stacks=[200] * 6,
                small_blind=1,
                big_blind=2,
                opponents=[
                    "fold_to_bet",
                    None,
                    "passive",
                    "fold_to_bet",
                    "fold_to_bet",
                    "fold_to_bet",
                ],
                hands=[
                    dict(
                        private_hands=[list(hand) for hand in deal.private_hands],
                        board_runout=list(board),
                    )
                ],
            ),
        )
        label = f"native-river-{index}"
        cases[label] = (deal, supported)
        cells.append(
            dict(
                id=label,
                runtime="3.14",
                kind="session",
                size=13,
                argv=[],
                parameters=dict(
                    deal=index,
                    seat=1,
                    lineup=0,
                    strategy="blueprint-v1",
                    diagnostic=False,
                    session_id="pontius-v0a-table-session-v1-correctness-" + label,
                ),
            )
        )
    request = dict(
        population_root=str(population),
        population={"artifacts": [{"size": 13}]},
        selections={},
        input_hashes=identities,
        cells=cells,
    )
    measured = controller.supervise(request, context, seconds, 3072 * 1024 * 1024)
    measured["input_hashes"] = identities
    # Retain interrupted/failed worker results before assessment can raise.
    (directory / "sessions.json").write_bytes(encode(measured))
    assert measured["status"] == "completed", measured.get("errors")
    assert measured["completed"] == len(cells) and measured["cleanup_verified"]
    indexed = {entry.key: entry.action for entry in source.entries}
    timings, hand_compute, learned_actions = [], [], []
    hits = misses = 0
    for cell in measured["cells"]:
        deal, supported = cases[cell["id"]]
        session = cell["observation"]["session"]
        assert session["status"] == "completed" and session["completed_hands"] == 1
        result = session["hands"][0]["result"]
        events = [
            json.loads(line)
            for line in base64.b64decode(result["child_stdout_base64"]).splitlines()
        ]
        decisions = iter(event["decision"] for event in events if event.get("decision"))
        ledger = next(event for event in events if event["type"] == "hand_result")
        assert ledger["accounting_complete"]
        closing = next(event for event in events if event["type"] == "session_result")
        assert closing["accounting_complete"]
        charged = ledger["preparation_compute_seconds"]
        state = base_state()
        for row in result["applied_actions"]:
            while state.round_complete:
                state = state.advance_street()
            assert row["seat"] == state.acting_seat and row["street"] == state.street.value
            action = HandAction(**row["action"]).to_betting_action()
            if row["origin"] == "bot":
                decision = next(decisions)
                assert decision["selected_action"] == row["action"]
                key = key_for(state, 1, deal.hand(1), deal.public_cards(state.street))
                expected = indexed.get(key)
                hit = expected is not None
                assert decision["selection_reason"] == ("table_hit" if hit else "passive_default")
                if isinstance(expected, WeightedBlueprintAction):
                    assert action in dict(expected.choices)
                else:
                    assert action == (expected or passive_blueprint_action(state.legal_decision()))
                if state.street.value == "river":
                    assert hit == supported
                    learned_actions.append(action.kind.value) if hit else None
                    hits += int(hit)
                    misses += int(not hit)
                timing = decision["timing"]
                assert timing["status"] == "completed"
                assert not timing["work_cutoff_crossed"] and not timing["deadline_crossed"]
                timings.append(timing["elapsed_ns"] / 1e6)
                charged += timing["response_compute_seconds"]
            else:
                expected = (
                    (CALL if state.legal_decision().can_call else CHECK)
                    if row["seat"] == 2
                    else FOLD
                )
                assert action == expected
            state = state.apply_action(action)
        assert next(decisions, None) is None
        while not state.is_terminal and state.round_complete:
            state = state.advance_street()
        strengths = deal.showdown_strengths(state.live_seats) if state.showdown_ready else None
        expected = state.settle(strengths)
        assert result["settlement"]["payouts"] == list(expected.payouts)
        assert result["settlement"]["final_stacks"] == list(expected.final_stacks)
        assert sum(expected.final_stacks) == 1200
        hand_compute.append(charged * 1000)
    assert hits == 32 and misses == 4
    return dict(
        sessions=len(cells),
        learned_hits=hits,
        unsupported_misses=misses,
        learned_actions={name: learned_actions.count(name) for name in set(learned_actions)},
        response_ms=timings,
        charged_hand_compute_ms=hand_compute,
        max_response_ms=max(timings),
        max_charged_hand_compute_ms=max(hand_compute),
        cleanup_verified=True,
    )


def native_run(args, started, context, directory, driver_hash, retain, retained):
    design = dict(
        teacher_run="ab92e996889a41a08c8c3f4e75d54b1f",
        denominator=2**20,
        maximum_probability_error=1 / 2**20,
        maximum_export_nashconv_increase=0.08,
        draws_per_key=20000,
        maximum_frequency_error=0.015,
        sessions=36,
        session_population="32 supported bettor cases, four changed board/hand misses",
        direct_hands=100,
        direct_population="16 deals x 2 roles x 3 opponents + four misses",
        limitation="Fixed river game; system-random sessions do not estimate win rate or tails",
    )
    retain("design.json", design)
    report = dict(
        status="failed", experiment_sha256=driver_hash, source_verified=context["verified"]
    )
    try:
        teacher_raw = (
            ROOT / "experiments/results/runs" / design["teacher_run"] / "teacher.json"
        ).read_bytes()
        assert (
            hashlib.sha256(teacher_raw).hexdigest()
            == "7874807b9523ee47ebd30a5c943a883a7dc7d6cde076bff76e8ade038ed54791"
        )
        teacher = json.loads(teacher_raw)
        retain("teacher.json", teacher_raw)
        game = game_for()
        raw, source, recovered, choices = native_export(game, teacher)
        retain("blueprint.json", raw)
        retain("recovered-policy.json", recovered)
        probability_error = max(
            abs(recovered[key][name] - value)
            for key in teacher
            for name, value in teacher[key].items()
        )
        assert probability_error <= design["maximum_probability_error"]
        metrics = {
            name: asdict(evaluate_profile(game, policy))
            for name, policy in (
                ("teacher", teacher),
                ("native_export", recovered),
                ("argmax", deterministic(teacher)),
            )
        }
        loss = metrics["native_export"]["nash_conv"] - metrics["teacher"]["nash_conv"]
        report.update(
            evaluations=metrics,
            quality=dict(
                maximum_probability_error=probability_error, export_nashconv_increase=loss
            ),
            artifact_bytes=len(raw),
            artifact_entries=len(source.entries),
        )
        assert loss <= design["maximum_export_nashconv_increase"]
        frequencies = {}
        for key, distribution in choices.items():
            counts = {action: 0 for action, _ in distribution.choices}
            for _ in range(design["draws_per_key"]):
                counts[distribution.sample()] += 1
            frequencies[key] = {
                name: counts.get(concrete(name), 0) / design["draws_per_key"]
                for name in recovered[key]
            }
        error = max(
            abs(frequencies[key][name] - recovered[key][name])
            for key in frequencies
            for name in frequencies[key]
        )
        retain("sampling.json", dict(frequencies=frequencies, maximum_frequency_error=error))
        assert error <= design["maximum_frequency_error"]
        hands = []
        projected = deterministic(teacher)
        for deal, _ in game.deals:
            for player in (0, 1):
                for mode in ("projected", "aggressive", "passive"):
                    hand = play(
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
                        native=True,
                    )
                    abstract = game.initial_state().apply_action(deal)
                    selected = iter(row for row in hand["decisions"] if row["modeled"])
                    while not abstract.terminal:
                        acting = abstract.current_player
                        if acting == player:
                            name = next(selected)["action"]["kind"]
                            action = "bet" if name == "raise" else name
                        elif mode == "projected":
                            action = action_for(game, projected, acting, deal.hand(acting))
                        else:
                            action = (
                                ("bet" if mode == "aggressive" else "check")
                                if acting == 0
                                else ("call" if mode == "aggressive" else "fold")
                            )
                        abstract = abstract.apply_action(action)
                    assert hand["river_utility"] == abstract.returns()[player]
                    hands.append(hand)
        for player in (0, 1):
            for changed in ("board", "hand"):
                first, second = HANDS[0][0], HANDS[1][0]
                if changed == "hand":
                    first, second = (
                        (UNSUPPORTED[0], second) if player == 0 else (first, UNSUPPORTED[1])
                    )
                hands.append(
                    play(
                        source,
                        game,
                        projected,
                        first,
                        second,
                        player,
                        "aggressive",
                        CHANGED_BOARD if changed == "board" else BOARD,
                        context["source_sha256"],
                        False,
                        native=True,
                    )
                )
        retain("runtime-hands.json", hands)
        assert len(hands) == design["direct_hands"]
        remaining = args.seconds - (time.perf_counter() - started)
        if remaining <= 0:
            raise TimeoutError("Native session budget exhausted before launch")
        report["sessions"] = native_sessions(source, raw, context, directory, remaining)
        report.update(
            status="completed",
            direct_hands=len(hands),
            sampling_maximum_error=error,
            quality_preserved=True,
        )
    except Exception as error:
        report.update(error=f"{type(error).__name__}: {error}")
    if (directory / "sessions.json").exists():
        retained["sessions.json"] = hashlib.sha256(
            (directory / "sessions.json").read_bytes()
        ).hexdigest()
    report.update(retained_hashes=retained, total_seconds=time.perf_counter() - started)
    report["summary"] = (
        f"Native mixed river: {report['status']}; quality={report.get('quality_preserved')}; "
        f"sessions={report.get('sessions', {}).get('sessions', 0)}/36"
    )
    finish_run(
        context,
        "2026-09-08-trained-river-blueprint --native --development",
        report,
        report["total_seconds"],
    )
    print(
        json.dumps(
            dict(
                result=str(directory / "result.json"),
                summary=report["summary"],
                error=report.get("error"),
            )
        )
    )
    return 0 if report["status"] == "completed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument(
        "--native", action="store_true", help="Test native weighted codec and real sessions"
    )
    parser.add_argument(
        "--development", action="store_true", help="Record an unreviewed source change"
    )
    parser.add_argument(
        "--mixed",
        action="store_true",
        help="Test the retained teacher with weighted export and per-hand sampling",
    )
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 14) or args.seconds <= 0:
        parser.error("Use Python 3.14 and a positive budget")
    started = time.perf_counter()
    context = begin_run(ROOT, allow_working_tree=args.development)
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
    if args.native:
        return native_run(args, started, context, directory, driver_hash, retain, retained)
    if args.mixed:
        return mixed_run(args, started, context, directory, driver_hash, retain, retained)
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
