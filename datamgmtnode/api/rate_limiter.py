import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
import aiohttp.web

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.

    Implements per-IP rate limiting with configurable requests per second
    and burst capacity.
    """

    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Rate at which tokens are replenished
            burst_size: Maximum tokens (requests) that can be accumulated
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        # Dict mapping IP -> (tokens, last_update_time)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (float(burst_size), time.monotonic())
        )

    def _get_client_ip(self, request: aiohttp.web.Request) -> str:
        """Extract client IP from request, considering proxies."""
        # Check for forwarded headers (reverse proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()

        # Fall back to direct connection IP
        peername = request.transport.get_extra_info('peername')
        if peername:
            return peername[0]

        return 'unknown'

    def is_allowed(self, request: aiohttp.web.Request) -> Tuple[bool, float]:
        """
        Check if request is allowed under rate limit.

        Returns:
            Tuple of (allowed: bool, retry_after: float seconds)
        """
        client_ip = self._get_client_ip(request)
        now = time.monotonic()

        tokens, last_update = self._buckets[client_ip]

        # Replenish tokens based on time elapsed
        time_passed = now - last_update
        tokens = min(self.burst_size, tokens + time_passed * self.requests_per_second)

        if tokens >= 1.0:
            # Allow request, consume one token
            self._buckets[client_ip] = (tokens - 1.0, now)
            return True, 0.0
        else:
            # Deny request, calculate retry time
            self._buckets[client_ip] = (tokens, now)
            retry_after = (1.0 - tokens) / self.requests_per_second
            return False, retry_after

    def cleanup_old_entries(self, max_age_seconds: float = 3600.0):
        """Remove entries that haven't been accessed recently."""
        now = time.monotonic()
        old_ips = [
            ip for ip, (_, last_update) in self._buckets.items()
            if now - last_update > max_age_seconds
        ]
        for ip in old_ips:
            del self._buckets[ip]

        if old_ips:
            logger.debug(f"Cleaned up {len(old_ips)} stale rate limit entries")


def create_rate_limit_middleware(rate_limiter: RateLimiter):
    """
    Create an aiohttp middleware that enforces rate limiting.

    Args:
        rate_limiter: RateLimiter instance to use

    Returns:
        aiohttp middleware function
    """
    @aiohttp.web.middleware
    async def rate_limit_middleware(request: aiohttp.web.Request, handler):
        # Skip rate limiting for health check endpoints
        if request.path in ('/health', '/healthz', '/ready'):
            return await handler(request)

        allowed, retry_after = rate_limiter.is_allowed(request)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {rate_limiter._get_client_ip(request)} "
                f"on {request.path}"
            )
            return aiohttp.web.json_response(
                {
                    'error': 'Rate limit exceeded',
                    'retry_after': round(retry_after, 2)
                },
                status=429,
                headers={'Retry-After': str(int(retry_after) + 1)}
            )

        return await handler(request)

    return rate_limit_middleware


# Default rate limiters for different API types
def create_internal_rate_limiter() -> RateLimiter:
    """Create rate limiter for internal API (higher limits)."""
    return RateLimiter(requests_per_second=50.0, burst_size=100)


def create_external_rate_limiter() -> RateLimiter:
    """Create rate limiter for external API (stricter limits)."""
    return RateLimiter(requests_per_second=10.0, burst_size=20)
