import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    aws_region: str
    stats_table: str
    click_queue_url: str
    endpoint_url: str | None
    wait_time_seconds: int
    max_messages: int
    metrics_port: int


def load_config() -> Config:
    endpoint = os.getenv("AWS_ENDPOINT_URL") or None
    return Config(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        stats_table=os.getenv("STATS_TABLE", "click_stats"),
        click_queue_url=os.getenv("CLICK_QUEUE_URL", ""),
        endpoint_url=endpoint,
        wait_time_seconds=int(os.getenv("WAIT_TIME_SECONDS", "20")),
        max_messages=int(os.getenv("MAX_MESSAGES", "10")),
        metrics_port=int(os.getenv("METRICS_PORT", "9000")),
    )
