import json
import logging

import pytest
from botocore.exceptions import ClientError

from app.config import load_config
from app.events import ClickPublisher
from app.logging_config import JsonFormatter, log_with_fields
from app.repository import LinkRepository, StatsRepository
from app.shortcode import generate
from app.stats import build_stats


def test_generate_returns_requested_length():
    code = generate(10)

    assert len(code) == 10
    assert code.isalnum()


def test_generate_produces_distinct_values():
    values = {generate(8) for _ in range(50)}

    assert len(values) == 50


def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("LINKS_TABLE", "custom")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localstack:4566")

    config = load_config()

    assert config.links_table == "custom"
    assert config.endpoint_url == "http://localstack:4566"


def test_load_config_treats_blank_endpoint_as_none(monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "")

    config = load_config()

    assert config.endpoint_url is None


def test_build_stats_sums_and_sorts_days():
    items = [
        {"short_code": "abc", "day": "2026-07-02", "count": 2},
        {"short_code": "abc", "day": "2026-07-01", "count": 4},
    ]

    result = build_stats("abc", items)

    assert result.total_clicks == 6
    assert [d.day for d in result.daily] == ["2026-07-01", "2026-07-02"]


def test_click_publisher_skips_when_no_queue():
    sent = []
    publisher = ClickPublisher(_RecordingSqs(sent), "")

    publisher.publish("abc")

    assert sent == []


def test_click_publisher_sends_payload():
    sent = []
    publisher = ClickPublisher(_RecordingSqs(sent), "http://queue")

    publisher.publish("abc")

    assert len(sent) == 1
    assert json.loads(sent[0]["MessageBody"])["short_code"] == "abc"


def test_stats_repository_returns_empty_on_client_error():
    repo = StatsRepository(_FailingTable())

    assert repo.by_short_code("abc") == []


def test_json_formatter_includes_extra_fields():
    formatter = JsonFormatter()
    logger = logging.getLogger("unit-test")
    record = logger.makeRecord(
        "unit-test", logging.INFO, __file__, 1, "hello", None, None
    )
    record.extra_fields = {"short_code": "abc"}

    output = json.loads(formatter.format(record))

    assert output["message"] == "hello"
    assert output["short_code"] == "abc"


def test_json_formatter_serializes_exception():
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        logger = logging.getLogger("unit-test")
        record = logger.makeRecord(
            "unit-test", logging.ERROR, __file__, 1, "failed", None, _exc_info()
        )
        output = json.loads(formatter.format(record))

    assert "ValueError" in output["exception"]


def test_log_with_fields_passes_extra(caplog):
    logger = logging.getLogger("field-test")
    with caplog.at_level(logging.INFO):
        log_with_fields(logger, logging.INFO, "event", key="value")

    assert "event" in caplog.text


def test_link_repository_get_returns_none_when_absent():
    repo = LinkRepository(_EmptyTable())

    assert repo.get("nope") is None
    assert repo.exists("nope") is False


def _exc_info():
    import sys

    return sys.exc_info()


class _RecordingSqs:
    def __init__(self, sent):
        self._sent = sent

    def send_message(self, **kwargs):
        self._sent.append(kwargs)


class _FailingTable:
    def query(self, **kwargs):
        raise ClientError({"Error": {"Code": "ResourceNotFoundException"}}, "Query")


class _EmptyTable:
    def get_item(self, **kwargs):
        return {}
