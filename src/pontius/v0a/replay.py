"""Explicit-deal fixture host, isolated mailbox, and terminal verifier.

The host owns the complete deal and the future schedule; the runtime never
sees either. Settlement is judged by an independent chip-depth oracle that
never calls production pot assembly, per the ADR-0287 gate reused here as an
engineering control.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import permutations

from ..holdem_cards import OneSeatCardState, SixSeatHoldemDeal
from ..immutable_blueprint import ImmutableBlueprintActionSource
from ..legal_decision_spine_v2 import public_betting_state_sha256
from ..no_limit_betting import SEAT_COUNT, BettingStreet, NoLimitBettingState, TerminalReason
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
    visible_cards_sha256,
)
from .clock import ClockInvalidError, ClockReversedError
from .runtime import HandRuntime, OperationFailed, _admit_blueprint
from .trace import (
    TraceBuilder,
    TraceInvalidError,
    TraceWriteError,
    parse_trace,
    TraceWriter,
    semantic_sha256,
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
            # A folded-only depth boundary does not change who may win.
            # Combine it before division so it cannot manufacture odd chips.
            if pots and pots[-1][1] == eligible:
                pots[-1] = (pots[-1][0] + amount, eligible)
            else:
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
        # Fixture/deal admission is declared pre-run setup. Header identity
        # computation and serialization begin only inside run's public ledger.
        self._header_arguments = dict(
            run_id=run_id, mode=mode, source_commit=source_commit,
            source_manifest_sha256=source_manifest_sha256, clock_kind=clock_kind,
        )
        self._builder: TraceBuilder | None = None

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
        """Measure host work and publish required rows before acquiring more input."""
        runtime, fixture = self._runtime, self._fixture
        builder = None
        writer = None
        writer_closed = False
        reported_close_errors = ()
        stream_usable = True
        file_requested = destination is not None or run_root is not None
        decisions: list[DecisionRecord] = []
        failures: list[FailureRecord] = []
        accepted_events: list[object] = []
        iterator = None
        header_attempted = False

        def new_builder():
            return TraceBuilder(
                **self._header_arguments,
                configuration_sha256=fixture.configuration_sha256(),
                blueprint_sha256=runtime.blueprint_sha256,
            )

        def close_stream():
            nonlocal writer_closed, reported_close_errors
            if writer is None:
                return ()
            if not writer_closed:
                writer_closed = True
                try:
                    writer.close()
                except BaseException as closing_error:
                    # The native owner retains every actual close failure.
                    # Unexpected callback/source errors still cross normally.
                    if not any(item is closing_error for item in writer.close_errors):
                        raise
            pending = tuple(error for error in writer.close_errors
                            if not any(error is prior for prior in reported_close_errors))
            reported_close_errors += pending
            return pending

        def flush_rows():
            nonlocal writer
            pending = builder.take_pending()
            if not file_requested:
                return
            if destination is None or run_root is None:
                raise TraceWriteError("file publication requires both destination and run root")
            if writer is None:
                # The owner exists before native acquisition starts.
                writer = TraceWriter(destination, run_root=run_root)
            writer.append(pending)

        try:
            runtime.begin_host_accounting()
            with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED,
                                           required=True):
                header_attempted = True
                builder = new_builder()
                iterator = iter(self._events())
        except OperationFailed:
            stream_usable = False
        if builder is None and not header_attempted:
            # Source failure before ordinary work may still produce an honest
            # in-memory failure report. No file/digest/accounting success follows.
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED):
                    builder = new_builder()
            except OperationFailed:
                pass
        self._builder = builder

        def feed(event):
            nonlocal stream_usable
            outcome = runtime.dispatch(event)
            retained = False

            def retain_and_serialize():
                nonlocal retained
                if outcome.status != "failed":
                    accepted_events.append(event)
                if outcome.failure is not None:
                    failures.append(outcome.failure)
                if outcome.decision is not None:
                    decisions.append(outcome.decision)
                # Retention precedes serialization: a serializer/write failure
                # cannot erase an action the real mailbox already accepted.
                retained = True
                if outcome.status != "failed":
                    builder.add_event(event)
                if outcome.failure is not None:
                    builder.add_failure(outcome.failure)
                if outcome.decision is not None:
                    builder.add_decision(outcome.decision)

            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED,
                                               required=True):
                    retain_and_serialize()
                    flush_rows()
            except OperationFailed:
                stream_usable = False
                if not retained:
                    # Required entry failed after dispatch. This separate
                    # optional path reports already observed outcomes only;
                    # it never acquires input or publishes unmeasured rows.
                    try:
                        with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED):
                            retain_and_serialize()
                    except OperationFailed:
                        pass
                # The body cause was retained before this later cleanup.
                try:
                    with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED,
                                                   cleanup=close_stream):
                        pass
                except OperationFailed:
                    pass
            return outcome.status != "failed" and not runtime.closure_failures and stream_usable

        exhausted = object()
        while iterator is not None and not runtime.closure_failures:
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.INVALID_EVENT,
                                               required=True):
                    event = next(iterator, exhausted)
            except OperationFailed:
                stream_usable = False
                break
            if event is exhausted or runtime.closure_failures or not feed(event):
                break

        # Event construction/evaluation is host preparation, never response
        # work. All-in runout still closes each actual street boundary.
        streets = tuple(BettingStreet)
        while (not runtime.closure_failures and runtime.state is not None
               and not runtime.state.is_terminal and runtime.state.round_complete
               and runtime.state.street is not BettingStreet.RIVER):
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.INVALID_EVENT,
                                               required=True):
                    following = streets[streets.index(runtime.state.street) + 1]
                    event = StreetRevealedEvent(
                        hand_id=fixture.hand_id, event_index=len(accepted_events),
                        street=following.value, cards=tuple(self._deal.reveal_for(following)),
                    )
            except OperationFailed:
                stream_usable = False
                break
            if runtime.closure_failures or not feed(event):
                break

        state = runtime.state
        needs_showdown = state is not None and (
            (state.is_terminal and state.terminal_reason is TerminalReason.SHOWDOWN)
            or (not state.is_terminal and state.round_complete and state.street is BettingStreet.RIVER)
        )
        if not runtime.closure_failures and needs_showdown:
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.INVALID_EVENT,
                                               required=True):
                    event = ShowdownResultEvent(
                        hand_id=fixture.hand_id, event_index=len(accepted_events),
                        strengths=tuple(self._deal.showdown_strengths(state.live_seats)),
                    )
            except OperationFailed:
                stream_usable = False
            else:
                if not runtime.closure_failures:
                    feed(event)

        # Exhaustion is lawful only after automatic runout/showdown has had
        # its chance to finish the hand. Keep all deliveries already accepted.
        if not runtime.closure_failures and not runtime.betting_terminal:
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.EVENT_ORDER,
                                               required=True):
                    runtime.record(FailureCode.EVENT_ORDER)
            except OperationFailed:
                stream_usable = False

        settlement: SettlementRecord | None = None
        oracle_payouts: tuple[int, ...] | None = None
        if not runtime.closure_failures and runtime.betting_terminal:
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.SETTLEMENT_MISMATCH,
                                               required=True):
                    settlement = runtime.settle()
                    state = runtime.state
                    assert state is not None
                    strengths = (None if state.terminal_reason is TerminalReason.FOLD
                                 else tuple(self._deal.showdown_strengths(state.live_seats)))
                    oracle = self._oracle(total_contributions=state.total_contributions,
                        folded=state.folded, starting_stacks=state.starting_stacks,
                        strengths=strengths, button=state.button)
                    oracle_payouts = oracle.payouts
                    if (oracle.payouts != settlement.payouts
                            or oracle.final_stacks != settlement.final_stacks
                            or tuple((pot.amount, pot.seats) for pot in settlement.pots) != oracle.pots
                            or sum(settlement.payouts) != sum(state.total_contributions)
                            or sum(settlement.final_stacks) != sum(state.starting_stacks)):
                        runtime.record(FailureCode.SETTLEMENT_MISMATCH)
            except OperationFailed:
                settlement = None

        # Compute semantics before sampling the terminal cut. If this interval
        # dies, a failed report may recompute the null-settlement projection;
        # it cannot claim measurement or successful publication.
        candidate_pass = (not runtime.closure_failures and runtime.betting_terminal
                          and settlement is not None and runtime.accounting().complete)
        semantic_digest = ""
        try:
            with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED,
                                           required=candidate_pass):
                semantic_digest = semantic_sha256(events=tuple(accepted_events),
                    decisions=tuple(decisions), settlement=settlement if candidate_pass else None)
        except OperationFailed:
            stream_usable = False
        if candidate_pass and runtime.closure_failures:
            candidate_pass = False
            try:
                with runtime.owned_bookkeeping(body_failure=FailureCode.TRACE_WRITE_FAILED):
                    semantic_digest = semantic_sha256(events=tuple(accepted_events),
                                                       decisions=tuple(decisions), settlement=None)
            except OperationFailed:
                pass

        totals = runtime.accounting()
        journal = runtime.closure_failures
        primary = journal[0] if journal else None
        passed = candidate_pass and primary is None and totals.complete
        publication: list[float] = []
        content = b""
        trace_digest = None
        try:
            with runtime.owned_publication(publication,
                    body_failure=FailureCode.TRACE_WRITE_FAILED, cleanup=close_stream):
                if builder is not None:
                    content = builder.close(
                        hand_id=fixture.hand_id, complete=runtime.betting_terminal and primary is None,
                        passed=passed, failure_reason=primary, event_count=len(accepted_events),
                        decision_count=runtime.accepted_delivery_count,
                        interrupted_response_count=totals.interrupted_response_count,
                        accounting_complete=totals.complete, settlement=settlement if passed else None,
                        semantic_digest=semantic_digest,
                        preparation_compute_seconds=totals.preparation_compute_seconds,
                        post_terminal_compute_seconds=totals.post_terminal_compute_seconds,
                    )
                    if file_requested:
                        if stream_usable and runtime.measurable:
                            flush_rows()
                            trace_digest = writer.finish()
                            writer_closed = True
                    elif stream_usable and runtime.measurable:
                        trace_digest = sha256(content).hexdigest()
        except OperationFailed:
            trace_digest = None

        runtime.finalize_accounting()
        journal = runtime.closure_failures
        primary = journal[0] if journal else None
        closed = runtime.accounting()
        receipt = HostCompletionReceipt(
            run_id=self._run_id, hand_id=fixture.hand_id, trace_sha256=trace_digest,
            terminal_publication_compute_seconds=publication[0] if len(publication) == 1 else None,
            accounting_complete=closed.complete,
            passed=passed and primary is None and trace_digest is not None and closed.complete,
            failure_reason=primary, secondary_failures=tuple(journal[1:]),
        )
        return ReplayOutcome(receipt=receipt, trace=content, decisions=tuple(decisions),
            failures=tuple(failures), settlement=settlement, oracle_payouts=oracle_payouts,
            semantic_digest=semantic_digest)


# -- accepting replay, independent of the producer's orchestration ----------


@dataclass(frozen=True, slots=True)
class VerifiedTrace:
    """A legal, timely trace; no claim about host publication or source sealing."""

    run_id: str
    semantic_sha256: str
    payouts: tuple[int, ...]
    final_stacks: tuple[int, ...]
    pots: tuple[tuple[int, tuple[int, ...]], ...]


def _owned_expected_fixture(fixture: object) -> Fixture:
    """Admit value-only expectations before calling any fixture behavior."""
    if type(fixture) is not Fixture:
        raise TraceInvalidError("expected fixture must be exact")
    for key in ("name", "seed_label", "hand_id"):
        if type(getattr(fixture, key)) is not str or not getattr(fixture, key):
            raise TraceInvalidError(f"expected fixture {key} must be nonempty text")
    for key in ("button", "controlled_seat", "small_blind", "big_blind",
                "expected_controlled_actions"):
        if type(getattr(fixture, key)) is not int:
            raise TraceInvalidError(f"expected fixture {key} must be an exact integer")
    if fixture.controlled_seat not in range(SEAT_COUNT):
        raise TraceInvalidError("expected controlled seat must identify one of six seats")
    for key, kind in (("starting_stacks", int), ("board_text", str), ("hand_text", str),
                      ("expected_payouts", int), ("expected_pots", int)):
        value = getattr(fixture, key)
        if type(value) is not tuple or any(type(item) is not kind for item in value):
            raise TraceInvalidError(f"expected fixture {key} must contain exact immutable values")
    if type(fixture.script) is not tuple:
        raise TraceInvalidError("expected script must be an exact tuple")
    script = []
    for step in fixture.script:
        if (type(step) is not ScriptedAction or type(step.street) is not str
                or type(step.kind) is not str or type(step.seat) is not int
                or (step.raise_to is not None and type(step.raise_to) is not int)):
            raise TraceInvalidError("expected script requires exact action values")
        script.append(ScriptedAction(step.street, step.seat, step.kind, step.raise_to))
    return Fixture(
        name=fixture.name, seed_label=fixture.seed_label, hand_id=fixture.hand_id,
        button=fixture.button, controlled_seat=fixture.controlled_seat,
        starting_stacks=fixture.starting_stacks, small_blind=fixture.small_blind,
        big_blind=fixture.big_blind, board_text=fixture.board_text, hand_text=fixture.hand_text,
        script=tuple(script), expected_payouts=fixture.expected_payouts,
        expected_pots=fixture.expected_pots,
        expected_controlled_actions=fixture.expected_controlled_actions,
    )


def verify_successful_trace(
    content: bytes,
    *,
    fixture: Fixture,
    blueprint: object,
    source_commit: str,
    source_manifest_sha256: str,
    expected_mode: str,
    expected_clock_kind: str,
) -> VerifiedTrace:
    """Accept raw bytes only after replay against independently supplied bindings.

    Parsing does not grant acceptance. This checker owns its betting/card state,
    compares the full expected event schedule, calls the sealed blueprint lookup
    directly, and judges settlement by chip depth. It never dispatches a runtime,
    runs a host, uses its selector, trusts a caller hook or deserializes behavior.
    Timing consistency is checked; actual measured-work completeness, source seal
    and host publication/finalization remain outside a trace-only proof.
    """
    parsed = parse_trace(content)
    if not parsed.terminal["passed"] or not parsed.terminal["complete"]:
        raise TraceInvalidError("a failed or incomplete prefix cannot earn successful replay")
    for value, label in ((source_commit, "source commit"),
                         (source_manifest_sha256, "source manifest"),
                         (expected_mode, "mode"), (expected_clock_kind, "clock kind")):
        if type(value) is not str:
            raise TraceInvalidError(f"expected {label} must be exact text")
    expected = _owned_expected_fixture(fixture)
    try:
        policy = _admit_blueprint(blueprint)
        deal = expected.deal()
        bindings = {
            "source_commit": source_commit,
            "source_manifest_sha256": source_manifest_sha256,
            "configuration_sha256": expected.configuration_sha256(),
            "blueprint_sha256": policy.digest,
            "mode": expected_mode,
            "clock_kind": expected_clock_kind,
        }
        if any(parsed.header[key] != value for key, value in bindings.items()):
            raise TraceInvalidError("trace header disagrees with independently expected bindings")
        if not parsed.run_id.startswith(f"{PROTOCOL_ID}-{expected_mode}-"):
            raise TraceInvalidError("trace run identity disagrees with its expected mode")
        if parsed.terminal["hand_id"] != expected.hand_id:
            raise TraceInvalidError("terminal hand differs from the bound fixture")
        return _replay_parsed_success(parsed, expected, deal, policy)
    except (TypeError, ValueError, AssertionError, OverflowError) as error:
        if isinstance(error, TraceInvalidError):
            raise
        raise TraceInvalidError("trace or expected values cannot produce a legal replay") from error


def _replay_parsed_success(parsed, fixture, deal, policy) -> VerifiedTrace:
    state = None
    cards = None
    strengths = None
    script_index = action_index = street_action_index = 0
    trigger_index = None
    awaiting_decision = False
    policy_digest = policy.digest
    for row in parsed.records[1:-1]:
        if row["record_type"] == "event":
            if awaiting_decision:
                raise TraceInvalidError("event overtook a required controlled decision")
            event = row["event"]
            if event["hand_id"] != fixture.hand_id:
                raise TraceInvalidError("event hand differs from the bound fixture")
            kind = event["kind"]
            if kind == "hand_started":
                wanted = {
                    "button": fixture.button, "controlled_seat": fixture.controlled_seat,
                    "starting_stacks": fixture.starting_stacks, "small_blind": fixture.small_blind,
                    "big_blind": fixture.big_blind,
                    "private_cards": tuple(deal.hand(fixture.controlled_seat)),
                }
                if any(event[key] != value for key, value in wanted.items()):
                    raise TraceInvalidError("initial event differs from the bound fixture")
                state = NoLimitBettingState.new_hand(
                    button=fixture.button, starting_stacks=fixture.starting_stacks,
                    small_blind=fixture.small_blind, big_blind=fixture.big_blind,
                )
                cards = OneSeatCardState.preflop(
                    controlled_seat=fixture.controlled_seat, private_hand=event["private_cards"]
                )
            elif state is None or (state.is_terminal and not (
                    kind == "showdown_result" and strengths is None
                    and state.terminal_reason is TerminalReason.SHOWDOWN)):
                raise TraceInvalidError("event is outside an active hand")
            elif kind == "opponent_action":
                if script_index >= len(fixture.script):
                    raise TraceInvalidError("extra opponent action beyond the bound script")
                step = fixture.script[script_index]
                if (event["street"] != state.street.value or event["street"] != step.street
                        or event["seat"] != state.acting_seat or event["seat"] != step.seat
                        or event["seat"] == fixture.controlled_seat
                        or event["action"] != {"kind": step.kind, "raise_to": step.raise_to}):
                    raise TraceInvalidError("opponent action disagrees with the legal bound schedule")
                state = state.apply_action(HandAction(**event["action"]).to_betting_action())
                script_index += 1
            elif kind == "street_revealed":
                street = BettingStreet(event["street"])
                if event["cards"] != tuple(deal.reveal_for(street)):
                    raise TraceInvalidError("reveal disagrees with the bound full deal")
                cards = cards.advance_to(street, event["cards"])
                state = state.advance_street()
                if state.street is not street:
                    raise TraceInvalidError("reveal and legal street transition disagree")
                street_action_index = 0
            elif kind == "showdown_result":
                if state.street is not BettingStreet.RIVER or not state.round_complete:
                    raise TraceInvalidError("showdown arrived before the river completed")
                strengths = tuple(deal.showdown_strengths(state.live_seats))
                if event["strengths"] != strengths:
                    raise TraceInvalidError("showdown ranks disagree with the full bound deal")
                if not state.is_terminal:
                    state = state.advance_street()
            trigger_index = event["event_index"]
            awaiting_decision = state.acting_seat == fixture.controlled_seat
        elif row["record_type"] == "decision":
            if not awaiting_decision or state is None or cards is None:
                raise TraceInvalidError("decision arrived without its controlled turn")
            selection = ImmutableBlueprintActionSource.action_for(
                policy, cards=cards, betting=state, decision=state.legal_decision()
            )
            action_index += 1
            street_action_index += 1
            after = state.apply_action(selection.action)
            wanted = {
                "hand_id": fixture.hand_id, "event_index": trigger_index,
                "action_index": action_index, "street_action_index": street_action_index,
                "seat": fixture.controlled_seat, "street": state.street.value,
                "state_before_sha256": public_betting_state_sha256(state),
                "state_after_sha256": public_betting_state_sha256(after),
                "visible_cards_sha256": visible_cards_sha256(cards),
                "blueprint_sha256": policy_digest,
                "selected_action": {"kind": selection.action.kind.value,
                                    "raise_to": selection.action.raise_to},
                "selection_reason": "table_hit" if selection.table_hit else "passive_default",
                "spine_reason": "no_candidate", "failure_reason": None,
            }
            if any(row[key] != value for key, value in wanted.items()):
                raise TraceInvalidError("decision disagrees with independently replayed state/policy")
            state = after
            awaiting_decision = False
        else:
            raise TraceInvalidError("successful replay has only event and decision rows")
    if (state is None or not state.is_terminal or awaiting_decision
            or script_index != len(fixture.script)
            or action_index != fixture.expected_controlled_actions
            or (state.terminal_reason is TerminalReason.SHOWDOWN and strengths is None)):
        raise TraceInvalidError("trace stopped before its complete legal bound schedule")
    oracle = chip_depth_settlement(
        total_contributions=state.total_contributions, folded=state.folded,
        starting_stacks=state.starting_stacks, strengths=strengths, button=state.button,
    )
    settlement = parsed.terminal["settlement"]
    if (settlement["payouts"] != oracle.payouts
            or settlement["final_stacks"] != oracle.final_stacks
            or tuple((pot["amount"], pot["seats"]) for pot in settlement["pots"]) != oracle.pots
            or oracle.payouts != fixture.expected_payouts
            or tuple(pot[0] for pot in oracle.pots) != fixture.expected_pots):
        raise TraceInvalidError("terminal settlement disagrees with independent chip-depth judgment")
    return VerifiedTrace(parsed.run_id, parsed.terminal["semantic_sha256"],
                         oracle.payouts, oracle.final_stacks, oracle.pots)


__all__ = [
    "FIXTURES",
    "FIXTURE_A",
    "FIXTURE_B",
    "Fixture",
    "HostCompletionReceipt",
    "PROTOCOL_ID",
    "ReplayHost",
    "ReplayOutcome",
    "VerifiedTrace",
    "verify_successful_trace",
    "ScriptedAction",
    "OracleSettlement",
    "chip_depth_settlement",
    "permutation_for_label",
    "rename_card",
    "suit_mapping",
]
