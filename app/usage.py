"""
Usage Limits
============

Per-user usage limiting for the run endpoints (agents/teams/workflows).
Protects model spend from abuse with two layers:

- Burst: a sliding-window cap on run requests per minute, in memory
- Quota: a daily cap on runs per user, persisted in Postgres so it
  survives restarts and redeploys

Users are identified by the authenticated ``request.state.user_id`` (set by
the AgentOS JWT middleware when RBAC is on); unauthenticated requests fall
back to the client IP. The internal scheduler, service accounts, and admin
callers are exempt.
"""

from __future__ import annotations

import logging
import math
import re
import threading
import time
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from agno.os.middleware.jwt import INTERNAL_SCHEDULER_USER_ID, is_reserved_principal
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)

# POST endpoints that trigger model execution: run create, continue, resume.
# Cancel is deliberately excluded — a limited user must be able to stop a run.
RUN_PATH = re.compile(r"^/(agents|teams|workflows)/[^/]+/runs(/[^/]+/(continue|resume))?/?$")

USAGE_TABLE = "demo_user_usage"


# ---------------------------------------------------------------------------
# Burst limit (sliding window, in memory)
# ---------------------------------------------------------------------------
class SlidingWindowLimiter:
    """Per-key sliding-window counter. In-memory, so per-process — fine for
    burst protection; the persistent daily quota is the backstop."""

    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_prune = time.monotonic()

    def hit(self, key: str) -> float:
        """Record a request. Returns 0.0 if allowed, else seconds until a slot frees."""
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= self.limit:
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
# Daily quota (Postgres)
# ---------------------------------------------------------------------------
class DailyQuota:
    """Per-user daily run counter backed by Postgres, keyed on (user_id, UTC day)."""

    def __init__(self, engine: Engine, limit: int):
        self.engine = engine
        self.limit = limit
        self._table_ready = False
        self._lock = threading.Lock()

    def hit(self, user_id: str) -> int | None:
        """Increment today's counter and return the new count.

        Returns None if the database is unavailable — callers fail open, since
        the run itself would surface the database error anyway.
        """
        try:
            self._ensure_table()
            with self.engine.begin() as conn:
                count = conn.execute(
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
            return int(count)
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


def seconds_until_utc_midnight() -> int:
    now = datetime.now(UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((tomorrow - now).total_seconds()))


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
class UsageLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-user usage limits on run endpoints.

    Must run inside (after) the AgentOS JWT middleware so ``request.state.user_id``
    is populated — pre-add it to the ``base_app`` passed to AgentOS, which stacks
    its own middleware on top.
    """

    def __init__(self, app, rate_limit_rpm: int = 10, daily_run_limit: int = 50, engine: Engine | None = None):
        super().__init__(app)
        self.burst = SlidingWindowLimiter(limit=rate_limit_rpm)
        self.daily_run_limit = daily_run_limit
        self._engine = engine
        self._quota: DailyQuota | None = None

    @property
    def quota(self) -> DailyQuota | None:
        # Resolved lazily so importing this module never forces a DB connection
        if self._quota is None:
            if self._engine is None:
                from app.settings import agent_db

                self._engine = agent_db.db_engine
            self._quota = DailyQuota(self._engine, self.daily_run_limit)
        return self._quota

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST" or not RUN_PATH.match(request.url.path):
            return await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if self._is_exempt(request, user_id):
            return await call_next(request)

        key = user_id or f"ip:{self._client_ip(request)}"

        # Burst — checked first so throttled requests never consume quota
        retry_after = self.burst.hit(key)
        if retry_after > 0:
            return self._limited(
                f"Rate limit exceeded: max {self.burst.limit} run requests per minute.",
                retry_after=math.ceil(retry_after),
            )

        # Daily quota
        count = self.quota.hit(key) if self.quota else None
        if count is not None and count > self.daily_run_limit:
            return self._limited(
                f"Daily usage limit reached ({self.daily_run_limit} runs per day). Resets at midnight UTC.",
                retry_after=seconds_until_utc_midnight(),
            )

        response = await call_next(request)
        if count is not None:
            response.headers["X-Usage-Daily-Limit"] = str(self.daily_run_limit)
            response.headers["X-Usage-Daily-Remaining"] = str(max(0, self.daily_run_limit - count))
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
    def _limited(detail: str, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": detail},
            headers={"Retry-After": str(retry_after)},
        )
