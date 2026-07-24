from __future__ import annotations


def _event(date, country="USA", direction="ENTRY", stamp_id=None, source_image=None):
    from src.reconstruction.timeline import TimelineEvent
    return TimelineEvent(
        date=date,
        country=country,
        direction=direction,
        stamp_id=stamp_id,
        source_image=source_image,
    )


def test_sorts_events_by_date_ascending():
    from src.reconstruction.timeline import build_timeline
    events = [_event("2019-05-14"), _event("1988-11-17"), _event("2006-10-05")]
    timeline = build_timeline(events)
    assert [e.date for e in timeline.events] == ["1988-11-17", "2006-10-05", "2019-05-14"]
    assert timeline.undated == []


def test_none_date_goes_to_undated():
    from src.reconstruction.timeline import build_timeline
    events = [_event("2019-05-14"), _event(None, stamp_id="s1")]
    timeline = build_timeline(events)
    assert [e.date for e in timeline.events] == ["2019-05-14"]
    assert [e.stamp_id for e in timeline.undated] == ["s1"]


def test_invalid_date_string_treated_as_undated_without_crashing():
    from src.reconstruction.timeline import build_timeline
    events = [_event("2019-05-14"), _event("1988-13-40", stamp_id="bad"), _event("abc", stamp_id="junk")]
    timeline = build_timeline(events)
    assert [e.date for e in timeline.events] == ["2019-05-14"]
    assert {e.stamp_id for e in timeline.undated} == {"bad", "junk"}


def test_same_date_preserves_input_order():
    from src.reconstruction.timeline import build_timeline
    events = [_event("2020-01-01", stamp_id="a"), _event("2020-01-01", stamp_id="b")]
    timeline = build_timeline(events)
    assert [e.stamp_id for e in timeline.events] == ["a", "b"]


def test_empty_input_returns_empty_timeline():
    from src.reconstruction.timeline import build_timeline
    timeline = build_timeline([])
    assert timeline.events == []
    assert timeline.undated == []
