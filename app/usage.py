"""
Usage Limits
============

Per-user usage limiting for the run endpoints (agents/teams/workflows).
Protects model spend from abuse with three layers:

- Burst: a sliding-window cap on run requests per minute, in memory
- Daily: a cap on runs per user per UTC day, persisted in Postgres
- Total: an absolute cap on runs per user, ever (sum over all days)

Users are identified by the authenticated ``request.state.user_id`` (set by
the AgentOS JWT middleware when RBAC is on); unauthenticated requests fall
back to the client IP. The internal scheduler, service accounts, and admin
callers are exempt.

Limits come from env defaults, overridable per user through the PostHog
``usage-limits`` feature flag (see ``PostHogLimits``). Over-limit requests
get a 429 with a machine-readable body (``error_code``, ``limit_type``,
``retry_after``, ``resets_at``) that the AgentOS UI can key a modal off.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from agno.os.middleware.jwt import INTERNAL_SCHEDULER_USER_ID, is_reserved_principal
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.routing import compile_path

logger = logging.getLogger(__name__)

# The POST routes that trigger model execution, as AgentOS mounts them.
# Cancel routes are deliberately absent — a limited user must be able to
# stop a run. Trailing slashes are already stripped by AgentOS's outermost
# TrailingSlashMiddleware before this middleware sees the path.
RUN_ROUTES = [
    "/agents/{agent_id}/runs",
    "/agents/{agent_id}/runs/{run_id}/continue",
    "/agents/{agent_id}/runs/{run_id}/resume",
    "/teams/{team_id}/runs",
    "/teams/{team_id}/runs/{run_id}/continue",
    "/teams/{team_id}/runs/{run_id}/resume",
    "/workflows/{workflow_id}/runs",
    "/workflows/{workflow_id}/runs/{run_id}/continue",
    "/workflows/{workflow_id}/runs/{run_id}/resume",
]

_RUN_ROUTE_PATTERNS = [compile_path(route)[0] for route in RUN_ROUTES]


def is_run_route(path: str) -> bool:
    return any(pattern.match(path) for pattern in _RUN_ROUTE_PATTERNS)


USAGE_TABLE = "demo_user_usage"


# ---------------------------------------------------------------------------
# Limit configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UsageLimits:
    """Effective limits for one user."""

    enabled: bool = True
    rpm: int = 10  # run requests per minute (burst)
    daily: int = 20  # runs per UTC day
    total: int = 200  # runs ever (absolute cap)


class PostHogLimits:
    """Resolves per-user limits from the PostHog ``usage-limits`` feature flag.

    The env-configured limits are the baseline. When PostHog is configured and
    the flag matches a user, its JSON payload overrides individual fields, e.g.
    ``{"daily": 100}`` to raise one user's quota or ``{"enabled": false}`` to
    lift limits entirely. A non-matching flag or any evaluation failure falls
    back to the baseline, so limits stay on if PostHog is down or the flag
    isn't rolled out. Results are cached per user for ``cache_ttl`` seconds.
    """

    FLAG_KEY = "usage-limits"

    def __init__(self, defaults: UsageLimits, api_key: str = "", host: str = "", cache_ttl: float = 60.0):
        self.defaults = defaults
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, UsageLimits]] = {}
        self._lock = threading.Lock()
        self._client = None
        if api_key:
            from posthog import Posthog

            self._client = Posthog(api_key, host=host, feature_flags_request_timeout_seconds=2)

    def resolve(self, user_key: str) -> UsageLimits:
        if self._client is None:
            return self.defaults

        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(user_key)
            if cached and now - cached[0] < self.cache_ttl:
                return cached[1]

        limits = self._evaluate(user_key)

        with self._lock:
            if len(self._cache) > 10_000:
                self._cache = {k: v for k, v in self._cache.items() if now - v[0] < self.cache_ttl}
            self._cache[user_key] = (now, limits)
        return limits

    def _evaluate(self, user_key: str) -> UsageLimits:
        try:
            assert self._client is not None
            match = self._client.get_feature_flag(self.FLAG_KEY, user_key, send_feature_flag_events=False)
            if not match:
                return self.defaults
            payload = self._client.get_feature_flag_payload(self.FLAG_KEY, user_key, match_value=match)
            if not isinstance(payload, dict):
                return self.defaults
            overrides = {
                field: payload[field]
                for field in ("enabled", "rpm", "daily", "total")
                if isinstance(payload.get(field), (bool, int))
            }
            return replace(self.defaults, **overrides)
        except Exception as e:  # noqa: BLE001 — flag evaluation must never block a run
            logger.warning(f"PostHog usage-limits flag evaluation failed, using defaults: {e}")
            return self.defaults


# ---------------------------------------------------------------------------
# Burst limit (sliding window, in memory)
# ---------------------------------------------------------------------------
class SlidingWindowLimiter:
    """Per-key sliding-window counter. In-memory, so per-process — fine for
    burst protection; the persistent quotas are the backstop."""

    def __init__(self, window_seconds: float = 60.0):
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_prune = time.monotonic()

    def hit(self, key: str, limit: int) -> float:
        """Record a request. Returns 0.0 if allowed, else seconds until a slot frees."""
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= limit:
                return self.window - (now - hits[0])
            hits.append(now)
            return 0.0

    def _prune(self, now: float) -> None:
        """Drop idle keys so the map doesn't grow unbounded. Called under the lock."""
        if now - self._last_prune < self.window:
            return
        self._last_prune = now
        idle = [key for key, hits in self._hits.items() if not hits or now - hits[-1] >= self.window]
        for key in idle:
            del self._hits[key]


# ---------------------------------------------------------------------------
# Run quotas (Postgres)
# ---------------------------------------------------------------------------
class RunQuota:
    """Per-user run counters backed by Postgres, keyed on (user_id, UTC day)."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self._table_ready = False
        self._lock = threading.Lock()

    def hit(self, user_id: str) -> tuple[int, int] | None:
        """Increment today's counter. Returns (today's count, all-time count).

        Returns None if the database is unavailable — callers fail open, since
        the run itself would surface the database error anyway.
        """
        try:
            self._ensure_table()
            with self.engine.begin() as conn:
                daily = conn.execute(
                    text(
                        f"""
                        INSERT INTO {USAGE_TABLE} (user_id, day, runs)
                        VALUES (:user_id, :day, 1)
                        ON CONFLICT (user_id, day)
                        DO UPDATE SET runs = {USAGE_TABLE}.runs + 1
                        RETURNING runs
                        """
                    ),
                    {"user_id": user_id, "day": datetime.now(UTC).date()},
                ).scalar_one()
                total = conn.execute(
                    text(f"SELECT COALESCE(SUM(runs), 0) FROM {USAGE_TABLE} WHERE user_id = :user_id"),
                    {"user_id": user_id},
                ).scalar_one()
            return int(daily), int(total)
        except SQLAlchemyError as e:
            logger.warning(f"Usage quota check failed, allowing request: {e}")
            return None

    def _ensure_table(self) -> None:
        if self._table_ready:
            return
        with self._lock:
            if self._table_ready:
                return
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {USAGE_TABLE} (
                            user_id TEXT NOT NULL,
                            day DATE NOT NULL,
                            runs INTEGER NOT NULL DEFAULT 0,
                            PRIMARY KEY (user_id, day)
                        )
                        """
                    )
                )
            self._table_ready = True


def next_utc_midnight() -> datetime:
    now = datetime.now(UTC)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
class UsageLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-user usage limits on run endpoints.

    Must run inside (after) the AgentOS JWT middleware so ``request.state.user_id``
    is populated — pre-add it to the ``base_app`` passed to AgentOS, which stacks
    its own middleware on top.
    """

    def __init__(
        self,
        app,
        limits: UsageLimits | None = None,
        posthog_api_key: str = "",
        posthog_host: str = "",
        engine: Engine | None = None,
        resolver: PostHogLimits | None = None,
    ):
        super().__init__(app)
        self.resolver = resolver or PostHogLimits(limits or UsageLimits(), api_key=posthog_api_key, host=posthog_host)
        self.burst = SlidingWindowLimiter()
        self._engine = engine
        self._quota: RunQuota | None = None

    @property
    def quota(self) -> RunQuota | None:
        # Resolved lazily so importing this module never forces a DB connection
        if self._quota is None:
            if self._engine is None:
                from app.settings import agent_db

                self._engine = agent_db.db_engine
            self._quota = RunQuota(self._engine)
        return self._quota

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST" or not is_run_route(request.url.path):
            return await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if self._is_exempt(request, user_id):
            return await call_next(request)

        key = user_id or f"ip:{self._client_ip(request)}"
        limits = self.resolver.resolve(key)
        if not limits.enabled:
            return await call_next(request)

        # Burst — checked first so throttled requests never consume quota
        retry_after = self.burst.hit(key, limits.rpm)
        if retry_after > 0:
            return self._limited(
                f"Rate limit exceeded: max {limits.rpm} run requests per minute.",
                limit_type="rate",
                limit=limits.rpm,
                retry_after=math.ceil(retry_after),
            )

        # Quotas — the absolute cap wins over the daily one
        counts = self.quota.hit(key) if self.quota else None
        if counts is not None:
            daily_count, total_count = counts
            if total_count > limits.total:
                return self._limited(
                    f"Usage exhausted: the limit of {limits.total} total runs has been reached.",
                    limit_type="total",
                    limit=limits.total,
                )
            if daily_count > limits.daily:
                resets_at = next_utc_midnight()
                return self._limited(
                    f"Daily usage limit reached ({limits.daily} runs per day). Resets at midnight UTC.",
                    limit_type="daily",
                    limit=limits.daily,
                    retry_after=max(1, int((resets_at - datetime.now(UTC)).total_seconds())),
                    resets_at=resets_at,
                )

        response = await call_next(request)
        if counts is not None:
            daily_count, total_count = counts
            response.headers["X-Usage-Daily-Limit"] = str(limits.daily)
            response.headers["X-Usage-Daily-Remaining"] = str(max(0, limits.daily - daily_count))
            response.headers["X-Usage-Total-Limit"] = str(limits.total)
            response.headers["X-Usage-Total-Remaining"] = str(max(0, limits.total - total_count))
        return response

    @staticmethod
    def _is_exempt(request: Request, user_id: str | None) -> bool:
        # Internal scheduler and service-account / MCP principals
        if user_id == INTERNAL_SCHEDULER_USER_ID or is_reserved_principal(user_id):
            return True
        # Admin-scoped callers (os.agno.com operators)
        scopes = getattr(request.state, "scopes", None)
        admin_scope = getattr(request.state, "admin_scope", None)
        return bool(admin_scope and scopes and admin_scope in scopes)

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _limited(
        detail: str,
        limit_type: str,
        limit: int,
        retry_after: int | None = None,
        resets_at: datetime | None = None,
    ) -> JSONResponse:
        """429 with a machine-readable body the AgentOS UI can key a modal off.

        ``limit_type`` is "rate", "daily", or "total"; a "total" response has no
        ``retry_after``/``resets_at`` — that usage never replenishes.
        """
        body: dict = {
            "detail": detail,
            "error_code": "usage_limit_exceeded",
            "limit_type": limit_type,
            "limit": limit,
        }
        headers = {}
        if retry_after is not None:
            body["retry_after"] = retry_after
            headers["Retry-After"] = str(retry_after)
        if resets_at is not None:
            body["resets_at"] = resets_at.isoformat()
        return JSONResponse(status_code=429, content=body, headers=headers)
