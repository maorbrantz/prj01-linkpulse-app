import logging

from .logging_config import log_with_fields
from .metrics import BATCHES_POLLED
from .poller import SqsPoller
from .processor import ClickProcessor

logger = logging.getLogger("linkpulse.worker")


class ShutdownFlag:
    def __init__(self):
        self._stop = False

    def request_stop(self, *_args) -> None:
        self._stop = True

    @property
    def stopped(self) -> bool:
        return self._stop


def run_once(poller: SqsPoller, processor: ClickProcessor) -> int:
    messages = poller.receive()
    if not messages:
        return 0
    BATCHES_POLLED.inc()
    handles = processor.process_batch(messages)
    poller.delete(handles)
    log_with_fields(
        logger,
        logging.INFO,
        "batch_processed",
        received=len(messages),
        deleted=len(handles),
    )
    return len(messages)


def run_loop(poller: SqsPoller, processor: ClickProcessor, flag: ShutdownFlag) -> None:
    while not flag.stopped:
        run_once(poller, processor)
    log_with_fields(logger, logging.INFO, "worker_stopped")
