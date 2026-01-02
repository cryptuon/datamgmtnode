import pytest
import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from api.rate_limiter import (
    RateLimiter,
    create_rate_limit_middleware,
    create_internal_rate_limiter,
    create_external_rate_limiter
)


class MockRequest:
    """Mock aiohttp request for testing."""

    def __init__(self, ip='127.0.0.1', path='/test', headers=None):
        self.path = path
        self.headers = headers or {}
        self._transport = MagicMock()
        self._transport.get_extra_info.return_value = (ip, 12345)

    @property
    def transport(self):
        return self._transport


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_init_defaults(self):
        limiter = RateLimiter()
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 20

    def test_init_custom_values(self):
        limiter = RateLimiter(requests_per_second=5.0, burst_size=10)
        assert limiter.requests_per_second == 5.0
        assert limiter.burst_size == 10

    def test_is_allowed_first_request(self):
        limiter = RateLimiter(burst_size=5)
        request = MockRequest()
        allowed, retry_after = limiter.is_allowed(request)
        assert allowed is True
        assert retry_after == 0.0

    def test_is_allowed_within_burst(self):
        limiter = RateLimiter(burst_size=5)
        request = MockRequest()

        # Should allow up to burst_size requests
        for i in range(5):
            allowed, _ = limiter.is_allowed(request)
            assert allowed is True, f"Request {i+1} should be allowed"

    def test_is_allowed_exceeds_burst(self):
        limiter = RateLimiter(burst_size=2, requests_per_second=1.0)
        request = MockRequest()

        # Exhaust the burst
        limiter.is_allowed(request)
        limiter.is_allowed(request)

        # Next request should be denied
        allowed, retry_after = limiter.is_allowed(request)
        assert allowed is False
        assert retry_after > 0

    def test_is_allowed_replenishes_over_time(self):
        limiter = RateLimiter(burst_size=2, requests_per_second=20.0)  # Rate for testing
        request = MockRequest(ip='10.0.0.1')  # Explicit IP

        # Use all tokens
        allowed1, _ = limiter.is_allowed(request)
        assert allowed1 is True
        allowed2, _ = limiter.is_allowed(request)
        assert allowed2 is True

        # Should be denied immediately - no tokens left
        allowed3, retry_after = limiter.is_allowed(request)
        assert allowed3 is False
        assert retry_after > 0

        # Wait for token replenishment (100ms = 2 tokens at 20/sec)
        time.sleep(0.12)

        # Should be allowed again
        allowed4, _ = limiter.is_allowed(request)
        assert allowed4 is True

    def test_get_client_ip_direct(self):
        limiter = RateLimiter()
        request = MockRequest(ip='192.168.1.100')
        ip = limiter._get_client_ip(request)
        assert ip == '192.168.1.100'

    def test_get_client_ip_forwarded(self):
        limiter = RateLimiter()
        request = MockRequest(
            ip='127.0.0.1',
            headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'}
        )
        ip = limiter._get_client_ip(request)
        assert ip == '10.0.0.1'

    def test_get_client_ip_real_ip(self):
        limiter = RateLimiter()
        request = MockRequest(
            ip='127.0.0.1',
            headers={'X-Real-IP': '10.0.0.1'}
        )
        ip = limiter._get_client_ip(request)
        assert ip == '10.0.0.1'

    def test_different_ips_have_separate_limits(self):
        limiter = RateLimiter(burst_size=2, requests_per_second=0.1)  # Low rate to ensure no replenishment

        request1 = MockRequest(ip='192.168.1.1')
        request2 = MockRequest(ip='192.168.1.2')

        # First IP uses its tokens
        allowed1, _ = limiter.is_allowed(request1)
        assert allowed1 is True
        allowed1, _ = limiter.is_allowed(request1)
        assert allowed1 is True

        # First IP is now limited
        allowed1, _ = limiter.is_allowed(request1)
        assert allowed1 is False

        # Second IP still has its tokens
        allowed2, _ = limiter.is_allowed(request2)
        assert allowed2 is True

    def test_cleanup_old_entries(self):
        limiter = RateLimiter()
        request = MockRequest(ip='192.168.1.1')

        # Make a request to create an entry
        limiter.is_allowed(request)
        assert '192.168.1.1' in limiter._buckets

        # Cleanup with 0 max age should remove all entries
        limiter.cleanup_old_entries(max_age_seconds=0)
        assert '192.168.1.1' not in limiter._buckets


class TestRateLimitMiddleware:
    """Tests for rate limit middleware factory."""

    @pytest.mark.asyncio
    async def test_middleware_allows_request(self):
        limiter = RateLimiter(burst_size=10)
        middleware = create_rate_limit_middleware(limiter)
        request = MockRequest()

        handler_called = False

        async def handler(req):
            nonlocal handler_called
            handler_called = True
            return MagicMock(status=200)

        response = await middleware(request, handler)
        assert handler_called is True

    @pytest.mark.asyncio
    async def test_middleware_blocks_request(self):
        limiter = RateLimiter(burst_size=0)  # No tokens available
        middleware = create_rate_limit_middleware(limiter)
        request = MockRequest()

        async def handler(req):
            return MagicMock(status=200)

        response = await middleware(request, handler)
        assert response.status == 429

    @pytest.mark.asyncio
    async def test_middleware_skips_health_endpoint(self):
        limiter = RateLimiter(burst_size=0)  # Would block normal requests
        middleware = create_rate_limit_middleware(limiter)
        request = MockRequest(path='/health')

        handler_called = False

        async def handler(req):
            nonlocal handler_called
            handler_called = True
            return MagicMock(status=200)

        await middleware(request, handler)
        assert handler_called is True


class TestFactoryFunctions:
    """Tests for rate limiter factory functions."""

    def test_create_internal_rate_limiter(self):
        limiter = create_internal_rate_limiter()
        assert limiter.requests_per_second == 50.0
        assert limiter.burst_size == 100

    def test_create_external_rate_limiter(self):
        limiter = create_external_rate_limiter()
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 20
