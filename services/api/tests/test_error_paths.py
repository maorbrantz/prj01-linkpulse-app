import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from app import dependencies
from app.events import ClickPublisher
from app.main import app


class _UnavailableRepo:
    def exists(self, short_code):
        raise ClientError({"Error": {"Code": "ServiceUnavailable"}}, "GetItem")

    def save(self, short_code, url):
        raise ClientError({"Error": {"Code": "ServiceUnavailable"}}, "PutItem")

    def get(self, short_code):
        return None


class _AlwaysConflictRepo:
    def save(self, short_code, url):
        raise ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
        )


@pytest.fixture
def unavailable_client():
    app.dependency_overrides[dependencies.get_link_repository] = lambda: _UnavailableRepo()
    app.dependency_overrides[dependencies.get_click_publisher] = lambda: ClickPublisher(
        None, ""
    )
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_readyz_returns_503_when_storage_down(unavailable_client):
    response = unavailable_client.get("/readyz")

    assert response.status_code == 503


def test_create_link_returns_503_on_storage_error(unavailable_client):
    response = unavailable_client.post("/links", json={"url": "https://example.com/x"})

    assert response.status_code == 503


def test_create_link_gives_up_after_repeated_conflicts():
    app.dependency_overrides[dependencies.get_link_repository] = lambda: _AlwaysConflictRepo()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.post("/links", json={"url": "https://example.com/x"})
    app.dependency_overrides.clear()

    assert response.status_code == 500
