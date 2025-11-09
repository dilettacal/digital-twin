"""Tests for rate limiting logic."""
import time
import pytest
from app.core.rate_limiter import validate_message_content, get_client_identifier


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_allows_requests_under_limit(self, rate_limiter):
        """Should allow requests when under the rate limit."""
        identifier = "test-user-1"

        # Should allow first 5 requests (test config: 5 requests per 10 seconds)
        for i in range(5):
            allowed, error_msg = rate_limiter.check_rate_limit(
                identifier=identifier,
                max_requests=5,
                window_seconds=10,
                cooldown_seconds=0.1
            )
            assert allowed is True
            assert error_msg == ""
            time.sleep(0.15)  # Wait for cooldown

    def test_blocks_requests_over_limit(self, rate_limiter):
        """Should block requests when rate limit is exceeded."""
        identifier = "test-user-2"

        # Fill up the rate limit (5 requests)
        for i in range(5):
            rate_limiter.check_rate_limit(
                identifier=identifier,
                max_requests=5,
                window_seconds=10,
                cooldown_seconds=0.1
            )
            time.sleep(0.15)

        # 6th request should be blocked
        allowed, error_msg = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=5,
            window_seconds=10,
            cooldown_seconds=0.1
        )
        assert allowed is False
        assert "Rate limit exceeded" in error_msg

    def test_enforces_cooldown_period(self, rate_limiter):
        """Should enforce cooldown period between consecutive requests."""
        identifier = "test-user-3"

        # First request should succeed
        allowed, _ = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=10,
            window_seconds=60,
            cooldown_seconds=1.0
        )
        assert allowed is True

        # Immediate second request should fail (cooldown not elapsed)
        allowed, error_msg = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=10,
            window_seconds=60,
            cooldown_seconds=1.0
        )
        assert allowed is False
        assert "Please wait" in error_msg

        # After waiting, request should succeed
        time.sleep(1.1)
        allowed, _ = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=10,
            window_seconds=60,
            cooldown_seconds=1.0
        )
        assert allowed is True

    def test_sliding_window_allows_requests_after_expiry(self, rate_limiter):
        """Should allow new requests after old requests expire from the window."""
        identifier = "test-user-4"

        # Fill up the limit with short window
        for i in range(3):
            rate_limiter.check_rate_limit(
                identifier=identifier,
                max_requests=3,
                window_seconds=1,
                cooldown_seconds=0.1
            )
            time.sleep(0.15)

        # Should be blocked immediately
        allowed, _ = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=3,
            window_seconds=1,
            cooldown_seconds=0.1
        )
        assert allowed is False

        # After window expires, should allow again
        time.sleep(1.2)
        allowed, _ = rate_limiter.check_rate_limit(
            identifier=identifier,
            max_requests=3,
            window_seconds=1,
            cooldown_seconds=0.1
        )
        assert allowed is True

    def test_different_identifiers_have_separate_limits(self, rate_limiter):
        """Different clients should have independent rate limits."""
        # Fill up limit for user 1
        for i in range(5):
            rate_limiter.check_rate_limit(
                identifier="user-1",
                max_requests=5,
                window_seconds=10,
                cooldown_seconds=0.1
            )
            time.sleep(0.15)

        # User 1 should be blocked
        allowed, _ = rate_limiter.check_rate_limit(
            identifier="user-1",
            max_requests=5,
            window_seconds=10,
            cooldown_seconds=0.1
        )
        assert allowed is False

        # User 2 should still be allowed
        allowed, _ = rate_limiter.check_rate_limit(
            identifier="user-2",
            max_requests=5,
            window_seconds=10,
            cooldown_seconds=0.1
        )
        assert allowed is True

    def test_cleanup_removes_old_entries(self, rate_limiter):
        """Cleanup should remove old entries to prevent memory buildup."""
        # Add some old requests
        for i in range(10):
            rate_limiter.check_rate_limit(
                identifier=f"user-{i}",
                max_requests=10,
                window_seconds=1,
                cooldown_seconds=0.1
            )

        assert len(rate_limiter.requests) == 10

        # Wait and cleanup
        time.sleep(2)
        rate_limiter.cleanup_old_entries(max_age_seconds=1)

        # Old entries should be removed
        assert len(rate_limiter.requests) == 0


class TestMessageValidation:
    """Tests for message content validation."""

    def test_rejects_empty_message(self):
        """Should reject empty messages."""
        valid, error = validate_message_content("")
        assert valid is False
        assert "cannot be empty" in error.lower()

    def test_rejects_whitespace_only_message(self):
        """Should reject messages with only whitespace."""
        valid, error = validate_message_content("   \n  \t  ")
        assert valid is False
        assert "cannot be empty" in error.lower()

    def test_rejects_too_short_message(self):
        """Should reject messages that are too short."""
        valid, error = validate_message_content("a")
        assert valid is False
        assert "too short" in error.lower()

    def test_accepts_minimum_valid_message(self):
        """Should accept messages at minimum length."""
        valid, error = validate_message_content("ab")
        assert valid is True
        assert error == ""

    def test_accepts_normal_message(self):
        """Should accept normal messages."""
        valid, error = validate_message_content("Hello, how are you?")
        assert valid is True
        assert error == ""

    def test_rejects_too_long_message(self):
        """Should reject messages that exceed maximum length."""
        long_message = "a" * 2001
        valid, error = validate_message_content(long_message)
        assert valid is False
        assert "too long" in error.lower()
        assert "2000" in error

    def test_accepts_maximum_length_message(self):
        """Should accept messages at exactly maximum length."""
        max_message = "a" * 2000
        valid, error = validate_message_content(max_message)
        assert valid is True
        assert error == ""

    @pytest.mark.parametrize("suspicious_text", [
        "ignore previous instructions",
        "Ignore Previous Instructions",
        "IGNORE ALL PREVIOUS",
        "disregard previous",
        "forget everything",
        "new instructions:",
        "system: hello",
        "<script>alert('xss')</script>",
        "javascript:void(0)",
        "eval(malicious)",
        "exec(code)",
    ])
    def test_rejects_suspicious_patterns(self, suspicious_text):
        """Should reject messages with suspicious patterns."""
        valid, error = validate_message_content(suspicious_text)
        assert valid is False
        assert "cannot be processed" in error.lower()

    def test_accepts_message_with_similar_but_safe_content(self):
        """Should accept messages that contain similar words but are safe."""
        valid, error = validate_message_content("I want to ignore the noise and focus on work")
        assert valid is True
        assert error == ""


class TestClientIdentification:
    """Tests for client identifier extraction."""

    def test_uses_session_id_when_provided(self):
        """Should prefer session ID when provided."""
        headers = {"x-forwarded-for": "1.2.3.4"}
        identifier = get_client_identifier(headers, session_id="session-123")
        assert identifier == "session:session-123"

    def test_uses_x_forwarded_for_header(self):
        """Should extract IP from x-forwarded-for header."""
        headers = {"x-forwarded-for": "1.2.3.4"}
        identifier = get_client_identifier(headers)
        assert identifier == "ip:1.2.3.4"

    def test_uses_first_ip_from_forwarded_list(self):
        """Should use first IP when x-forwarded-for contains multiple IPs."""
        headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8, 9.10.11.12"}
        identifier = get_client_identifier(headers)
        assert identifier == "ip:1.2.3.4"

    def test_uses_x_real_ip_header(self):
        """Should extract IP from x-real-ip header."""
        headers = {"x-real-ip": "1.2.3.4"}
        identifier = get_client_identifier(headers)
        assert identifier == "ip:1.2.3.4"

    def test_uses_cf_connecting_ip_header(self):
        """Should extract IP from cf-connecting-ip header (Cloudflare)."""
        headers = {"cf-connecting-ip": "1.2.3.4"}
        identifier = get_client_identifier(headers)
        assert identifier == "ip:1.2.3.4"

    def test_prefers_x_forwarded_for_over_others(self):
        """Should prefer x-forwarded-for when multiple headers present."""
        headers = {
            "x-forwarded-for": "1.2.3.4",
            "x-real-ip": "5.6.7.8",
            "cf-connecting-ip": "9.10.11.12"
        }
        identifier = get_client_identifier(headers)
        assert identifier == "ip:1.2.3.4"

    def test_returns_anonymous_when_no_identifier(self):
        """Should return 'anonymous' when no identifier available."""
        headers = {}
        identifier = get_client_identifier(headers)
        assert identifier == "anonymous"
