"""7-card hand evaluation. Higher score = stronger hand.

Uses the C-backed `phevaluator` package when available (~1M evals/sec/core);
falls back to a correct pure-Python evaluator otherwise.
"""
from itertools import combinations

BACKEND = None
try:
    # Call the C extension directly: the public evaluate_cards wrapper re-validates
    # every card (isinstance + to_id) and costs ~6x the actual evaluation. Our card
    # ints are already phevaluator ids, so the wrapper adds nothing but time.
    from phevaluator import _pheval

    _eval7 = _pheval.evaluate_7cards

    def hand_rank(cards7) -> int:
        """phevaluator: 1 (royal flush) .. 7462 (worst). Negate so higher=better."""
        return -_eval7(*cards7)

    BACKEND = "phevaluator-c"
except (ImportError, AttributeError):
    try:
        from phevaluator import evaluate_cards as _phe

        def hand_rank(cards7) -> int:
            """phevaluator: 1 (royal flush) .. 7462 (worst). Negate so higher=better."""
            return -_phe(*cards7)

        BACKEND = "phevaluator"
    except ImportError:
        pass

if BACKEND is None:  # pure-Python fallback

    def _score5(cards):
        ranks = sorted((c // 4 for c in cards), reverse=True)
        suits = [c % 4 for c in cards]
        flush = len(set(suits)) == 1
        # straight detection (ace can play low)
        uniq = sorted(set(ranks), reverse=True)
        straight_high = -1
        if len(uniq) == 5:
            if uniq[0] - uniq[4] == 4:
                straight_high = uniq[0]
            elif uniq == [12, 3, 2, 1, 0]:  # wheel A-5
                straight_high = 3
        counts = {}
        for r in ranks:
            counts[r] = counts.get(r, 0) + 1
        groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
        shape = [g[1] for g in groups]
        order = [g[0] for g in groups]
        if straight_high >= 0 and flush:
            cat, tie = 8, [straight_high]
        elif shape[0] == 4:
            cat, tie = 7, order
        elif shape[0] == 3 and shape[1] == 2:
            cat, tie = 6, order
        elif flush:
            cat, tie = 5, ranks
        elif straight_high >= 0:
            cat, tie = 4, [straight_high]
        elif shape[0] == 3:
            cat, tie = 3, order
        elif shape[0] == 2 and shape[1] == 2:
            cat, tie = 2, order
        elif shape[0] == 2:
            cat, tie = 1, order
        else:
            cat, tie = 0, ranks
        score = cat
        for t in tie:
            score = score * 16 + t
        for _ in range(5 - len(tie)):
            score *= 16
        return score

    def hand_rank(cards7) -> int:
        return max(_score5(c) for c in combinations(cards7, 5))

    BACKEND = "python-fallback"
