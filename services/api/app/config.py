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
    fail_rate: float


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
        # fault injection knob for the canary rollback demo. the fraction of
        # redirect requests that return a 500 instead of redirecting. defaults to
        # off. a bad release sets this so its canary pods fail analysis.
        fail_rate=_parse_fail_rate(os.getenv("FAIL_RATE", "0.0")),
    )


def _parse_fail_rate(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError:
        return 0.0
    return min(max(value, 0.0), 1.0)
