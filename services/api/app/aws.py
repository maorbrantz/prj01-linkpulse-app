import boto3

from .config import Config


def build_session(config: Config) -> boto3.session.Session:
    return boto3.session.Session(region_name=config.aws_region)


def dynamodb_resource(config: Config):
    session = build_session(config)
    return session.resource("dynamodb", endpoint_url=config.endpoint_url)


def sqs_client(config: Config):
    session = build_session(config)
    return session.client("sqs", endpoint_url=config.endpoint_url)
