"""Explicit-deal fixture host, isolated mailbox, and terminal verifier.

The host owns the complete deal and the future schedule; the runtime never
sees either. Settlement is judged by an independent chip-depth oracle that
never calls production pot assembly, per the ADR-0287 gate reused here as an
engineering control.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from itertools import permutations

from ..holdem_cards import SixSeatHoldemDeal
from ..no_limit_betting import SEAT_COUNT, BettingStreet, TerminalReason
from ..river import RANKS, SUITS, parse_card
from .model import (
    ActionMailbox,
    DecisionRecord,
    FailureCode,
    FailureRecord,
    HandAction,
    HandStartedEvent,
    OpponentActionEvent,
    PotRecord,
    SettlementRecord,
    ShowdownResultEvent,
    StreetRevealedEvent,
)
from .clock import ClockInvalidError, ClockReversedError
from .runtime import HandRuntime
from .trace import (
    TraceBuilder,
    TraceWriteError,
    semantic_sha256,
    write_trace,
)

PROTOCOL_ID = "pontius-v0a-hand-replay-v1"


# -- seed-bound suit permutation -------------------------------------------


def permutation_for_label(label: str) -> str:
    """Disclosed deterministic suit renaming — not random sampling.

    Hash the UTF-8 label with SHA-256, read the first eight bytes as an
    unsigned big-endian integer, take modulo 24, and select that zero-based
    lexicographic permutation of ``cdhs``.
    """

    if not isinstance(label, str) or not label:
        raise ValueError("a seed label must be a nonempty string")
    digest = sha256(label.encode("utf-8")).digest()
    index = int.from_bytes(digest[:8], "big") % 24
    return "".join(sorted(permutations(SUITS))[index])


def rename_card(card: int, mapping: dict[str, str]) -> int:
    rank_index, suit_index = divmod(card, len(SUITS))
    return parse_card(RANKS[rank_index] + mapping[SUITS[suit_index]])


def suit_mapping(target: str) -> dict[str, str]:
    if len(target) != 4 or set(target) != set(SUITS):
        raise ValueError("a suit permutation must be a rearrangement of cdhs")
    return {source: target[position] for position, source in enumerate(SUITS)}


# -- fixtures ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScriptedAction:
    """One scripted opponent action in the fixture's frozen order."""

    street: str
    seat: int
    kind: str
    raise_to: int | None = None

    def action(self) -> HandAction:
        return HandAction(kind=self.kind, raise_to=self.raise_to)


@dataclass(frozen=True, slots=True)
class Fixture:
    """One explicit-deal control: deal, schedule, and independent expectations."""

    name: str
    seed_label: str
    hand_id: str
    button: int
    controlled_seat: int
    starting_stacks: tuple[int, ...]
    small_blind: int
    big_blind: int
    board_text: tuple[str, ...]
    hand_text: tuple[str, ...]
    script: tuple[ScriptedAction, ...]
    expected_payouts: tuple[int, ...]
    expected_pots: tuple[int, ...]
    expected_controlled_actions: int

    @property
    def permutation(self) -> str:
        return permutation_for_label(self.seed_label)

    def deal(self) -> SixSeatHoldemDeal:
        mapping = suit_mapping(self.permutation)
        board = tuple(rename_card(parse_card(card), mapping) for card in self.board_text)
        hands = tuple(
            tuple(sorted(rename_card(parse_card(card), mapping) for card in text.split()))
            for text in self.hand_text
        )
        return SixSeatHoldemDeal(private_hands=hands, board_runout=board)

    def configuration_sha256(self) -> str:
        """Bind the host's full sealed schedule; only this digest reaches the runtime."""

        deal = self.deal()
        payload = "|".join(
            (
                self.name,
                self.seed_label,
                self.permutation,
                self.hand_id,
                str(self.button),
                str(self.controlled_seat),
                ",".join(str(stack) for stack in self.starting_stacks),
                f"{self.small_blind}/{self.big_blind}",
                deal.digest,
                ";".join(
                    f"{step.street}:{step.seat}:{step.kind}:{step.raise_to}"
                    for step in self.script
                ),
            )
        )
        return sha256(payload.encode("utf-8")).hexdigest()


BOARD = ("2c", "7d", "9h", "Js", "Qc")

FIXTURE_A = Fixture(
    name="control-A",
    seed_label=f"{PROTOCOL_ID}/control-A",
    hand_id="control-A",
    button=0,
    controlled_seat=3,
    starting_stacks=(200,) * SEAT_COUNT,
    small_blind=1,
    big_blind=2,
    board_text=BOARD,
    hand_text=("As Ad", "Kh Kd", "Ts 8s", "Ks Td", "Ah 3h", "4s 5s"),
    script=(
        ScriptedAction("preflop", 4, "call"),
        ScriptedAction("preflop", 5, "call"),
        ScriptedAction("preflop", 0, "call"),
        ScriptedAction("preflop", 1, "call"),
        ScriptedAction("preflop", 2, "check"),
        ScriptedAction("flop", 1, "check"),
        ScriptedAction("flop", 2, "check"),
        ScriptedAction("flop", 4, "check"),
        ScriptedAction("flop", 5, "check"),
        ScriptedAction("flop", 0, "check"),
        ScriptedAction("turn", 1, "check"),
        ScriptedAction("turn", 2, "check"),
        ScriptedAction("turn", 4, "check"),
        ScriptedAction("turn", 5, "check"),
        ScriptedAction("turn", 0, "check"),
        ScriptedAction("river", 1, "check"),
        ScriptedAction("river", 2, "check"),
        ScriptedAction("river", 4, "check"),
        ScriptedAction("river", 5, "check"),
        ScriptedAction("river", 0, "check"),
    ),
    expected_payouts=(0, 0, 0, 12, 0, 0),
    expected_pots=(12,),
    expected_controlled_actions=4,
)

FIXTURE_B = Fixture(
    name="control-B",
    seed_label=f"{PROTOCOL_ID}/control-B",
    hand_id="control-B",
    button=0,
    controlled_seat=5,
    starting_stacks=(10, 6, 4, 20, 20, 20),
    small_blind=1,
    big_blind=2,
    board_text=BOARD,
    hand_text=("As Ad", "Th 8h", "Kc Tc", "Kh Kd", "Ah 3h", "4s 5s"),
    script=(
        ScriptedAction("preflop", 3, "raise", 10),
        ScriptedAction("preflop", 4, "call"),
        ScriptedAction("preflop", 0, "call"),
        ScriptedAction("preflop", 1, "call"),
        ScriptedAction("preflop", 2, "call"),
        ScriptedAction("flop", 3, "raise", 10),
        ScriptedAction("flop", 4, "call"),
    ),
    expected_payouts=(16, 10, 24, 30, 0, 0),
    expected_pots=(24, 10, 16, 30),
    expected_controlled_actions=2,
)

FIXTURES: tuple[Fixture, ...] = (FIXTURE_A, FIXTURE_B)


# -- independent settlement oracle -----------------------------------------


@dataclass(frozen=True, slots=True)
class OracleSettlement:
    """The independent judge's complete expectation for one terminal hand."""

    payouts: tuple[int, ...]
    final_stacks: tuple[int, ...]
    pots: tuple[tuple[int, tuple[int, ...]], ...]


def chip_depth_settlement(
    *,
    total_contributions: tuple[int, ...],
    folded: tuple[bool, ...],
    starting_stacks: tuple[int, ...],
    strengths: tuple[object, ...] | None,
    button: int,
) -> OracleSettlement:
    """Recompute pots and payouts from contribution depth alone.

    This oracle never calls production pot assembly; it exists so the
    production settlement has an independent judge.
    """

    levels = sorted({value for value in total_contributions if value > 0})
    pots: list[tuple[int, tuple[int, ...]]] = []
    lower = 0
    for level in levels:
        contributors = tuple(
            seat for seat in range(SEAT_COUNT) if total_contributions[seat] >= level
        )
        amount = (level - lower) * len(contributors)
        eligible = tuple(seat for seat in contributors if not folded[seat])
        if amount:
            pots.append((amount, eligible))
        lower = level

    payouts = [0] * SEAT_COUNT
    odd_order = tuple((button + offset) % SEAT_COUNT for offset in range(1, SEAT_COUNT + 1))
    for amount, eligible in pots:
        if not eligible:
            raise AssertionError("an oracle pot has no eligible seat")
        if strengths is None:
            winners = eligible
        else:
            best = max(strengths[seat] for seat in eligible)
            winners = tuple(seat for seat in eligible if strengths[seat] == best)
        share, odd = divmod(amount, len(winners))
        for winner in winners:
            payouts[winner] += share
        for winner in tuple(seat for seat in odd_order if seat in winners)[:odd]:
            payouts[winner] += 1

    if sum(payouts) != sum(total_contributions):
        raise AssertionError("oracle settlement does not conserve the pot")
    final = tuple(
        starting_stacks[seat] - total_contributions[seat] + payouts[seat]
        for seat in range(SEAT_COUNT)
    )
    if sum(final) != sum(starting_stacks):
        raise AssertionError("oracle settlement does not conserve table chips")
    return OracleSettlement(
        payouts=tuple(payouts), final_stacks=final, pots=tuple(pots)
    )


# -- host completion receipt -----------------------------------------------


@contextmanager
def _optional(context):
    """Enter a measurement context when one could be opened, else proceed."""

    if context is None:
        yield None
        return
    with context as value:
        yield value


@dataclass(frozen=True, slots=True)
class HostCompletionReceipt:
    """Returned outside the trace it describes; never self-measuring."""

    run_id: str
    hand_id: str | None
    trace_sha256: str | None
    terminal_publication_compute_seconds: float | None
    accounting_complete: bool
    passed: bool
    failure_reason: FailureCode | None
    secondary_failures: tuple[FailureCode, ...]


@dataclass(frozen=True, slots=True)
class ReplayOutcome:
    receipt: HostCompletionReceipt
    trace: bytes
    decisions: tuple[DecisionRecord, ...]
    failures: tuple[FailureRecord, ...]
    settlement: SettlementRecord | None
    oracle_payouts: tuple[int, ...] | None
    semantic_digest: str


class ReplayHost:
    """Owns the complete deal and schedule; feeds the runtime public events only."""

    def __init__(
        self,
        fixture: Fixture,
        *,
        run_id: str,
        blueprint: object,
        clock: object | None = None,
        mode: str = "correctness",
        source_commit: str = "0" * 40,
        source_manifest_sha256: str = "0" * 64,
        clock_kind: str = "deterministic_test",
        settlement_oracle=chip_depth_settlement,
        mailbox=None,
    ) -> None:
        if not run_id.startswith((f"{PROTOCOL_ID}-correctness-", f"{PROTOCOL_ID}-rehearsal-")):
            raise ValueError(
                "a replay run id must use a correctness or rehearsal identity; "
                "the production identity stays absent until its own authorization"
            )
        self._fixture = fixture
        self._run_id = run_id
        # The default is the real independent oracle; tests substitute a
        # deliberately wrong judge to prove the comparison actually fires.
        self._oracle = settlement_oracle
        self._deal = fixture.deal()
        self._mailbox = ActionMailbox() if mailbox is None else mailbox
        self._runtime = HandRuntime(
            blueprint=blueprint, mailbox=self._mailbox, clock=clock
        )
        self._builder = TraceBuilder(
            run_id=run_id,
            mode=mode,
            source_commit=source_commit,
            source_manifest_sha256=source_manifest_sha256,
            configuration_sha256=fixture.configuration_sha256(),
            blueprint_sha256=blueprint.digest,
            clock_kind=clock_kind,
        )

    @property
    def mailbox(self) -> ActionMailbox:
        return self._mailbox

    @property
    def runtime(self) -> HandRuntime:
        return self._runtime

    def _events(self):
        fixture = self._fixture
        yield HandStartedEvent(
            hand_id=fixture.hand_id,
            event_index=0,
            button=fixture.button,
            controlled_seat=fixture.controlled_seat,
            starting_stacks=fixture.starting_stacks,
            small_blind=fixture.small_blind,
            big_blind=fixture.big_blind,
            private_cards=tuple(self._deal.hand(fixture.controlled_seat)),
        )
        index = 1
        remaining = list(fixture.script)
        current = "preflop"
        while remaining:
            step = remaining[0]
            if step.street != current:
                street = BettingStreet(step.street)
                yield StreetRevealedEvent(
                    hand_id=fixture.hand_id,
                    event_index=index,
                    street=step.street,
                    cards=tuple(self._deal.reveal_for(street)),
                )
                index += 1
                current = step.street
                continue
            remaining.pop(0)
            yield OpponentActionEvent(
                hand_id=fixture.hand_id,
                event_index=index,
                street=step.street,
                seat=step.seat,
                action=step.action(),
            )
            index += 1

    def run(self, *, destination=None, run_root=None) -> ReplayOutcome:
        """Replay the fixture, verify settlement, and publish the terminal."""

        runtime = self._runtime
        fixture = self._fixture
        builder = self._builder
        decisions: list[DecisionRecord] = []
        failures: list[FailureRecord] = []
        accepted_events: list[object] = []
        def note(code: FailureCode) -> None:
            """Journal a host-detected cause at the moment it occurs."""

            runtime.record(code)

        for event in self._events():
            outcome = runtime.dispatch(event)
            if outcome.status == "failed":
                if outcome.failure is not None:
                    failures.append(outcome.failure)
                    builder.add_failure(outcome.failure)
                if outcome.decision is not None:
                    decisions.append(outcome.decision)
                    builder.add_decision(outcome.decision)
                break
            accepted_events.append(event)
            builder.add_event(event)
            if outcome.decision is not None:
                decisions.append(outcome.decision)
                builder.add_decision(outcome.decision)

        def feed(event: object) -> bool:
            outcome = runtime.dispatch(event)
            if outcome.status == "failed":
                if outcome.failure is not None:
                    failures.append(outcome.failure)
                    builder.add_failure(outcome.failure)
                if outcome.decision is not None:
                    decisions.append(outcome.decision)
                    builder.add_decision(outcome.decision)
                return False
            accepted_events.append(event)
            builder.add_event(event)
            if outcome.decision is not None:
                decisions.append(outcome.decision)
                builder.add_decision(outcome.decision)
            return True

        # All-in runout: streets with no actionable seat still reveal their
        # public cards and close their ledgers.
        streets = tuple(BettingStreet)
        while (
            not runtime.closure_failures
            and runtime.state is not None
            and not runtime.state.is_terminal
            and runtime.state.round_complete
            and runtime.state.street is not BettingStreet.RIVER
        ):
            following = streets[streets.index(runtime.state.street) + 1]
            if not feed(
                StreetRevealedEvent(
                    hand_id=fixture.hand_id,
                    event_index=len(accepted_events),
                    street=following.value,
                    cards=tuple(self._deal.reveal_for(following)),
                )
            ):
                break

        settlement: SettlementRecord | None = None
        oracle_payouts: tuple[int, ...] | None = None
        state = runtime.state
        needs_showdown = state is not None and (
            (state.is_terminal and state.terminal_reason is TerminalReason.SHOWDOWN)
            or (
                not state.is_terminal
                and state.round_complete
                and state.street is BettingStreet.RIVER
            )
        )
        if not runtime.closure_failures and needs_showdown:
            feed(
                ShowdownResultEvent(
                    hand_id=fixture.hand_id,
                    event_index=len(accepted_events),
                    strengths=tuple(self._deal.showdown_strengths(state.live_seats)),
                )
            )

        if not runtime.closure_failures and runtime.betting_terminal:
          try:
            with runtime.bookkeeping():
                settlement = runtime.settle()
                state = runtime.state
                assert state is not None
                strengths = (
                    None
                    if state.terminal_reason is TerminalReason.FOLD
                    else tuple(self._deal.showdown_strengths(state.live_seats))
                )
                oracle = self._oracle(
                    total_contributions=state.total_contributions,
                    folded=state.folded,
                    starting_stacks=state.starting_stacks,
                    strengths=strengths,
                    button=state.button,
                )
                oracle_payouts = oracle.payouts
                produced = tuple((pot.amount, pot.seats) for pot in settlement.pots)
                if (
                    oracle.payouts != settlement.payouts
                    or oracle.final_stacks != settlement.final_stacks
                    or produced != oracle.pots
                    or sum(settlement.payouts) != sum(state.total_contributions)
                    or sum(settlement.final_stacks) != sum(state.starting_stacks)
                ):
                    note(FailureCode.SETTLEMENT_MISMATCH)
          except (ClockInvalidError, ClockReversedError):
            # already journalled by the seam that raised it
            settlement = None
          except Exception:
            # Any other host-side failure is contained and typed rather
            # than escaping run(): an unhandled settlement or oracle error
            # would otherwise leave the caller with no receipt at all.
            note(FailureCode.SETTLEMENT_MISMATCH)
            settlement = None

        totals = runtime.accounting()
        journal = runtime.closure_failures
        primary = journal[0] if journal else None
        passed = (
            primary is None
            and runtime.betting_terminal
            and settlement is not None
            and totals.complete
        )
        semantic_digest = semantic_sha256(
            events=tuple(accepted_events),
            decisions=tuple(decisions),
            settlement=settlement if passed else None,
        )

        publication: list[float] = []
        content = b""
        publication_measured = True
        try:
            publication_context = runtime.publication_interval(publication)
        except RuntimeError:
            publication_context = None
        if publication_context is None:
            publication_measured = False
        with _optional(publication_context):
            content = builder.close(
                hand_id=fixture.hand_id,
                complete=runtime.betting_terminal and primary is None,
                passed=passed,
                failure_reason=primary,
                event_count=len(accepted_events),
                decision_count=runtime.accepted_delivery_count,
                interrupted_response_count=totals.interrupted_response_count,
                accounting_complete=totals.complete,
                settlement=settlement if passed else None,
                semantic_digest=semantic_digest,
                preparation_compute_seconds=totals.preparation_compute_seconds,
                post_terminal_compute_seconds=totals.post_terminal_compute_seconds,
            )
            trace_digest: str | None = None
            if destination is not None and run_root is not None:
                try:
                    trace_digest = write_trace(content, destination, run_root=run_root)
                except (TraceWriteError, OSError):
                    note(FailureCode.TRACE_WRITE_FAILED)
                    trace_digest = None
            else:
                trace_digest = sha256(content).hexdigest()

        runtime.finalize_accounting()
        journal = runtime.closure_failures
        primary = journal[0] if journal else None
        secondary = list(journal[1:])
        closed = runtime.accounting()
        if secondary or primary is not None or not closed.complete or not publication_measured:
            passed = False
        receipt = HostCompletionReceipt(
            run_id=self._run_id,
            hand_id=fixture.hand_id,
            trace_sha256=trace_digest,
            terminal_publication_compute_seconds=(
                publication[0] if len(publication) == 1 else None
            ),
            accounting_complete=closed.complete,
            passed=passed and trace_digest is not None and closed.complete,
            failure_reason=primary,
            secondary_failures=tuple(secondary),
        )
        return ReplayOutcome(
            receipt=receipt,
            trace=content,
            decisions=tuple(decisions),
            failures=tuple(failures),
            settlement=settlement,
            oracle_payouts=oracle_payouts,
            semantic_digest=semantic_digest,
        )


__all__ = [
    "FIXTURES",
    "FIXTURE_A",
    "FIXTURE_B",
    "Fixture",
    "HostCompletionReceipt",
    "PROTOCOL_ID",
    "ReplayHost",
    "ReplayOutcome",
    "ScriptedAction",
    "OracleSettlement",
    "chip_depth_settlement",
    "permutation_for_label",
    "rename_card",
    "suit_mapping",
]
