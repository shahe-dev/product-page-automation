"""
Rate limiting middleware for PDP Automation v.3

Implements sliding window rate limiting with:
- Per-IP limits for unauthenticated requests
- Per-user limits for authenticated requests
- Configurable limits per endpoint pattern
- Standard rate limit headers
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
import asyncio
import logging

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Only trust X-Forwarded-For from known reverse proxy IPs.
# Add your load balancer / Cloud Run / nginx IPs here.
TRUSTED_PROXY_IPS = frozenset(
    getattr(settings, "TRUSTED_PROXY_IPS", "127.0.0.1,::1,10.0.0.0/8").split(",")
)


class RateLimitStore:
    """
    In-memory rate limit store with sliding window.

    For production with multiple workers, use Redis instead.
    """

    def __init__(self):
        # {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a key is rate limited.

        Args:
            key: Rate limit key (IP or user ID)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_limited, remaining, reset_time)
        """
        async with self._lock:
            now = time.time()
            window_start = now - window_seconds

            # Clean old entries
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]

            current_count = len(self._requests[key])

            if current_count >= limit:
                # Calculate reset time
                oldest = min(self._requests[key]) if self._requests[key] else now
                reset_time = int(oldest + window_seconds - now)
                return True, 0, max(reset_time, 1)

            # Add current request
            self._requests[key].append(now)
            remaining = limit - current_count - 1
            reset_time = window_seconds

            return False, remaining, reset_time

    async def cleanup(self, max_age_seconds: int = 300):
        """Remove stale entries older than max_age."""
        async with self._lock:
            now = time.time()
            cutoff = now - max_age_seconds

            keys_to_remove = []
            for key, timestamps in self._requests.items():
                self._requests[key] = [ts for ts in timestamps if ts > cutoff]
                if not self._requests[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._requests[key]


# Global rate limit store
rate_limit_store = RateLimitStore()


# Rate limit configurations by endpoint pattern
RATE_LIMITS = {
    # Auth endpoints - tighter limits (brute-force protection)
    "/api/v1/auth/google": (10, 60),      # 10 attempts per minute
    "/api/v1/auth/refresh": (20, 60),     # 20 refreshes per minute
    "/api/v1/auth/login": (10, 60),       # 10 login URL requests per minute

    # Read endpoints - high limits (all users, frequent access)
    "/api/v1/prompts": (200, 60),         # 200 prompt list requests per minute

    # Upload endpoints - moderate limits
    "/api/v1/upload": (20, 60),           # 20 uploads per minute

    # Content generation - expensive operations
    "/api/v1/content/generate": (10, 60),  # 10 generations per minute
    "/api/v1/content/regenerate": (20, 60), # 20 regenerations per minute

    # QA comparison - expensive
    "/api/v1/qa/compare": (20, 60),       # 20 comparisons per minute

    # Default for all other endpoints
    "default": (100, 60),
}


def get_rate_limit_for_path(path: str) -> Tuple[str, int, int]:
    """
    Get rate limit configuration for a path.

    Args:
        path: Request path

    Returns:
        Tuple of (matched_pattern, limit, window_seconds)
    """
    # Check exact matches first
    if path in RATE_LIMITS:
        limit, window = RATE_LIMITS[path]
        return path, limit, window

    # Check prefix matches
    for pattern, limits in RATE_LIMITS.items():
        if pattern != "default" and path.startswith(pattern):
            return pattern, limits[0], limits[1]

    limit, window = RATE_LIMITS["default"]
    return "default", limit, window


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from request.

    Uses user ID for authenticated requests, IP for anonymous.

    Args:
        request: FastAPI request

    Returns:
        Rate limit key string
    """
    # Check for authenticated user in request state
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address -- only trust X-Forwarded-For from known proxies
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded and client_ip in TRUSTED_PROXY_IPS:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = client_ip

    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Applies sliding window rate limits and returns standard headers:
    - X-RateLimit-Limit: Maximum requests allowed
    - X-RateLimit-Remaining: Requests remaining in window
    - X-RateLimit-Reset: Seconds until window resets
    - Retry-After: Seconds to wait (on 429 response)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Skip CORS preflight requests -- they should not count against limits
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get rate limit configuration (pattern used to scope counters)
        pattern, limit, window = get_rate_limit_for_path(request.url.path)

        # Get rate limit key scoped to endpoint pattern
        raw_key = get_rate_limit_key(request)
        key = f"{raw_key}:{pattern}"

        # Check rate limit
        is_limited, remaining, reset_time = await rate_limit_store.is_rate_limited(
            key, limit, window
        )

        if is_limited:
            logger.warning(
                f"Rate limit exceeded: {key} on {request.url.path}",
                extra={"key": key, "path": request.url.path}
            )
            # Return JSONResponse instead of raising HTTPException.
            # This keeps the response in the normal middleware flow,
            # allowing CORSMiddleware to add CORS headers.
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": {
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please wait before retrying.",
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time),
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response


async def cleanup_rate_limits():
    """Background task to clean up stale rate limit entries."""
    while True:
        await asyncio.sleep(60)  # Run every minute
        await rate_limit_store.cleanup()
