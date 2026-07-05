FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

RUN groupadd --system --gid 1000 app && useradd --system --uid 1000 --gid app --home /app app

COPY --from=builder /install /usr/local
WORKDIR /app
COPY app ./app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    METRICS_PORT=9000

# numeric uid so the kubelet can verify the container runs as non-root under a
# runAsNonRoot policy without a non-numeric user lookup.
USER 1000
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['METRICS_PORT']}/metrics\")" || exit 1

CMD ["python", "-m", "app.main"]
