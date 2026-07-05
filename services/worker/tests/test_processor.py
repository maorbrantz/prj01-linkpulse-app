import json

from app.processor import ClickProcessor
from app.repository import StatsRepository


def _message(handle: str, short_code: str, day: str) -> dict:
    return {
        "ReceiptHandle": handle,
        "Body": json.dumps({"short_code": short_code, "clicked_at": f"{day}T01:00:00"}),
    }


def test_process_batch_writes_counts_and_returns_handles(stats_table):
    processor = ClickProcessor(StatsRepository(stats_table))
    messages = [
        _message("h1", "abc", "2026-07-05"),
        _message("h2", "abc", "2026-07-05"),
        _message("h3", "abc", "2026-07-06"),
    ]

    handles = processor.process_batch(messages)

    assert sorted(handles) == ["h1", "h2", "h3"]
    item = stats_table.get_item(Key={"short_code": "abc", "day": "2026-07-05"})["Item"]
    assert int(item["count"]) == 2


def test_process_batch_drops_invalid_messages(stats_table):
    processor = ClickProcessor(StatsRepository(stats_table))
    messages = [
        {"ReceiptHandle": "bad", "Body": "not-json"},
        _message("good", "abc", "2026-07-05"),
    ]

    handles = processor.process_batch(messages)

    assert sorted(handles) == ["bad", "good"]


def test_process_batch_keeps_failed_writes_for_retry():
    processor = ClickProcessor(StatsRepository(_FailingTable()))
    messages = [_message("h1", "abc", "2026-07-05")]

    handles = processor.process_batch(messages)

    assert handles == []


class _FailingTable:
    def update_item(self, **kwargs):
        raise RuntimeError("dynamodb unavailable")
