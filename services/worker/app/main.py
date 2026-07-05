import logging
import signal

from .aws import dynamodb_resource, sqs_client
from .config import load_config
from .logging_config import configure_logging, log_with_fields
from .metrics import serve_metrics
from .poller import SqsPoller
from .processor import ClickProcessor
from .repository import StatsRepository
from .runner import ShutdownFlag, run_loop

logger = logging.getLogger("linkpulse.worker")


def build_processor(config) -> ClickProcessor:
    table = dynamodb_resource(config).Table(config.stats_table)
    return ClickProcessor(StatsRepository(table))


def build_poller(config) -> SqsPoller:
    return SqsPoller(
        sqs_client(config),
        config.click_queue_url,
        config.wait_time_seconds,
        config.max_messages,
    )


def main() -> None:
    configure_logging()
    config = load_config()
    serve_metrics(config.metrics_port)
    flag = ShutdownFlag()
    signal.signal(signal.SIGTERM, flag.request_stop)
    signal.signal(signal.SIGINT, flag.request_stop)
    log_with_fields(logger, logging.INFO, "worker_started", queue=config.click_queue_url)
    run_loop(build_poller(config), build_processor(config), flag)


if __name__ == "__main__":
    main()
