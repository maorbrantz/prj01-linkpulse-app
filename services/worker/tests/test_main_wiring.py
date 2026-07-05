from app import main as main_module
from app.config import load_config
from app.main import build_poller, build_processor, main
from app.poller import SqsPoller
from app.processor import ClickProcessor


def test_build_processor_returns_processor(stats_table, monkeypatch):
    monkeypatch.setenv("STATS_TABLE", "click_stats")
    config = load_config()

    processor = build_processor(config)

    assert isinstance(processor, ClickProcessor)


def test_build_poller_returns_poller(click_queue, monkeypatch):
    monkeypatch.setenv("CLICK_QUEUE_URL", click_queue)
    config = load_config()

    poller = build_poller(config)

    assert isinstance(poller, SqsPoller)


def test_main_starts_metrics_and_runs_loop(stats_table, click_queue, monkeypatch):
    monkeypatch.setenv("CLICK_QUEUE_URL", click_queue)
    calls = {}
    monkeypatch.setattr(main_module, "serve_metrics", lambda port: calls.setdefault("port", port))
    monkeypatch.setattr(main_module, "run_loop", lambda p, pr, flag: calls.setdefault("ran", True))
    monkeypatch.setattr(main_module.signal, "signal", lambda *args: None)

    main()

    assert calls["ran"] is True
    assert "port" in calls
