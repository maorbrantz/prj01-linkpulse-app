import os

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def aws():
    with mock_aws():
        yield


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
