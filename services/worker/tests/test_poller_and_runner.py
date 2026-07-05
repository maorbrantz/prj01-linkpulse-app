import json

import boto3

from app.poller import SqsPoller
from app.processor import ClickProcessor
from app.repository import StatsRepository
from app.runner import ShutdownFlag, run_loop, run_once


def _seed(queue_url: str, short_code: str) -> None:
    sqs = boto3.client("sqs", region_name="us-east-1")
    body = json.dumps({"short_code": short_code, "clicked_at": "2026-07-05T01:00:00"})
    sqs.send_message(QueueUrl=queue_url, MessageBody=body)


def test_poller_receives_and_deletes(click_queue):
    _seed(click_queue, "abc")
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = SqsPoller(sqs, click_queue, wait_time=0, max_messages=10)

    messages = poller.receive()
    poller.delete([m["ReceiptHandle"] for m in messages])

    assert len(messages) == 1
    remaining = sqs.receive_message(QueueUrl=click_queue, WaitTimeSeconds=0)
    assert remaining.get("Messages", []) == []


def test_poller_delete_noop_on_empty(click_queue):
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = SqsPoller(sqs, click_queue, wait_time=0, max_messages=10)

    assert poller.delete([]) == []


def test_poller_delete_returns_failed_handles():
    poller = SqsPoller(_PartialFailSqs(), "http://q", wait_time=0, max_messages=10)

    failed = poller.delete(["h0", "h1", "h2"])

    assert failed == ["h1"]


def test_run_once_processes_and_removes_message(click_queue, stats_table):
    _seed(click_queue, "abc")
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = SqsPoller(sqs, click_queue, wait_time=0, max_messages=10)
    processor = ClickProcessor(StatsRepository(stats_table))

    count = run_once(poller, processor)

    assert count == 1
    item = stats_table.get_item(Key={"short_code": "abc", "day": "2026-07-05"})["Item"]
    assert int(item["count"]) == 1


def test_run_once_logs_when_delete_fails(click_queue, stats_table, caplog):
    _seed(click_queue, "abc")
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = _DeleteFailingPoller(sqs, click_queue, wait_time=0, max_messages=10)
    processor = ClickProcessor(StatsRepository(stats_table))

    with caplog.at_level("WARNING"):
        run_once(poller, processor)

    assert "delete_failed" in caplog.text


def test_run_once_returns_zero_when_empty(click_queue, stats_table):
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = SqsPoller(sqs, click_queue, wait_time=0, max_messages=10)
    processor = ClickProcessor(StatsRepository(stats_table))

    assert run_once(poller, processor) == 0


def test_run_loop_stops_when_flag_set(click_queue, stats_table):
    _seed(click_queue, "abc")
    sqs = boto3.client("sqs", region_name="us-east-1")
    poller = SqsPoller(sqs, click_queue, wait_time=0, max_messages=10)
    processor = ClickProcessor(StatsRepository(stats_table))
    flag = _OneShotFlag()

    run_loop(poller, processor, flag)

    item = stats_table.get_item(Key={"short_code": "abc", "day": "2026-07-05"})["Item"]
    assert int(item["count"]) == 1


def test_shutdown_flag_toggles():
    flag = ShutdownFlag()

    assert flag.stopped is False
    flag.request_stop()
    assert flag.stopped is True


class _OneShotFlag:
    def __init__(self):
        self._checks = 0

    @property
    def stopped(self) -> bool:
        stop = self._checks >= 1
        self._checks += 1
        return stop


class _PartialFailSqs:
    def delete_message_batch(self, **kwargs):
        return {"Failed": [{"Id": "1"}]}


class _DeleteFailingPoller(SqsPoller):
    def delete(self, handles):
        return list(handles)
