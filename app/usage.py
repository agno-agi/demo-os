"""
Usage Limits
============

Per-user usage limiting for run execution (agents/teams/workflows).
Protects model spend from abuse with three layers:

- Burst: a cap on runs per minute (fixed one-minute windows)
- Daily: a cap on runs per user per UTC day
- Total: an absolute cap on runs per user, ever

All three counters live on one Postgres row per user, so limits hold across
restarts and are shared by every container and worker process. A single
atomic upsert both checks and consumes quota: denied attempts never advance
a counter, and no counter can exceed its limit. If Postgres is unreachable
the gate fails closed (503) — a spend guard that fails open would hand out
unlimited free runs for the length of the outage.

Runs arrive on two surfaces, each with its own middleware sharing one
``UsageGate`` so both drain the same counters:

- REST ``POST`` run routes → ``UsageLimitMiddleware``. Users are identified
  by the authenticated ``request.state.user_id`` (set by the AgentOS JWT
  middleware when RBAC is on); unauthenticated requests fall back to the
  client IP. Over-limit requests get a 429 with a machine-readable body
  (``error_code``, ``limit_type``, ``retry_after``, ``resets_at``) that the
  AgentOS UI can key a modal off. A run the app rejects before executing
  (4xx: unknown id, malformed body, missing scope) is refunded.
- The workflow WebSocket (``/workflows/ws``), where runs are in-band
  ``start-workflow`` / ``continue-workflow`` messages →
  ``WebSocketUsageLimitMiddleware``. Over-limit messages are answered with
  an ``event: "error"`` frame carrying the same machine-readable fields.

The internal scheduler, service accounts, and admin callers are exempt on
both surfaces. Limits come from env defaults, overridable per user through
the PostHog ``usage-limits`` feature flag (see ``PostHogLimits``).
"""

from __future__ import annotations

import base64
import binascii
import ipaddress
import json
import logging
import threading
import time
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta

from agno.os.middleware.jwt import INTERNAL_SCHEDULER_USER_ID, is_reserved_principal
from agno.os.scopes import AgentOSScope
from agno.os.utils import resolve_ws_jwt_config
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
    and_,
    case,
    delete,
    func,
    inspect,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateTable
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.routing import compile_path
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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


def forwarded_client_ip(forwarded: str | None) -> str | None:
    """The rightmost ``X-Forwarded-For`` entry — the one our edge proxy appended.

    Leftmost entries are client-controlled (clients can send their own header
    and proxies append after it), so trusting them would let a caller mint a
    fresh limit bucket per request. Junk that doesn't parse as an IP is
    rejected so it can't become a DB key; callers fall back to the socket peer.
    """
    if not forwarded:
        return None
    candidate = forwarded.split(",")[-1].strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def socket_peer_ip(host: str | None) -> str:
    """The socket peer as a limit key, or ``"unknown"`` if it isn't an IP.

    Uvicorn's proxy-headers mode can rewrite the ASGI ``client`` tuple from the
    same client-controlled ``X-Forwarded-For`` header, so junk here is collapsed
    into one shared bucket rather than minting a per-request key.
    """
    if not host:
        return "unknown"
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "unknown"
    return host


# ---------------------------------------------------------------------------
# Limit configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UsageLimits:
    """Effective limits for one user."""

    enabled: bool = True
    rpm: int = 10  # runs per minute (burst)
    daily: int = 20  # runs per UTC day
    total: int = 200  # runs ever (absolute cap)


class PostHogLimits:
    """Resolves per-user limits from the PostHog ``usage-limits`` feature flag.

    The env-configured limits are the baseline. When PostHog is configured and
    the flag matches a user, its JSON payload overrides individual fields, e.g.
    ``{"daily": 100}`` to raise one user's quota, ``{"daily": 0}`` to block
    them, or ``{"enabled": false}`` to lift limits entirely. A non-matching
    flag or any evaluation failure falls back to the baseline, so limits stay
    on if PostHog is down or the flag isn't rolled out. Results are cached per
    user for ``cache_ttl`` seconds.
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

    def invalidate(self, user_key: str) -> None:
        """Drop one user's cached limits so a flag change applies immediately."""
        with self._lock:
            self._cache.pop(user_key, None)

    def invalidate_all(self) -> None:
        with self._lock:
            self._cache.clear()

    def _evaluate(self, user_key: str) -> UsageLimits:
        try:
            assert self._client is not None
            match = self._client.get_feature_flag(self.FLAG_KEY, user_key, send_feature_flag_events=False)
            if not match:
                return self.defaults
            payload = self._client.get_feature_flag_payload(self.FLAG_KEY, user_key, match_value=match)
            if not isinstance(payload, dict):
                return self.defaults
            overrides = self._overrides(payload, user_key)
            if overrides:
                logger.info(f"usage-limits flag overrides for {user_key}: {overrides}")
            return replace(self.defaults, **overrides)
        except Exception as e:  # noqa: BLE001 — flag evaluation must never block a run
            logger.warning(f"PostHog usage-limits flag evaluation failed, using defaults: {e}")
            return self.defaults

    @staticmethod
    def _overrides(payload: dict, user_key: str) -> dict:
        """Validate the flag payload field by field.

        The payload is hand-edited in the PostHog UI, so each field is checked
        strictly — ``enabled`` must be a bool (not a truthy int), the counts
        must be non-negative ints (``bool`` is an ``int`` subclass, so
        ``true`` is rejected explicitly). Anything invalid is logged and
        skipped, leaving that field on the env baseline.
        """
        overrides: dict = {}
        for field, value in payload.items():
            if field == "enabled":
                valid = type(value) is bool
            elif field in ("rpm", "daily", "total"):
                valid = type(value) is int and value >= 0
            else:
                valid = False
            if valid:
                overrides[field] = value
            else:
                logger.warning(f"Ignoring invalid usage-limits override for {user_key}: {field}={value!r}")
        return overrides


# ---------------------------------------------------------------------------
# Run counters (Postgres)
# ---------------------------------------------------------------------------
# One row per user carries all three windows. The minute and day columns
# record which window the counter next to them belongs to; a counter whose
# window has rolled over is treated as zero and reset by the next admitted
# run. Rows are never pruned: total_runs is the absolute cap's only memory,
# so the table is bounded by the number of distinct principals (JWT users
# under RBAC, IPs otherwise), not by time.
metadata = MetaData()
usage_table = Table(
    "demo_user_usage",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("minute", BigInteger, nullable=False),  # epoch minute of the burst window
    Column("minute_runs", Integer, nullable=False),  # runs admitted in that minute
    Column("day", Date, nullable=False),  # UTC day of the daily window
    Column("day_runs", Integer, nullable=False),  # runs admitted that day
    Column("total_runs", Integer, nullable=False),  # runs admitted, ever
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


@dataclass(frozen=True)
class QuotaHit:
    """Outcome of recording one run attempt."""

    admitted: bool
    limit_type: str = ""  # "rate" | "daily" | "total" when not admitted
    day_runs: int = 0
    total_runs: int = 0


class RunQuota:
    """Per-user run counters backed by Postgres.

    Postgres is the single source of truth, so every container and worker
    process drains the same counters. The burst window is a fixed minute, so
    it can briefly admit up to 2x the per-minute limit across a boundary,
    which the persistent quotas cap anyway.
    """

    SCHEMA_RETRY_SECONDS = 30.0

    def __init__(self, engine: Engine, db_schema: str | None = None):
        self.engine = engine
        self.db_schema = db_schema
        # A schema-qualified clone of the declared table. Without this the DDL
        # is unqualified and lands wherever search_path points (public — or the
        # "$user" schema when the DB user happens to share its name), instead
        # of next to agno's own tables.
        meta = MetaData()
        self.table = usage_table.to_metadata(meta, schema=db_schema) if db_schema else usage_table.to_metadata(meta)
        self._schema_ready = False
        self._retry_schema_at = 0.0
        self._lock = threading.Lock()

    def prepare(self) -> bool:
        """Create the usage table if it doesn't exist. Safe to call at startup and again lazily."""
        return self._ensure_schema()

    def hit(self, user_id: str, limits: UsageLimits, day: date, minute: int) -> QuotaHit | None:
        """Admit one run for ``user_id`` if every limit still has headroom.

        A single upsert checks and consumes atomically: windows that have
        rolled over are reset, and the counters only advance when the row's
        current values are all below their limits — so a denied attempt
        changes nothing and no counter can exceed its limit. Returns None if
        the database is unavailable; callers fail closed.
        """
        # A zero limit admits nothing, and the insert path below has no check
        if limits.rpm < 1:
            return QuotaHit(admitted=False, limit_type="rate")
        if limits.total < 1:
            return QuotaHit(admitted=False, limit_type="total")
        if limits.daily < 1:
            return QuotaHit(admitted=False, limit_type="daily")
        if not self._ensure_schema():
            return None

        u = self.table.c
        in_minute = case((u.minute == minute, u.minute_runs), else_=0)
        in_day = case((u.day == day, u.day_runs), else_=0)
        stmt = (
            pg_insert(self.table)
            .values(
                user_id=user_id, minute=minute, minute_runs=1, day=day, day_runs=1, total_runs=1, updated_at=func.now()
            )
            .on_conflict_do_update(
                index_elements=[u.user_id],
                set_={
                    "minute": minute,
                    "minute_runs": in_minute + 1,
                    "day": day,
                    "day_runs": in_day + 1,
                    "total_runs": u.total_runs + 1,
                    "updated_at": func.now(),
                },
                where=and_(in_minute < limits.rpm, in_day < limits.daily, u.total_runs < limits.total),
            )
            .returning(u.day_runs, u.total_runs)
        )
        try:
            with self.engine.begin() as conn:
                row = conn.execute(stmt).one_or_none()
                if row is not None:
                    return QuotaHit(admitted=True, day_runs=row.day_runs, total_runs=row.total_runs)
                # Nothing updated — the row exists and some limit has no headroom
                current = conn.execute(
                    select(u.minute, u.minute_runs, u.day, u.day_runs, u.total_runs).where(u.user_id == user_id)
                ).one()
        except SQLAlchemyError as e:
            logger.error(f"Usage quota check failed for {user_id}: {e}")
            return None

        minute_runs = current.minute_runs if current.minute == minute else 0
        day_runs = current.day_runs if current.day == day else 0
        if minute_runs >= limits.rpm:
            limit_type = "rate"
        elif current.total_runs >= limits.total:
            limit_type = "total"
        else:
            limit_type = "daily"
        return QuotaHit(admitted=False, limit_type=limit_type, day_runs=day_runs, total_runs=current.total_runs)

    def refund(self, user_id: str, day: date) -> None:
        """Give back one admitted run that never executed.

        Restores the daily and absolute quotas (the daily one only if the
        window is still ``day``). The burst counter is deliberately left alone:
        it bounds request pressure, and a client looping on bad requests
        should still be throttled.
        """
        u = self.table.c
        stmt = (
            update(self.table)
            .where(u.user_id == user_id)
            .values(
                day_runs=case((u.day == day, func.greatest(u.day_runs - 1, 0)), else_=u.day_runs),
                total_runs=func.greatest(u.total_runs - 1, 0),
            )
        )
        try:
            with self.engine.begin() as conn:
                conn.execute(stmt)
        except SQLAlchemyError as e:
            logger.warning(f"Usage quota refund failed for {user_id}: {e}")

    def snapshot(self, user_id: str, day: date, minute: int) -> dict:
        """Current consumption for one user, with rolled-over windows read as zero."""
        u = self.table.c
        with self.engine.begin() as conn:
            row = conn.execute(
                select(u.minute, u.minute_runs, u.day, u.day_runs, u.total_runs).where(u.user_id == user_id)
            ).one_or_none()
        if row is None:
            return {"minute_runs": 0, "day_runs": 0, "total_runs": 0}
        return {
            "minute_runs": row.minute_runs if row.minute == minute else 0,
            "day_runs": row.day_runs if row.day == day else 0,
            "total_runs": row.total_runs,
        }

    def reset(self, user_id: str) -> bool:
        """Delete one user's row — resets all three counters, lifetime cap included."""
        with self.engine.begin() as conn:
            return conn.execute(delete(self.table).where(self.table.c.user_id == user_id)).rowcount > 0

    def reset_all(self) -> int:
        """Delete every row. Returns how many users were reset."""
        with self.engine.begin() as conn:
            return conn.execute(delete(self.table)).rowcount

    def _ensure_schema(self) -> bool:
        if self._schema_ready:
            return True
        with self._lock:
            if self._schema_ready:
                return True
            now = time.monotonic()
            if now < self._retry_schema_at:
                return False
            try:
                with self.engine.begin() as conn:
                    if self.db_schema:
                        # Same sequence agno's PostgresDb uses for its tables, so
                        # this works on a fresh database before AgentOS has run
                        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.db_schema}"'))
                    conn.execute(CreateTable(self.table, if_not_exists=True))
            except SQLAlchemyError as e:
                # Another worker may have won a create race — then the table is there
                if not self._table_exists():
                    return self._schema_failed(now, f"Could not create {self.qualified_name}: {e}")
            try:
                missing = self._missing_columns()
            except SQLAlchemyError as e:
                return self._schema_failed(now, f"Could not inspect {self.qualified_name}: {e}")
            if missing:
                # A table from an older revision of this module: IF NOT EXISTS kept
                # it and every upsert would fail on it. Say so once, with the
                # remedy, rather than 503-ing per request with a raw SQL error.
                return self._schema_failed(
                    now,
                    f"{self.qualified_name} exists with an older schema (missing columns {sorted(missing)}); "
                    f"drop it so it can be recreated: DROP TABLE {self.qualified_name}",
                )
            self._schema_ready = True
            return True

    def _schema_failed(self, now: float, reason: str) -> bool:
        self._retry_schema_at = now + self.SCHEMA_RETRY_SECONDS
        logger.error(f"{reason} — retrying in {self.SCHEMA_RETRY_SECONDS:.0f}s")
        return False

    def _table_exists(self) -> bool:
        try:
            return inspect(self.engine).has_table(self.table.name, schema=self.db_schema)
        except SQLAlchemyError:
            return False

    def _missing_columns(self) -> set[str]:
        present = {col["name"] for col in inspect(self.engine).get_columns(self.table.name, schema=self.db_schema)}
        return {col.name for col in self.table.columns} - present

    @property
    def qualified_name(self) -> str:
        return f"{self.db_schema}.{self.table.name}" if self.db_schema else self.table.name


def next_utc_midnight() -> datetime:
    now = datetime.now(UTC)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Shared enforcement core
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LimitVerdict:
    """Outcome of a limit check.

    Denials carry the fields both surfaces serialize for the client via
    ``payload()`` (``limit_type`` is "rate", "daily", or "total"; a "total"
    denial has no ``retry_after``/``resets_at`` — that usage never
    replenishes). A 503 denial means the counters were unreachable. Allowed
    verdicts that consumed quota carry the ``day`` it was charged to (for
    refunds) and the remaining counts (for the HTTP response headers).
    """

    allowed: bool
    detail: str = ""
    status_code: int = 429
    error_code: str = "usage_limit_exceeded"
    limit_type: str = ""
    limit: int = 0
    retry_after: int | None = None
    resets_at: datetime | None = None
    day: date | None = None
    daily_limit: int | None = None
    daily_remaining: int | None = None
    total_limit: int | None = None
    total_remaining: int | None = None

    def payload(self) -> dict:
        """The machine-readable denial fields shared by the 429 body and the WS error frame."""
        body: dict = {"error_code": self.error_code}
        if self.limit_type:
            body["limit_type"] = self.limit_type
            body["limit"] = self.limit
        if self.retry_after is not None:
            body["retry_after"] = self.retry_after
        if self.resets_at is not None:
            body["resets_at"] = self.resets_at.isoformat()
        return body


class UsageGate:
    """Shared limit enforcement: PostHog-resolved limits over Postgres-backed
    counters. One instance backs both the HTTP middleware and the WebSocket
    middleware so runs on either surface drain the same counters.
    """

    def __init__(
        self,
        limits: UsageLimits | None = None,
        posthog_api_key: str = "",
        posthog_host: str = "",
        engine: Engine | None = None,
        db_schema: str | None = None,
        resolver: PostHogLimits | None = None,
    ):
        self.resolver = resolver or PostHogLimits(limits or UsageLimits(), api_key=posthog_api_key, host=posthog_host)
        self._engine = engine
        self._db_schema = db_schema
        self._quota: RunQuota | None = None

    @property
    def quota(self) -> RunQuota:
        # Resolved lazily so importing this module never forces a DB connection.
        # When no engine is given, both it and the schema come from agent_db so
        # the counter table lands next to agno's own tables.
        if self._quota is None:
            if self._engine is None:
                from app.settings import agent_db

                self._engine = agent_db.db_engine
                self._db_schema = self._db_schema or agent_db.db_schema
            self._quota = RunQuota(self._engine, db_schema=self._db_schema)
        return self._quota

    def prepare(self) -> None:
        """Create the counter table at startup so the first user request doesn't pay for DDL.

        Raises on failure: a stale table or missing privilege is a deploy-time
        problem, and failing the rollout beats booting an app whose every run
        503s until someone reads the log. Runtime DB blips are still handled
        by the lazy 30s-backoff path.
        """
        if not self.quota.prepare():
            raise RuntimeError(
                f"Usage limits could not initialize {self.quota.qualified_name} (see log above); "
                "refusing to start rather than serve runs that all fail closed"
            )
        logger.info(f"Usage limits ready ({self.quota.qualified_name})")

    def check(self, key: str) -> LimitVerdict:
        """Consume one run for ``key`` if it's within limits and say whether it may proceed.

        Synchronous (DB round-trips plus, on cache miss, a PostHog HTTP call) —
        async callers must dispatch via ``run_in_threadpool`` to keep the event
        loop free.
        """
        limits = self.resolver.resolve(key)
        if not limits.enabled:
            return LimitVerdict(allowed=True)

        now = datetime.now(UTC)
        day = now.date()
        hit = self.quota.hit(key, limits, day=day, minute=int(now.timestamp()) // 60)
        if hit is None:
            # Fail closed: an unreachable counter must not mean unlimited free runs
            return LimitVerdict(
                allowed=False,
                detail="Usage limits are temporarily unavailable. Please retry shortly.",
                status_code=503,
                error_code="usage_limit_unavailable",
                retry_after=5,
            )
        if hit.admitted:
            return LimitVerdict(
                allowed=True,
                day=day,
                daily_limit=limits.daily,
                daily_remaining=max(0, limits.daily - hit.day_runs),
                total_limit=limits.total,
                total_remaining=max(0, limits.total - hit.total_runs),
            )
        if hit.limit_type == "rate":
            return LimitVerdict(
                allowed=False,
                detail=f"Rate limit exceeded: max {limits.rpm} runs per minute.",
                limit_type="rate",
                limit=limits.rpm,
                retry_after=max(1, 60 - int(now.timestamp()) % 60),
            )
        if hit.limit_type == "total":
            return LimitVerdict(
                allowed=False,
                detail=f"Usage exhausted: the limit of {limits.total} total runs has been reached.",
                limit_type="total",
                limit=limits.total,
            )
        resets_at = next_utc_midnight()
        return LimitVerdict(
            allowed=False,
            detail=f"Daily usage limit reached ({limits.daily} runs per day). Resets at midnight UTC.",
            limit_type="daily",
            limit=limits.daily,
            retry_after=max(1, int((resets_at - now).total_seconds())),
            resets_at=resets_at,
        )

    def refund(self, key: str, day: date) -> None:
        """Give back a run that ``check`` consumed but the app rejected before executing."""
        self.quota.refund(key, day)

    def describe(self, key: str) -> dict:
        """Effective limits and current consumption for one user key."""
        limits = self.resolver.resolve(key)
        now = datetime.now(UTC)
        usage = self.quota.snapshot(key, day=now.date(), minute=int(now.timestamp()) // 60)
        return {
            "user_id": key,
            "limits": {"enabled": limits.enabled, "rpm": limits.rpm, "daily": limits.daily, "total": limits.total},
            "usage": usage,
            "remaining": {
                "daily": max(0, limits.daily - usage["day_runs"]),
                "total": max(0, limits.total - usage["total_runs"]),
            },
        }

    def reset_usage(self, key: str) -> bool:
        """Wipe one user's counters (lifetime cap included) and their cached flag limits."""
        self.resolver.invalidate(key)
        return self.quota.reset(key)

    def reset_all_usage(self) -> int:
        """Wipe every user's counters and the whole flag cache. Returns users reset."""
        self.resolver.invalidate_all()
        return self.quota.reset_all()


# ---------------------------------------------------------------------------
# HTTP middleware (REST run routes)
# ---------------------------------------------------------------------------
class UsageLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-user usage limits on the REST run endpoints.

    Must run inside (after) the AgentOS JWT middleware so ``request.state.user_id``
    is populated — pre-add it to the ``base_app`` passed to AgentOS, which stacks
    its own middleware on top.
    """

    def __init__(self, app: ASGIApp, gate: UsageGate):
        super().__init__(app)
        self.gate = gate

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method != "POST" or not is_run_route(request.url.path):
            return await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if self._is_exempt(request, user_id):
            return await call_next(request)

        key = user_id or f"ip:{self._client_ip(request)}"
        # Threadpool: the gate does blocking DB and PostHog I/O
        verdict = await run_in_threadpool(self.gate.check, key)
        if not verdict.allowed:
            return self._limited(verdict)

        response = await call_next(request)
        if verdict.day is not None and 400 <= response.status_code < 500:
            # The app rejected the request before any model call (unknown id,
            # malformed body, missing scope) — don't let it burn the caps.
            await run_in_threadpool(self.gate.refund, key, verdict.day)
        elif verdict.daily_limit is not None:
            response.headers["X-Usage-Daily-Limit"] = str(verdict.daily_limit)
            response.headers["X-Usage-Daily-Remaining"] = str(verdict.daily_remaining)
            response.headers["X-Usage-Total-Limit"] = str(verdict.total_limit)
            response.headers["X-Usage-Total-Remaining"] = str(verdict.total_remaining)
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
        forwarded = forwarded_client_ip(request.headers.get("x-forwarded-for"))
        if forwarded:
            return forwarded
        return socket_peer_ip(request.client.host if request.client else None)

    @staticmethod
    def _limited(verdict: LimitVerdict) -> JSONResponse:
        """429 (or 503 when the counters are unreachable) with a body the AgentOS UI can key a modal off."""
        headers = {}
        if verdict.retry_after is not None:
            headers["Retry-After"] = str(verdict.retry_after)
        return JSONResponse(
            status_code=verdict.status_code, content={"detail": verdict.detail, **verdict.payload()}, headers=headers
        )


# ---------------------------------------------------------------------------
# WebSocket middleware (workflow runs over /workflows/ws)
# ---------------------------------------------------------------------------
WORKFLOW_WS_PATH = "/workflows/ws"

# The in-band actions that trigger model execution. `reconnect` is absent —
# subscribing to an existing run's events spends nothing — and there is no
# cancel over the socket to worry about.
WS_RUN_ACTIONS = frozenset({"start-workflow", "continue-workflow"})


@dataclass
class _WsConnectionState:
    """Per-connection identity learned from the in-band auth handshake."""

    client_ip: str
    user_id: str | None = None
    exempt: bool = False
    awaiting_auth: bool = False
    pending_token: str | None = None
    requires_auth: bool | None = None  # resolved lazily on first run action


class WebSocketUsageLimitMiddleware:
    """Enforce the same usage limits on workflow runs arriving over the socket.

    ``BaseHTTPMiddleware`` never sees websocket scopes, and the socket carries
    runs as in-band messages, so this is a pure ASGI middleware that wraps the
    ``receive``/``send`` pair of ``/workflows/ws`` connections:

    - Outbound ``authenticated`` events are observed to learn the verified
      identity — the app only emits that event after validating the token, so
      no token verification is duplicated here. Reserved principals (internal
      scheduler, service accounts) and admin-scoped callers are exempt,
      mirroring the HTTP middleware.
    - Inbound ``start-workflow`` / ``continue-workflow`` frames are checked
      against the shared ``UsageGate``. An over-limit frame is swallowed (the
      run never reaches the app) and answered with an ``event: "error"`` frame
      carrying the same machine-readable fields as the HTTP 429 body.

    Unauthenticated run frames on auth-required connections pass through
    uncounted: the app rejects them itself, and rejected attempts must not
    drain the per-IP counters. Legacy ``os_security_key`` auth attaches no
    identity, so runs on such connections are not limited (demo-os does not
    use that mode).

    Unlike the HTTP surface, a run frame the app rejects (unknown workflow id)
    is not refunded: the app answers with a plain ``error`` frame that can't be
    safely attributed to one frame while other runs stream on the same
    connection, and a client-triggerable refund would be a way to reclaim
    counted runs. The AgentOS UI only sends ids it listed, so this costs
    legitimate users nothing.
    """

    def __init__(self, app: ASGIApp, gate: UsageGate):
        self.app = app
        self.gate = gate

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "websocket" or scope["path"].rstrip("/") != WORKFLOW_WS_PATH:
            await self.app(scope, receive, send)
            return
        state = _WsConnectionState(client_ip=self._client_ip(scope))
        await self.app(
            scope, self._guarded_receive(scope, receive, send, state), self._observing_send(scope, send, state)
        )

    def _guarded_receive(self, scope: Scope, receive: Receive, send: Send, state: _WsConnectionState) -> Receive:
        async def guarded() -> Message:
            while True:
                message = await receive()
                if message["type"] != "websocket.receive":
                    return message
                frame = self._parse_frame(message.get("text"))
                if frame is None:
                    return message
                action = frame.get("action")
                if action == "authenticate":
                    # Remember the token so scopes can be read once the app
                    # confirms it (see _identify); watch for that confirmation.
                    state.awaiting_auth = True
                    token = frame.get("token")
                    state.pending_token = token if isinstance(token, str) else None
                    return message
                if action not in WS_RUN_ACTIONS or state.exempt:
                    return message
                if state.user_id is None:
                    if state.requires_auth is None:
                        state.requires_auth = self._auth_required(scope)
                    if state.requires_auth:
                        return message  # app rejects unauthenticated runs itself
                key = state.user_id or f"ip:{state.client_ip}"
                # Threadpool: the gate does blocking DB and PostHog I/O
                verdict = await run_in_threadpool(self.gate.check, key)
                if verdict.allowed:
                    return message
                await send({"type": "websocket.send", "text": json.dumps(self._limit_event(verdict))})
                # Swallow the frame and wait for the client's next message

        return guarded

    def _observing_send(self, scope: Scope, send: Send, state: _WsConnectionState) -> Send:
        async def observing(message: Message) -> None:
            # Only frames of the auth handshake are inspected; once it settles,
            # streamed run events pass through without parsing overhead.
            if state.awaiting_auth and message["type"] == "websocket.send":
                frame = self._parse_frame(message.get("text"))
                if frame is not None:
                    event = frame.get("event")
                    if event == "authenticated":
                        state.awaiting_auth = False
                        self._identify(scope, state, frame.get("user_id"))
                    elif event == "auth_error":
                        state.awaiting_auth = False
                        state.pending_token = None
            await send(message)

        return observing

    def _identify(self, scope: Scope, state: _WsConnectionState, user_id: object) -> None:
        """Record the app-verified identity and resolve exemptions."""
        if isinstance(user_id, str) and user_id:
            state.user_id = user_id
        token, state.pending_token = state.pending_token, None
        if state.user_id is None:
            return
        # Internal scheduler and service-account / MCP principals
        if state.user_id == INTERNAL_SCHEDULER_USER_ID or is_reserved_principal(state.user_id):
            state.exempt = True
            return
        # Admin-scoped callers (os.agno.com operators)
        scopes = self._token_scopes(scope, token)
        app_state = getattr(scope.get("app"), "state", None)
        admin_scope = getattr(app_state, "admin_scope", None) or AgentOSScope.ADMIN.value
        state.exempt = admin_scope in scopes

    @staticmethod
    def _token_scopes(scope: Scope, token: str | None) -> list[str]:
        """Scopes from the JWT the app just verified.

        Decoded without verification — ``_identify`` only runs after the app
        emitted ``authenticated`` for this exact token. The validator's claim
        mapping is used when available so a custom ``scopes_claim`` is honored.
        """
        if not token or token.count(".") != 2:
            return []
        segment = token.split(".")[1]
        try:
            payload = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        except (ValueError, TypeError, binascii.Error):
            return []
        if not isinstance(payload, dict):
            return []
        app = scope.get("app")
        if app is not None:
            try:
                validator = resolve_ws_jwt_config(app).get("validator")
                if validator is not None:
                    return list(validator.extract_claims(payload).get("scopes") or [])
            except Exception as e:  # noqa: BLE001 — exemption is best-effort, limits stay on
                logger.warning(f"WS scope extraction via validator failed, using raw claim: {e}")
        scopes = payload.get("scopes")
        return list(scopes) if isinstance(scopes, list) else []

    @staticmethod
    def _auth_required(scope: Scope) -> bool:
        """Whether the app will reject unauthenticated run actions on this socket."""
        app = scope.get("app")
        if app is None:
            return False
        try:
            cfg = resolve_ws_jwt_config(app)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"WS auth config resolution failed, treating socket as unauthenticated: {e}")
            return False
        if cfg.get("validator") is not None or cfg.get("auth_required"):
            return True
        from agno.os.settings import AgnoAPISettings

        return bool(AgnoAPISettings().os_security_key)

    @staticmethod
    def _parse_frame(text: object) -> dict | None:
        if not isinstance(text, str) or not text:
            return None
        try:
            frame = json.loads(text)
        except ValueError:
            return None
        return frame if isinstance(frame, dict) else None

    @staticmethod
    def _client_ip(scope: Scope) -> str:
        for name, value in scope.get("headers") or []:
            if name == b"x-forwarded-for":
                forwarded = forwarded_client_ip(value.decode("latin-1"))
                if forwarded:
                    return forwarded
                break
        client = scope.get("client")
        return socket_peer_ip(client[0] if client else None)

    @staticmethod
    def _limit_event(verdict: LimitVerdict) -> dict:
        """The socket-shaped mirror of the HTTP 429 body."""
        return {"event": "error", "error": verdict.detail, **verdict.payload()}


# ---------------------------------------------------------------------------
# Admin API (inspect and reset usage)
# ---------------------------------------------------------------------------
def usage_admin_router(gate: UsageGate, allow_unauthenticated: bool = False) -> APIRouter:
    """Admin endpoints so support doesn't need psql or a redeploy.

    - ``GET /usage/{user_id}`` — effective limits (env + PostHog flag) and
      current consumption for one key (``ip:…`` or a JWT user id).
    - ``DELETE /usage/{user_id}`` — reset one user: deletes their row (all
      three counters, lifetime cap included) and drops their cached flag
      limits so a simultaneous flag edit applies immediately.
    - ``DELETE /usage`` — reset everyone.

    *Changing* limits is not an API concern: per-user values live in the
    PostHog ``usage-limits`` flag (live within the 60s cache) and the env
    baseline stays a deploy setting.

    Access: admin-scoped callers only — the same bar as the middleware
    exemption. With RBAC off there is no admin identity, so the endpoints
    are locked (403) rather than open; ``allow_unauthenticated=True`` (dev)
    opens them for local testing. Counter-DB errors surface as 503.
    """

    def require_admin(request: Request) -> None:
        if allow_unauthenticated:
            return
        scopes = getattr(request.state, "scopes", None)
        admin_scope = getattr(request.state, "admin_scope", None)
        if not (admin_scope and scopes and admin_scope in scopes):
            raise HTTPException(status_code=403, detail="Admin scope required")

    router = APIRouter(prefix="/usage", tags=["Usage"], dependencies=[Depends(require_admin)])

    @router.get("/{user_id}")
    async def read_usage(user_id: str) -> dict:
        try:
            return await run_in_threadpool(gate.describe, user_id)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=503, detail="Usage counters are temporarily unavailable") from e

    @router.delete("/{user_id}")
    async def reset_usage(user_id: str) -> dict:
        try:
            existed = await run_in_threadpool(gate.reset_usage, user_id)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=503, detail="Usage counters are temporarily unavailable") from e
        return {"user_id": user_id, "reset": existed}

    @router.delete("")
    async def reset_all_usage() -> dict:
        try:
            count = await run_in_threadpool(gate.reset_all_usage)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=503, detail="Usage counters are temporarily unavailable") from e
        return {"reset_users": count}

    return router
