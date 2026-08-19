"""
Usage Limits
============

Per-user usage limiting for run execution (agents/teams/workflows).
Protects model spend from abuse with three layers:

- Burst: a cap on run requests per minute (fixed one-minute windows)
- Daily: a cap on runs per user per UTC day
- Total: an absolute cap on runs per user, ever (sum over all days)

All three counters live in Postgres, so limits hold across restarts and are
shared by every container and worker process.

Runs arrive on two surfaces, each with its own middleware sharing one
``UsageGate`` so both drain the same counters:

- REST ``POST`` run routes → ``UsageLimitMiddleware``. Users are identified
  by the authenticated ``request.state.user_id`` (set by the AgentOS JWT
  middleware when RBAC is on); unauthenticated requests fall back to the
  client IP. Over-limit requests get a 429 with a machine-readable body
  (``error_code``, ``limit_type``, ``retry_after``, ``resets_at``) that the
  AgentOS UI can key a modal off.
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
from datetime import UTC, datetime, timedelta

from agno.os.middleware.jwt import INTERNAL_SCHEDULER_USER_ID, is_reserved_principal
from agno.os.scopes import AgentOSScope
from agno.os.utils import resolve_ws_jwt_config
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
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


USAGE_TABLE = "demo_user_usage"
USAGE_MINUTE_TABLE = "demo_user_usage_minute"


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
# Run counters (Postgres)
# ---------------------------------------------------------------------------
class RunQuota:
    """Per-user run counters backed by Postgres.

    Two tables: ``USAGE_TABLE`` keyed on (user_id, UTC day) for the daily and
    all-time quotas, and ``USAGE_MINUTE_TABLE`` keyed on (user_id, epoch
    minute) for the burst window. Postgres is the single source of truth, so
    every container and worker process drains the same counters — a fixed
    one-minute window can briefly admit up to 2x the per-minute limit across
    a boundary, which the persistent quotas cap anyway.
    """

    def __init__(self, engine: Engine):
        self.engine = engine
        self._table_ready = False
        self._lock = threading.Lock()

    def hit(self, user_id: str, rpm: int) -> tuple[int, int | None, int | None] | None:
        """Record one attempt. Returns (this minute's count, today's count, all-time count).

        A burst-limited attempt (minute count above ``rpm``) does not consume
        the daily/total quotas — those come back as None. Returns None if the
        database is unavailable; callers fail open, since the run itself would
        surface the database error anyway.
        """
        try:
            self._ensure_table()
            minute = int(time.time()) // 60
            with self.engine.begin() as conn:
                burst = conn.execute(
                    text(
                        f"""
                        INSERT INTO {USAGE_MINUTE_TABLE} (user_id, minute, runs)
                        VALUES (:user_id, :minute, 1)
                        ON CONFLICT (user_id, minute)
                        DO UPDATE SET runs = {USAGE_MINUTE_TABLE}.runs + 1
                        RETURNING runs
                        """
                    ),
                    {"user_id": user_id, "minute": minute},
                ).scalar_one()
                conn.execute(
                    text(f"DELETE FROM {USAGE_MINUTE_TABLE} WHERE user_id = :user_id AND minute < :cutoff"),
                    {"user_id": user_id, "cutoff": minute - 1},
                )
                if int(burst) > rpm:
                    return int(burst), None, None
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
            return int(burst), int(daily), int(total)
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
                conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {USAGE_MINUTE_TABLE} (
                            user_id TEXT NOT NULL,
                            minute BIGINT NOT NULL,
                            runs INTEGER NOT NULL DEFAULT 0,
                            PRIMARY KEY (user_id, minute)
                        )
                        """
                    )
                )
            self._table_ready = True


def next_utc_midnight() -> datetime:
    now = datetime.now(UTC)
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Shared enforcement core
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LimitVerdict:
    """Outcome of a limit check.

    Denials carry the fields both surfaces serialize for the client
    (``limit_type`` is "rate", "daily", or "total"; a "total" denial has no
    ``retry_after``/``resets_at`` — that usage never replenishes). Allowed
    verdicts carry remaining counts when the quota was consulted, for the
    HTTP response headers.
    """

    allowed: bool
    detail: str = ""
    limit_type: str = ""
    limit: int = 0
    retry_after: int | None = None
    resets_at: datetime | None = None
    daily_limit: int | None = None
    daily_remaining: int | None = None
    total_limit: int | None = None
    total_remaining: int | None = None


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
        resolver: PostHogLimits | None = None,
    ):
        self.resolver = resolver or PostHogLimits(limits or UsageLimits(), api_key=posthog_api_key, host=posthog_host)
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

    def check(self, key: str) -> LimitVerdict:
        """Record one run attempt for ``key`` and decide whether it may proceed.

        Synchronous (DB round-trips plus, on cache miss, a PostHog HTTP call) —
        async callers must dispatch via ``run_in_threadpool`` to keep the event
        loop free.
        """
        limits = self.resolver.resolve(key)
        if not limits.enabled:
            return LimitVerdict(allowed=True)

        counts = self.quota.hit(key, limits.rpm) if self.quota else None
        if counts is None:
            return LimitVerdict(allowed=True)
        _, daily_count, total_count = counts

        # Burst — checked first; throttled attempts never consume quota
        if daily_count is None or total_count is None:
            return LimitVerdict(
                allowed=False,
                detail=f"Rate limit exceeded: max {limits.rpm} run requests per minute.",
                limit_type="rate",
                limit=limits.rpm,
                retry_after=max(1, 60 - int(time.time()) % 60),
            )

        # Quotas — the absolute cap wins over the daily one
        if total_count > limits.total:
            return LimitVerdict(
                allowed=False,
                detail=f"Usage exhausted: the limit of {limits.total} total runs has been reached.",
                limit_type="total",
                limit=limits.total,
            )
        if daily_count > limits.daily:
            resets_at = next_utc_midnight()
            return LimitVerdict(
                allowed=False,
                detail=f"Daily usage limit reached ({limits.daily} runs per day). Resets at midnight UTC.",
                limit_type="daily",
                limit=limits.daily,
                retry_after=max(1, int((resets_at - datetime.now(UTC)).total_seconds())),
                resets_at=resets_at,
            )
        return LimitVerdict(
            allowed=True,
            daily_limit=limits.daily,
            daily_remaining=max(0, limits.daily - daily_count),
            total_limit=limits.total,
            total_remaining=max(0, limits.total - total_count),
        )


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
        if verdict.daily_limit is not None:
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
        """429 with a machine-readable body the AgentOS UI can key a modal off."""
        body: dict = {
            "detail": verdict.detail,
            "error_code": "usage_limit_exceeded",
            "limit_type": verdict.limit_type,
            "limit": verdict.limit,
        }
        headers = {}
        if verdict.retry_after is not None:
            body["retry_after"] = verdict.retry_after
            headers["Retry-After"] = str(verdict.retry_after)
        if verdict.resets_at is not None:
            body["resets_at"] = verdict.resets_at.isoformat()
        return JSONResponse(status_code=429, content=body, headers=headers)


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
        event: dict = {
            "event": "error",
            "error": verdict.detail,
            "error_code": "usage_limit_exceeded",
            "limit_type": verdict.limit_type,
            "limit": verdict.limit,
        }
        if verdict.retry_after is not None:
            event["retry_after"] = verdict.retry_after
        if verdict.resets_at is not None:
            event["resets_at"] = verdict.resets_at.isoformat()
        return event
