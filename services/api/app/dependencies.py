from functools import lru_cache

from .aws import dynamodb_resource, sqs_client
from .config import Config, load_config
from .events import ClickPublisher
from .repository import LinkRepository, StatsRepository


@lru_cache
def get_config() -> Config:
    return load_config()


def get_link_repository() -> LinkRepository:
    config = get_config()
    table = dynamodb_resource(config).Table(config.links_table)
    return LinkRepository(table)


def get_stats_repository() -> StatsRepository:
    config = get_config()
    table = dynamodb_resource(config).Table(config.stats_table)
    return StatsRepository(table)


def get_click_publisher() -> ClickPublisher:
    config = get_config()
    return ClickPublisher(sqs_client(config), config.click_queue_url)
