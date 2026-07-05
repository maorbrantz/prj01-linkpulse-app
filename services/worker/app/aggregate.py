import json
from collections import Counter


def parse_event(body: str) -> tuple[str, str]:
    event = json.loads(body)
    short_code = event["short_code"]
    day = event["clicked_at"][:10]
    if not short_code or len(day) != 10:
        raise ValueError("invalid click event")
    return short_code, day


def aggregate(bodies: list[str]) -> dict[tuple[str, str], int]:
    counts: Counter = Counter()
    for body in bodies:
        counts[parse_event(body)] += 1
    return dict(counts)
