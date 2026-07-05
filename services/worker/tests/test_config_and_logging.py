import json
import logging

from app.config import load_config
from app.logging_config import JsonFormatter, configure_logging, log_with_fields


def test_load_config_defaults(monkeypatch):
    for key in ("AWS_ENDPOINT_URL", "STATS_TABLE", "WAIT_TIME_SECONDS"):
        monkeypatch.delenv(key, raising=False)

    config = load_config()

    assert config.stats_table == "click_stats"
    assert config.wait_time_seconds == 20
    assert config.endpoint_url is None


def test_load_config_reads_overrides(monkeypatch):
    monkeypatch.setenv("STATS_TABLE", "custom_stats")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localstack:4566")
    monkeypatch.setenv("MAX_MESSAGES", "5")

    config = load_config()

    assert config.stats_table == "custom_stats"
    assert config.endpoint_url == "http://localstack:4566"
    assert config.max_messages == 5


def test_configure_logging_installs_json_handler():
    configure_logging()

    handler = logging.getLogger().handlers[0]
    assert isinstance(handler.formatter, JsonFormatter)


def test_log_with_fields_records_message(caplog):
    logger = logging.getLogger("worker-test")
    with caplog.at_level(logging.INFO):
        log_with_fields(logger, logging.INFO, "hello", short_code="abc")

    assert "hello" in caplog.text


def test_json_formatter_emits_fields():
    formatter = JsonFormatter()
    logger = logging.getLogger("fmt")
    record = logger.makeRecord("fmt", logging.INFO, __file__, 1, "msg", None, None)
    record.extra_fields = {"received": 3}

    output = json.loads(formatter.format(record))

    assert output["received"] == 3
