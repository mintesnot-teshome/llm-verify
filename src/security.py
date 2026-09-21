"""Authentication, rate limiting, and outbound URL protections."""

import asyncio
import ipaddress
import secrets
import socket
import time
from collections import defaultdict, deque
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import Settings, get_settings

_OFFICIAL_API_HOSTS = {"api.openai.com", "api.anthropic.com"}
_bearer = HTTPBearer(auto_error=False)


class _InMemoryRateLimiter:
    """Small per-process sliding-window limiter for API abuse protection."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, identity: str, limit: int) -> None:
        """Reject an identity after it exceeds the configured minute limit."""
        if limit <= 0:
            return

        now = time.monotonic()
        cutoff = now - 60.0
        async with self._lock:
            timestamps = self._requests[identity]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= limit:
                retry_after = max(1, int(60 - (now - timestamps[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="API request limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )
            timestamps.append(now)


_rate_limiter = _InMemoryRateLimiter()


async def require_api_access(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Require the configured bearer key and enforce a basic request quota."""
    client_host = request.client.host if request.client else "unknown"

    if settings.allow_unauthenticated:
        identity = f"anonymous:{client_host}"
    else:
        if not settings.api_access_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API_ACCESS_KEY is not configured",
            )
        if (
            credentials is None
            or credentials.scheme.lower() != "bearer"
            or not secrets.compare_digest(credentials.credentials, settings.api_access_key)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API access key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # There is one configured service key, so the client address is enough
        # to partition limits without retaining the bearer secret in memory.
        identity = f"authenticated:{client_host}"

    await _rate_limiter.check(identity, settings.api_requests_per_minute)


def validate_outbound_api_url(url: str, settings: Settings) -> None:
    """Validate a configured API base URL against the operator's host allowlist."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("API base URL is malformed") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("API base URL must use http or https")
    if not parsed.hostname:
        raise ValueError("API base URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("API base URL must not contain embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("API base URL must not contain a query string or fragment")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("API base URL contains an invalid port")

    hostname = parsed.hostname.lower().rstrip(".")
    explicit_hosts = set(settings.outbound_api_hosts)
    suspect_host = _hostname_from_url(settings.suspect_api_base_url)
    if suspect_host:
        explicit_hosts.add(suspect_host)

    allowed_hosts = _OFFICIAL_API_HOSTS | explicit_hosts
    if hostname not in allowed_hosts:
        raise ValueError(
            f"API host {hostname!r} is not trusted; add it to ALLOWED_API_HOSTS"
        )

    # Explicit entries are an operator-controlled escape hatch for LAN-hosted
    # models. Official public endpoints must always resolve to public addresses.
    if hostname not in explicit_hosts:
        _require_public_dns(hostname, port or (443 if parsed.scheme == "https" else 80))


def _hostname_from_url(url: str) -> str | None:
    if not url:
        return None
    try:
        hostname = urlsplit(url).hostname
    except ValueError:
        return None
    return hostname.lower().rstrip(".") if hostname else None


def _require_public_dns(hostname: str, port: int) -> None:
    """Reject official endpoints if DNS unexpectedly resolves to a non-public IP."""
    try:
        addresses = {
            entry[4][0]
            for entry in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise ValueError(f"API host {hostname!r} could not be resolved") from exc

    if not addresses:
        raise ValueError(f"API host {hostname!r} did not resolve to an address")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(f"API host {hostname!r} resolves to a non-public address")
