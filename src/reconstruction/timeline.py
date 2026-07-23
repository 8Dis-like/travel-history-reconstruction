from __future__ import annotations

"""Minimal timeline reconstruction: order stamp observations chronologically.

Given extracted stamps (each carrying a date/country/direction), sort them into
a chronological event sequence. Stamps whose date is missing or not a valid
ISO YYYY-MM-DD are kept separately in `undated` rather than dropped, so callers
and tests can see exactly what could not be placed.

Entry/exit interval pairing is intentionally out of scope here — this step only
establishes the time order.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class TimelineEvent:
    date: str | None
    country: str | None
    direction: str | None
    stamp_id: str | None = None
    source_image: str | None = None


@dataclass(frozen=True)
class Timeline:
    events: list[TimelineEvent]   # placeable events, ascending by date (stable)
    undated: list[TimelineEvent]  # missing / invalid date, order preserved


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def build_timeline(events: Iterable[TimelineEvent]) -> Timeline:
    """Split events into date-sorted `events` and unplaceable `undated`."""
    dated: list[tuple[datetime, TimelineEvent]] = []
    undated: list[TimelineEvent] = []

    for event in events:
        parsed = _parse_date(event.date)
        if parsed is None:
            undated.append(event)
        else:
            dated.append((parsed, event))

    # sorted() is stable, so events sharing a date keep their input order
    dated.sort(key=lambda pair: pair[0])
    return Timeline(events=[event for _, event in dated], undated=undated)
