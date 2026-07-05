import json
from dataclasses import replace


def test_create_link_returns_short_code_and_url(client):
    response = client.post("/links", json={"url": "https://example.com/page"})

    assert response.status_code == 201
    body = response.json()
    assert len(body["short_code"]) == 7
    assert body["short_url"].endswith(body["short_code"])


def test_create_link_rejects_invalid_url(client):
    response = client.post("/links", json={"url": "not-a-url"})

    assert response.status_code == 422


def test_redirect_returns_302_to_target(client):
    created = client.post("/links", json={"url": "https://example.com/target"}).json()

    response = client.get(f"/{created['short_code']}", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/target"


def test_redirect_emits_click_event(client, sqs_messages):
    created = client.post("/links", json={"url": "https://example.com/click"}).json()

    client.get(f"/{created['short_code']}", follow_redirects=False)

    messages = sqs_messages()
    assert len(messages) == 1
    payload = json.loads(messages[0]["Body"])
    assert payload["short_code"] == created["short_code"]
    assert "clicked_at" in payload


def test_redirect_unknown_code_returns_404(client):
    response = client.get("/missing1", follow_redirects=False)

    assert response.status_code == 404


def test_redirect_injects_failure_when_fail_rate_is_one(client):
    from app import dependencies
    from app.config import load_config
    from app.main import app

    created = client.post("/links", json={"url": "https://example.com/fail"}).json()
    base = load_config()
    forced = replace(base, fail_rate=1.0)
    app.dependency_overrides[dependencies.get_config] = lambda: forced
    try:
        response = client.get(f"/{created['short_code']}", follow_redirects=False)
    finally:
        app.dependency_overrides.pop(dependencies.get_config, None)

    assert response.status_code == 500


def test_redirect_succeeds_when_fail_rate_is_zero(client):
    from app import dependencies
    from app.config import load_config
    from app.main import app

    created = client.post("/links", json={"url": "https://example.com/ok"}).json()
    forced = replace(load_config(), fail_rate=0.0)
    app.dependency_overrides[dependencies.get_config] = lambda: forced
    try:
        response = client.get(f"/{created['short_code']}", follow_redirects=False)
    finally:
        app.dependency_overrides.pop(dependencies.get_config, None)

    assert response.status_code == 302


def test_stats_unknown_code_returns_404(client):
    response = client.get("/links/missing1/stats")

    assert response.status_code == 404


def test_stats_returns_aggregated_counts(client, stats_table):
    created = client.post("/links", json={"url": "https://example.com/stats"}).json()
    code = created["short_code"]
    stats_table.put_item(Item={"short_code": code, "day": "2026-07-01", "count": 3})
    stats_table.put_item(Item={"short_code": code, "day": "2026-07-02", "count": 5})

    response = client.get(f"/links/{code}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_clicks"] == 8
    assert body["daily"] == [
        {"day": "2026-07-01", "count": 3},
        {"day": "2026-07-02", "count": 5},
    ]


def test_stats_empty_when_no_clicks(client):
    created = client.post("/links", json={"url": "https://example.com/none"}).json()

    response = client.get(f"/links/{created['short_code']}/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_clicks"] == 0
    assert body["daily"] == []
