import json

import pytest

from app.aggregate import aggregate, parse_event


def test_parse_event_extracts_code_and_day():
    body = json.dumps({"short_code": "abc123", "clicked_at": "2026-07-05T10:00:00+00:00"})

    short_code, day = parse_event(body)

    assert short_code == "abc123"
    assert day == "2026-07-05"


def test_parse_event_rejects_missing_short_code():
    body = json.dumps({"short_code": "", "clicked_at": "2026-07-05T10:00:00+00:00"})

    with pytest.raises(ValueError):
        parse_event(body)


def test_parse_event_rejects_short_timestamp():
    body = json.dumps({"short_code": "abc", "clicked_at": "2026"})

    with pytest.raises(ValueError):
        parse_event(body)


def test_aggregate_counts_per_code_and_day():
    bodies = [
        json.dumps({"short_code": "a", "clicked_at": "2026-07-05T01:00:00"}),
        json.dumps({"short_code": "a", "clicked_at": "2026-07-05T02:00:00"}),
        json.dumps({"short_code": "a", "clicked_at": "2026-07-06T01:00:00"}),
        json.dumps({"short_code": "b", "clicked_at": "2026-07-05T01:00:00"}),
    ]

    result = aggregate(bodies)

    assert result[("a", "2026-07-05")] == 2
    assert result[("a", "2026-07-06")] == 1
    assert result[("b", "2026-07-05")] == 1
