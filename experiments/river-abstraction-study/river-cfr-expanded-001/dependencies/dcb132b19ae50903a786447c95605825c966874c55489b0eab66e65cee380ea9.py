"""Card representation: ints 0..51, rank-major (2c=0, 2d=1, 2h=2, 2s=3, 3c=4 ... As=51).

This matches the `phevaluator` package's card ids exactly, so cards go straight
into the evaluator with no conversion.
"""
RANK_CHARS = "23456789TJQKA"
SUIT_CHARS = "cdhs"
SUIT_SYMBOLS = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}


def rank_of(card: int) -> int:
    return card // 4  # 0 = deuce ... 12 = ace


def suit_of(card: int) -> int:
    return card % 4


def card_str(card: int) -> str:
    return RANK_CHARS[card // 4] + SUIT_CHARS[card % 4]


def cards_str(cards) -> str:
    return " ".join(card_str(c) for c in cards)


def parse_card(text: str) -> int:
    rank = RANK_CHARS.index(text[0].upper())
    suit = SUIT_CHARS.index(text[1].lower())
    return rank * 4 + suit


def preflop_class(hole) -> int:
    """Lossless preflop bucket 0..168 (13 pairs + 78 suited + 78 offsuit)."""
    r1, r2 = sorted((rank_of(hole[0]), rank_of(hole[1])), reverse=True)
    suited = suit_of(hole[0]) == suit_of(hole[1])
    if r1 == r2:
        return r1  # 0..12 pairs
    # index over unordered rank pairs r1 > r2
    idx = r1 * (r1 - 1) // 2 + r2  # 0..77
    return 13 + idx + (78 if suited else 0)


def preflop_class_str(cls: int) -> str:
    if cls < 13:
        return RANK_CHARS[cls] * 2
    cls -= 13
    suited = cls >= 78
    if suited:
        cls -= 78
    # invert triangular index
    r1 = 1
    while (r1 + 1) * r1 // 2 <= cls:
        r1 += 1
    r2 = cls - r1 * (r1 - 1) // 2
    return RANK_CHARS[r1] + RANK_CHARS[r2] + ("s" if suited else "o")
