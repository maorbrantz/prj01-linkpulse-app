def test_healthz_reports_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_reports_ready_when_table_reachable(client):
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_metrics_exposes_prometheus_output(client):
    client.post("/links", json={"url": "https://example.com/metric"})

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
