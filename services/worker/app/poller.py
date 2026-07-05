class SqsPoller:
    def __init__(self, sqs, queue_url: str, wait_time: int, max_messages: int):
        self._sqs = sqs
        self._queue_url = queue_url
        self._wait_time = wait_time
        self._max_messages = max_messages

    def receive(self) -> list[dict]:
        response = self._sqs.receive_message(
            QueueUrl=self._queue_url,
            MaxNumberOfMessages=self._max_messages,
            WaitTimeSeconds=self._wait_time,
        )
        return response.get("Messages", [])

    def delete(self, handles: list[str]) -> None:
        if not handles:
            return
        entries = [{"Id": str(i), "ReceiptHandle": h} for i, h in enumerate(handles)]
        self._sqs.delete_message_batch(QueueUrl=self._queue_url, Entries=entries)
