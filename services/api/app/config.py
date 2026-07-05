import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    aws_region: str
    links_table: str
    stats_table: str
    click_queue_url: str
    endpoint_url: str | None
    base_url: str
    short_code_length: int


def load_config() -> Config:
    endpoint = os.getenv("AWS_ENDPOINT_URL") or None
    return Config(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        links_table=os.getenv("LINKS_TABLE", "links"),
        stats_table=os.getenv("STATS_TABLE", "click_stats"),
        click_queue_url=os.getenv("CLICK_QUEUE_URL", ""),
        endpoint_url=endpoint,
        base_url=os.getenv("BASE_URL", "http://localhost:8000"),
        short_code_length=int(os.getenv("SHORT_CODE_LENGTH", "7")),
    )
