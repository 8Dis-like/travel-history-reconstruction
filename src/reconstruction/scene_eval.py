from __future__ import annotations

"""Scoring helpers for the synthetic-scene test set.

pairwise_order_accuracy measures how well predicted dates preserve the true
chronological order of stamps — the downstream effect of OCR date errors on the
reconstructed timeline. For every pair of stamps whose true dates differ, the
pair is concordant when the predicted dates place them in the same relative
order (and both predicted dates are readable). Unreadable predicted dates make
their pairs discordant.
"""

from datetime import datetime
from itertools import combinations
from typing import Iterable


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def pairwise_order_accuracy(pairs: Iterable[tuple[str | None, str | None]]) -> float:
    """Fraction of comparable stamp pairs kept in correct chronological order.

    Each pair is (true_date, predicted_date) as ISO strings. Pairs whose true
    dates are equal or unparseable are not counted. With fewer than one
    comparable pair, returns 1.0.
    """
    parsed = [(_parse(true), _parse(pred)) for true, pred in pairs]

    comparable = 0
    concordant = 0
    for (ta, pa), (tb, pb) in combinations(parsed, 2):
        if ta is None or tb is None or ta == tb:
            continue
        comparable += 1
        if pa is None or pb is None:
            continue  # unreadable prediction -> discordant
        if (ta < tb) == (pa < pb):
            concordant += 1

    if comparable == 0:
        return 1.0
    return concordant / comparable
