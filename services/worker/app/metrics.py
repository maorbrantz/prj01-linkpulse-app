from prometheus_client import Counter, start_http_server

MESSAGES_PROCESSED = Counter(
    "worker_messages_processed_total",
    "Click messages successfully aggregated and deleted",
)

MESSAGES_FAILED = Counter(
    "worker_messages_failed_total",
    "Click messages that failed processing and returned to the queue",
)

BATCHES_POLLED = Counter(
    "worker_batches_polled_total",
    "SQS receive calls that returned at least one message",
)


def serve_metrics(port: int) -> None:
    start_http_server(port)
