import json
from datetime import datetime, timezone


class ClickPublisher:
    def __init__(self, sqs, queue_url: str):
        self._sqs = sqs
        self._queue_url = queue_url

    def publish(self, short_code: str) -> None:
        if not self._queue_url:
            return
        body = json.dumps(
            {
                "short_code": short_code,
                "clicked_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._sqs.send_message(QueueUrl=self._queue_url, MessageBody=body)
