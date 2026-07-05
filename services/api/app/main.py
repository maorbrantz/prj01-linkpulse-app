import logging
import random

from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import Config
from .dependencies import (
    get_click_publisher,
    get_config,
    get_link_repository,
    get_stats_repository,
)
from .events import ClickPublisher
from .logging_config import configure_logging, log_with_fields
from .metrics import metrics_middleware, metrics_response
from .repository import LinkRepository, StatsRepository
from .schemas import CreateLinkRequest, CreateLinkResponse, StatsResponse
from .shortcode import generate
from .stats import build_stats

configure_logging()
logger = logging.getLogger("linkpulse.api")

app = FastAPI(title="LinkPulse API")
app.middleware("http")(metrics_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_MAX_CODE_ATTEMPTS = 5


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(links: LinkRepository = Depends(get_link_repository)) -> dict:
    try:
        links.exists("__readiness_probe__")
    except ClientError as exc:
        raise HTTPException(status_code=503, detail="dependencies unavailable") from exc
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/links", response_model=CreateLinkResponse, status_code=201)
def create_link(
    payload: CreateLinkRequest,
    links: LinkRepository = Depends(get_link_repository),
    config=Depends(get_config),
) -> CreateLinkResponse:
    url = str(payload.url)
    short_code = _reserve_code(links, url, config.short_code_length)
    log_with_fields(logger, logging.INFO, "link_created", short_code=short_code, url=url)
    short_url = f"{config.base_url.rstrip('/')}/{short_code}"
    return CreateLinkResponse(short_code=short_code, short_url=short_url)


@app.get("/{short_code}")
def redirect(
    short_code: str,
    links: LinkRepository = Depends(get_link_repository),
    publisher: ClickPublisher = Depends(get_click_publisher),
    config: Config = Depends(get_config),
) -> RedirectResponse:
    _maybe_inject_failure(config)
    item = links.get(short_code)
    if item is None:
        raise HTTPException(status_code=404, detail="short code not found")
    publisher.publish(short_code)
    log_with_fields(logger, logging.INFO, "link_clicked", short_code=short_code)
    return RedirectResponse(url=item["url"], status_code=302)


def _maybe_inject_failure(config: Config) -> None:
    # fault injection for the canary rollback demo. when FAIL_RATE is set, that
    # fraction of redirects return a 500 so a bad release fails its prometheus
    # analysis. off by default, so normal releases are unaffected.
    if config.fail_rate > 0 and random.random() < config.fail_rate:
        raise HTTPException(status_code=500, detail="injected failure")


@app.get("/links/{short_code}/stats", response_model=StatsResponse)
def link_stats(
    short_code: str,
    links: LinkRepository = Depends(get_link_repository),
    stats: StatsRepository = Depends(get_stats_repository),
) -> StatsResponse:
    if not links.exists(short_code):
        raise HTTPException(status_code=404, detail="short code not found")
    return build_stats(short_code, stats.by_short_code(short_code))


def _reserve_code(links: LinkRepository, url: str, length: int) -> str:
    for _ in range(_MAX_CODE_ATTEMPTS):
        candidate = generate(length)
        try:
            links.save(candidate, url)
            return candidate
        except ClientError as exc:
            if _is_conflict(exc):
                continue
            raise HTTPException(status_code=503, detail="storage error") from exc
    raise HTTPException(status_code=500, detail="could not allocate short code")


def _is_conflict(exc: ClientError) -> bool:
    return exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"
