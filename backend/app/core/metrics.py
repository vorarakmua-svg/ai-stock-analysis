"""Prometheus metrics (uses prometheus_client directly; no extra deps)."""

from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
LLM_TOKENS = Counter(
    "llm_tokens_total",
    "LLM tokens consumed",
    ["model", "type"],
)


def record_llm_tokens(
    model: str, *, input_tokens: int, output_tokens: int, thinking_tokens: int
) -> None:
    """Increment the LLM token counters (called from record_llm_usage)."""
    LLM_TOKENS.labels(model=model, type="input").inc(input_tokens)
    LLM_TOKENS.labels(model=model, type="output").inc(output_tokens)
    LLM_TOKENS.labels(model=model, type="thinking").inc(thinking_tokens)


def metrics_response() -> Response:
    """Render the Prometheus exposition format for the /metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Count requests and observe latency, labeled by route template."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        # Use the matched route template (e.g. /stocks/{ticker}) to avoid
        # unbounded label cardinality from path params.
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        elapsed = time.perf_counter() - start
        HTTP_REQUEST_DURATION.labels(request.method, path).observe(elapsed)
        HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        return response
