import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from app import dependencies  # noqa: E402
from app.events import ClickPublisher  # noqa: E402
from app.main import app  # noqa: E402
from app.repository import LinkRepository, StatsRepository  # noqa: E402


@pytest.fixture
def aws():
    with mock_aws():
        yield


@pytest.fixture
def links_table(aws):
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    resource.create_table(
        TableName="links",
        KeySchema=[{"AttributeName": "short_code", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "short_code", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return resource.Table("links")


@pytest.fixture
def stats_table(aws):
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    resource.create_table(
        TableName="click_stats",
        KeySchema=[
            {"AttributeName": "short_code", "KeyType": "HASH"},
            {"AttributeName": "day", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "short_code", "AttributeType": "S"},
            {"AttributeName": "day", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return resource.Table("click_stats")


@pytest.fixture
def click_queue(aws):
    sqs = boto3.client("sqs", region_name="us-east-1")
    return sqs.create_queue(QueueName="clicks")["QueueUrl"]


@pytest.fixture
def client(links_table, stats_table, click_queue):
    from fastapi.testclient import TestClient

    sqs = boto3.client("sqs", region_name="us-east-1")
    app.dependency_overrides[dependencies.get_link_repository] = lambda: LinkRepository(links_table)
    app.dependency_overrides[dependencies.get_stats_repository] = lambda: StatsRepository(stats_table)
    app.dependency_overrides[dependencies.get_click_publisher] = lambda: ClickPublisher(sqs, click_queue)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sqs_messages(click_queue):
    def _read():
        sqs = boto3.client("sqs", region_name="us-east-1")
        response = sqs.receive_message(QueueUrl=click_queue, MaxNumberOfMessages=10)
        return response.get("Messages", [])

    return _read
