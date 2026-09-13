"""Fast N-player no-limit hold'em engine for MCCFR training and search.

Design goals, in order: correctness, speed, and a Pluribus-style *action
abstraction* — raises come from a configurable menu of pot-fraction sizes that
shrinks as a betting round gets raise-heavy (the paper used 1-14 sizes
depending on situation).

Conventions
-----------
- Chips are integers; small blind 1, big blind 2, default stacks 200 (100bb).
- Every hand resets stacks (as in the Pluribus experiments), so all players
  cover each other and no side pots arise; this is asserted, not assumed.
- Seats: 0 = small blind, 1 = big blind, last seat = button.
- Action ids: 0 FOLD, 1 CHECK/CALL, 2..2+k-1 the k raise-menu entries for the
  current situation, and ALL_IN as the final id (2+k).
- History strings use one token per action ('f', 'c', 'r<i>', 'a') with '/'
  between streets — the betting component of every infoset key.
"""
import random

from .evaluator import hand_rank

FOLD, CHECK_CALL = 0, 1
STREET_NAMES = ("preflop", "flop", "turn", "river")


class BetMenu:
    """Pot-fraction raise menu, thinned as raises pile up in a street.

    fractions[street] applies while the street has < cap raises; after that
    only `late_fraction` remains (plus all-in, always).
    """

    def __init__(self,
                 fractions=((1.0, 1.5, 2.5),        # preflop (of pot-after-call)
                            (0.33, 0.66, 1.0, 2.0),  # flop
                            (0.5, 1.0, 2.0),         # turn
                            (0.5, 1.0, 2.0)),        # river
                 cap=3, late_fraction=1.0):
        self.fractions = fractions
        self.cap = cap
        self.late_fraction = late_fraction

    def sizes(self, street: int, raises_this_street: int):
        if raises_this_street >= self.cap:
            return (self.late_fraction,)
        return self.fractions[street]


class NLHE:
    """One hand of no-limit hold'em. Create once, call reset() per hand."""

    def __init__(self, num_players=8, stack=200, sb=1, bb=2, menu=None, rng=None):
        # construction and other cold paths raise real exceptions (asserts
        # vanish under python -O); the per-action hot path keeps asserts
        if not 2 <= num_players <= 10:
            raise ValueError(f"num_players must be 2..10, got {num_players}")
        if not 0 < sb <= bb:
            raise ValueError(f"blinds must satisfy 0 < sb <= bb, "
                             f"got sb={sb} bb={bb}")
        if stack <= bb:
            raise ValueError(f"stack ({stack}) must cover the big blind ({bb})")
        self.n = num_players
        self.stack_size = stack
        self.sb, self.bb = sb, bb
        self.menu = menu or BetMenu()
        self.rng = rng or random.Random()

    # ------------------------------------------------------------------ setup
    def reset(self, deck=None):
        n = self.n
        if deck is None:
            deck = self.rng.sample(range(52), 2 * n + 5)
        else:
            need = 2 * n + 5
            if len(deck) < need:
                raise ValueError(f"deck needs at least {need} cards for "
                                 f"{n} players, got {len(deck)}")
            head = deck[:need]
            if len(set(head)) != need or not all(
                    isinstance(c, int) and 0 <= c <= 51 for c in head):
                raise ValueError("deck must contain unique card ints 0..51")
        self.holes = [deck[2 * i: 2 * i + 2] for i in range(n)]
        self.full_board = deck[2 * n: 2 * n + 5]
        self.street = 0
        self.folded = [False] * n
        self.stacks = [self.stack_size] * n
        self.committed = [0] * n          # total chips put in over the hand
        self.street_commit = [0] * n      # chips put in this street
        self.history = []                 # action tokens incl. '/' separators
        self.raises_this_street = 0
        self._winners = None

        self._pay(0, min(self.sb, self.stacks[0]))
        self._pay(1, min(self.bb, self.stacks[1]))
        self.cur_max = self.bb
        self.last_raise_inc = self.bb
        # cyclic order starting with first-to-act (UTG; heads-up: the SB/button)
        self.need_action = self._cycle_from(1)
        self.current = self.need_action[0]
        self._done = False
        return self

    def clone(self):
        """Cheap deep-enough copy for tree traversal (shares immutables)."""
        g = NLHE.__new__(NLHE)
        g.n, g.stack_size, g.sb, g.bb = self.n, self.stack_size, self.sb, self.bb
        g.menu, g.rng = self.menu, self.rng
        g.holes, g.full_board = self.holes, self.full_board  # cards never mutate
        g.street = self.street
        g.folded = self.folded[:]
        g.stacks = self.stacks[:]
        g.committed = self.committed[:]
        g.street_commit = self.street_commit[:]
        g.history = self.history[:]
        g.raises_this_street = self.raises_this_street
        g._winners = self._winners
        g.cur_max = self.cur_max
        g.last_raise_inc = self.last_raise_inc
        g.need_action = self.need_action[:]
        g.current = self.current
        g._done = self._done
        return g

    # ------------------------------------------------------------- inspection
    @property
    def board(self):
        shown = (0, 3, 4, 5)[self.street]
        return self.full_board[:shown]

    @property
    def pot(self):
        return sum(self.committed)

    def active_players(self):
        return [i for i in range(self.n) if not self.folded[i]]

    def is_over(self):
        return self._done

    def to_call(self, p):
        return min(self.cur_max - self.street_commit[p], self.stacks[p])

    def legal_actions(self):
        """Action ids for the current player. Raise menu ids depend on state."""
        p = self.current
        acts = []
        if self.to_call(p) > 0:
            acts.append(FOLD)
        acts.append(CHECK_CALL)
        sizes = self.menu.sizes(self.street, self.raises_this_street)
        n_raises = 0
        if self.stacks[p] > self.to_call(p):
            for i, frac in enumerate(sizes):
                raise_to = self._raise_to(p, frac)
                cost = raise_to - self.street_commit[p]
                if cost < self.stacks[p]:  # equal-to-stack collapses into all-in
                    acts.append(2 + i)
                    n_raises += 1
        if self.stacks[p] > self.to_call(p):
            # all-in only when it commits MORE than a call would (otherwise
            # it duplicates CHECK_CALL and splits strategy mass across twins)
            acts.append(2 + len(sizes))  # ALL_IN id is stable per situation
        return acts

    def all_in_action_id(self):
        return 2 + len(self.menu.sizes(self.street, self.raises_this_street))

    def _raise_to(self, p, frac):
        pot_after_call = self.pot + self.to_call(p)
        inc = max(int(round(frac * pot_after_call)), self.last_raise_inc)
        return self.cur_max + inc

    # ---------------------------------------------------------------- actions
    def _pay(self, p, amount):
        amount = min(amount, self.stacks[p])
        self.stacks[p] -= amount
        self.committed[p] += amount
        self.street_commit[p] += amount
        return amount

    def step(self, action):
        assert not self._done, "hand is over"
        p = self.current
        sizes = self.menu.sizes(self.street, self.raises_this_street)
        all_in_id = 2 + len(sizes)

        assert 0 <= action <= all_in_id, f"unknown action id {action}"
        if action == FOLD:
            assert self.to_call(p) > 0, "cannot fold when checking is free"
            self.folded[p] = True
            self.history.append("f")
            self._remove_from_queue(p)
            if len(self.active_players()) == 1:
                self._finish_fold_win()
                return
        elif action == CHECK_CALL:
            self._pay(p, self.to_call(p))
            self.history.append("c")
            self._remove_from_queue(p)
        else:
            if action == all_in_id:
                target = self.street_commit[p] + self.stacks[p]
                self.history.append("a")
            else:
                frac = sizes[action - 2]
                target = min(self._raise_to(p, frac),
                             self.street_commit[p] + self.stacks[p])
                self.history.append(f"r{action - 2}")
            cost = target - self.street_commit[p]
            assert cost > 0, "raise must put in chips"
            assert action == all_in_id or cost < self.stacks[p], \
                "menu raise reaching the full stack must use the all-in id"
            self._pay(p, cost)
            if self.street_commit[p] > self.cur_max:
                self.last_raise_inc = max(self.street_commit[p] - self.cur_max,
                                          self.last_raise_inc)
                self.cur_max = self.street_commit[p]
                self.raises_this_street += 1
                # a raise re-opens action for every other live, non-all-in
                # player. NOTE: an incomplete all-in raise (increment below
                # last_raise_inc) should NOT re-open raising in real NLHE, but
                # under this engine's equal-stack invariant every live player
                # starts a street with the same stack, so any all-in sets
                # cur_max to that shared total and re-queued players can only
                # ever call or fold — the deviation is unreachable. Revisit if
                # per-player stacks are ever introduced.
                self.need_action = [i for i in self._cycle_from(p)
                                    if not self.folded[i] and self.stacks[i] > 0
                                    and i != p]
            else:
                # defensive: unreachable via legal_actions() (every legal
                # raise/all-in commits above cur_max), kept for safety
                self._remove_from_queue(p)

        if self.stacks[p] == 0 and p in self.need_action:
            self.need_action.remove(p)

        if self.need_action:
            self.current = self.need_action[0]
        else:
            self._advance_street()

    def step_raise_to(self, target):
        """Chip-granular raise to an arbitrary street total (Phase D).

        For the REAL side of a dual real/abstract state: opponents off the
        bet menu (humans, other bots) raise to exact chip amounts here.
        History records 'x<target>', which is off the abstract tree —
        infoset_key() must never be queried on a state containing 'x'
        tokens; policy queries go through the shadow abstract state.
        """
        if self._done:
            raise ValueError("hand is over")
        p = self.current
        cost = target - self.street_commit[p]
        if not 0 < cost <= self.stacks[p]:
            raise ValueError(f"raise target {target} out of range for seat "
                             f"{p} (commit {self.street_commit[p]}, stack "
                             f"{self.stacks[p]})")
        if target <= self.cur_max:
            raise ValueError(f"raise to {target} does not exceed the current "
                             f"bet ({self.cur_max})")
        all_in = cost == self.stacks[p]
        if not all_in and target - self.cur_max < self.last_raise_inc:
            raise ValueError(f"increment {target - self.cur_max} below the "
                             f"min-raise ({self.last_raise_inc}) and not "
                             f"all-in")
        self.history.append(f"x{target}")
        self._pay(p, cost)
        self.last_raise_inc = max(self.street_commit[p] - self.cur_max,
                                  self.last_raise_inc)
        self.cur_max = self.street_commit[p]
        self.raises_this_street += 1
        self.need_action = [i for i in self._cycle_from(p)
                            if not self.folded[i] and self.stacks[i] > 0
                            and i != p]
        if self.stacks[p] == 0 and p in self.need_action:
            self.need_action.remove(p)
        if self.need_action:
            self.current = self.need_action[0]
        else:
            self._advance_street()

    def _remove_from_queue(self, p):
        if p in self.need_action:
            self.need_action.remove(p)

    def _cycle_from(self, p):
        return [(p + 1 + i) % self.n for i in range(self.n)]

    def _advance_street(self):
        # betting round complete
        live = self.active_players()
        can_act = [i for i in live if self.stacks[i] > 0]
        if self.street == 3 or len(can_act) <= 1:
            # showdown (dealing out any remaining board)
            self.street = 3
            self._finish_showdown()
            return
        self.street += 1
        self.history.append("/")
        self.street_commit = [0] * self.n
        self.cur_max = 0
        self.last_raise_inc = self.bb
        self.raises_this_street = 0
        # postflop order starts left of the button: seat 0 (SB) at 3+ handed
        # tables, but heads-up the SB *is* the button, so the BB (seat 1)
        # acts first and the button last
        start = 0 if self.n == 2 else self.n - 1
        self.need_action = [i for i in self._cycle_from(start)
                            if not self.folded[i] and self.stacks[i] > 0]
        if len(self.need_action) <= 1:
            self._advance_street()
            return
        self.current = self.need_action[0]

    # ------------------------------------------------------------- hand ends
    def _finish_fold_win(self):
        winner = self.active_players()[0]
        # refund any uncalled portion of the winner's last bet
        others_max = max((self.street_commit[i] for i in range(self.n)
                          if i != winner), default=0)
        excess = self.street_commit[winner] - max(others_max, 0)
        if excess > 0:
            self.stacks[winner] += excess
            self.committed[winner] -= excess
            self.street_commit[winner] -= excess
        self._winners = [winner]
        self._done = True

    def _finish_showdown(self):
        live = self.active_players()
        commits = {self.committed[i] for i in live}
        assert len(commits) == 1, f"side pot situation unexpected: {commits}"
        best, winners = None, []
        for i in live:
            score = hand_rank(self.holes[i] + self.full_board)
            if best is None or score > best:
                best, winners = score, [i]
            elif score == best:
                winners.append(i)
        self._winners = winners
        self._done = True

    def payoffs(self):
        """Chip result per seat (zero-sum). Call only when is_over()."""
        assert self._done
        result = [-c for c in self.committed]
        pot = self.pot
        share, rem = divmod(pot, len(self._winners))
        for k, w in enumerate(sorted(self._winners)):
            result[w] += share + (1 if k < rem else 0)
        return result

    # --------------------------------------------------------------- infosets
    def betting_string(self):
        return "".join(self.history)

    def infoset_key(self, bucket: int) -> str:
        """Key for the current player's infoset given their card bucket."""
        return f"{self.street}|{bucket}|{self.betting_string()}"
