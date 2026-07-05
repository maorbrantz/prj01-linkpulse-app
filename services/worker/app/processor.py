import logging

from .aggregate import parse_event
from .logging_config import log_with_fields
from .metrics import MESSAGES_FAILED, MESSAGES_PROCESSED
from .repository import StatsRepository

logger = logging.getLogger("linkpulse.worker")


class ClickProcessor:
    def __init__(self, stats: StatsRepository):
        self._stats = stats

    def process_batch(self, messages: list[dict]) -> list[dict]:
        parsed, invalid = self._parse(messages)
        counts = self._tally(parsed)
        written = self._write(counts, parsed)
        deletable = written + invalid
        MESSAGES_PROCESSED.inc(len(deletable))
        MESSAGES_FAILED.inc(len(messages) - len(deletable))
        return [m["handle"] for m in deletable]

    def _parse(self, messages: list[dict]) -> tuple[list[dict], list[dict]]:
        parsed: list[dict] = []
        invalid: list[dict] = []
        for message in messages:
            handle = message["ReceiptHandle"]
            try:
                short_code, day = parse_event(message["Body"])
                parsed.append({"handle": handle, "key": (short_code, day)})
            except (ValueError, KeyError):
                log_with_fields(logger, logging.WARNING, "invalid_message_dropped")
                invalid.append({"handle": handle})
        return parsed, invalid

    def _tally(self, parsed: list[dict]) -> dict[tuple[str, str], int]:
        counts: dict[tuple[str, str], int] = {}
        for entry in parsed:
            counts[entry["key"]] = counts.get(entry["key"], 0) + 1
        return counts

    def _write(self, counts: dict, parsed: list[dict]) -> list[dict]:
        failed_keys = set()
        for (short_code, day), amount in counts.items():
            try:
                self._stats.increment(short_code, day, amount)
            except Exception:
                log_with_fields(
                    logger, logging.ERROR, "increment_failed", short_code=short_code
                )
                failed_keys.add((short_code, day))
        return [e for e in parsed if e["key"] not in failed_keys]
