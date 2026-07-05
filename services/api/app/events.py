import json
import logging
from datetime import datetime, timezone

from botocore.exceptions import BotoCoreError, ClientError

from .logging_config import log_with_fields

logger = logging.getLogger("linkpulse.api")


class ClickPublisher:
    def __init__(self, sqs, queue_url: str):
        self._sqs = sqs
        self._queue_url = queue_url

    def publish(self, short_code: str) -> bool:
        if not self._queue_url:
            log_with_fields(logger, logging.WARNING, "click_queue_not_configured")
            return False
        body = json.dumps(
            {
                "short_code": short_code,
                "clicked_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        try:
            self._sqs.send_message(QueueUrl=self._queue_url, MessageBody=body)
            return True
        except (ClientError, BotoCoreError):
            log_with_fields(
                logger, logging.ERROR, "click_publish_failed", short_code=short_code
            )
            return False
