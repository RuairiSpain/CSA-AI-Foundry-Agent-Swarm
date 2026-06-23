"""Structured observability: correlation ID propagation and JSON-line logging.

Usage
-----
At the entry point (WebSocket handler, CLI, test) call ``set_correlation_id``
with a new UUID before dispatching work. Every ``StructuredLogger`` call and
every ``AuditEvent`` will then carry that ID, making it trivial to reconstruct
a full execution trace with a single grep:

    grep '"correlation_id": "abc-123"' app.log

Example::

    from safe_core.tracing import set_correlation_id, StructuredLogger
    import uuid

    cid = str(uuid.uuid4())
    set_correlation_id(cid)
    log = StructuredLogger(route_name="my-route")
    log.agent_invoked("mapper_1")
"""

from __future__ import annotations

import json
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

_CORRELATION_ID: ContextVar[str] = ContextVar("correlation_id", default="")


def set_correlation_id(cid: str) -> None:
    """Set the correlation ID for the current async context."""
    _CORRELATION_ID.set(cid)


def get_correlation_id() -> str:
    """Return the active correlation ID, or an empty string if none is set."""
    return _CORRELATION_ID.get()


def new_correlation_id() -> str:
    """Generate a fresh UUID, set it as the active correlation ID, and return it."""
    cid = str(uuid.uuid4())
    _CORRELATION_ID.set(cid)
    return cid


def correlation_headers() -> dict[str, str]:
    """Return an ``x-correlation-id`` header dict for outbound HTTP calls.

    Returns an empty dict when no correlation ID is active so callers can
    safely spread it into their headers unconditionally::

        headers = {**_base_headers(), **correlation_headers()}
    """
    cid = get_correlation_id()
    return {"x-correlation-id": cid} if cid else {}


class StructuredLogger:
    """Emits JSON-line log entries to stderr with automatic correlation ID injection.

    Each line includes ``correlation_id``, ``route_name``, ``stage``,
    ``event``, ``elapsed_ms``, and ``timestamp`` so log aggregators can
    group, filter, and measure every agent hop from a single stream.
    """

    def __init__(self, route_name: str = "") -> None:
        self.route_name = route_name

    def _emit(self, event: str, stage: str = "", elapsed_ms: float = 0.0, **extra: Any) -> None:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": get_correlation_id(),
            "route_name": self.route_name,
            "stage": stage,
            "event": event,
            "elapsed_ms": elapsed_ms,
        }
        entry.update(extra)
        print(json.dumps(entry), file=sys.stderr, flush=True)

    def agent_invoked(self, stage: str, elapsed_ms: float = 0.0, **kw: Any) -> None:
        self._emit("agent_invoked", stage=stage, elapsed_ms=elapsed_ms, **kw)

    def agent_succeeded(self, stage: str, elapsed_ms: float = 0.0, **kw: Any) -> None:
        self._emit("agent_succeeded", stage=stage, elapsed_ms=elapsed_ms, **kw)

    def agent_failed(self, stage: str, error: str = "", elapsed_ms: float = 0.0, **kw: Any) -> None:
        self._emit("agent_failed", stage=stage, error=error, elapsed_ms=elapsed_ms, **kw)

    def route_started(self, **kw: Any) -> None:
        self._emit("route_started", **kw)

    def route_completed(self, elapsed_ms: float = 0.0, **kw: Any) -> None:
        self._emit("route_completed", elapsed_ms=elapsed_ms, **kw)
