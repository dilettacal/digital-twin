"""
Rate limiting implementation for API requests.
Provides per-request limits to prevent abuse and control costs.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.

    For production with multiple Lambda instances, consider using:
    - DynamoDB for persistent rate limiting
    - ElastiCache/Redis for distributed rate limiting
    """

    def __init__(self):
        # Store request timestamps per identifier (IP or session)
        # Format: {identifier: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list[float]] = defaultdict(list)

        # Store last request timestamp per identifier for cooldown
        # Format: {identifier: last_request_timestamp}
        self.last_request: Dict[str, float] = {}

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60,
        cooldown_seconds: float = 2.0
    ) -> Tuple[bool, str]:
        """
        Check if the request should be allowed.

        Args:
            identifier: Unique identifier (IP address, session ID, or user ID)
            max_requests: Maximum number of requests allowed in the time window
            window_seconds: Time window in seconds
            cooldown_seconds: Minimum seconds between consecutive requests

        Returns:
            (allowed, error_message): Tuple of boolean and error message (empty if allowed)
        """
        current_time = time.time()

        # Check cooldown (prevents rapid-fire requests)
        if identifier in self.last_request:
            time_since_last = current_time - self.last_request[identifier]
            if time_since_last < cooldown_seconds:
                remaining = cooldown_seconds - time_since_last
                return False, f"Please wait {remaining:.1f} seconds before sending another message."

        # Clean old requests outside the window
        cutoff_time = current_time - window_seconds
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff_time
        ]

        # Check if under rate limit
        if len(self.requests[identifier]) >= max_requests:
            # Calculate when the oldest request will expire
            oldest_request = min(self.requests[identifier])
            retry_after = int(oldest_request + window_seconds - current_time) + 1
            return False, f"Rate limit exceeded. Please try again in {retry_after} seconds."

        # Allow the request
        self.requests[identifier].append(current_time)
        self.last_request[identifier] = current_time
        return True, ""

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Clean up old entries to prevent memory buildup.
        Should be called periodically.
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        # Clean requests dict
        to_delete = []
        for identifier, timestamps in self.requests.items():
            # Remove old timestamps
            self.requests[identifier] = [ts for ts in timestamps if ts > cutoff_time]
            # Mark empty entries for deletion
            if not self.requests[identifier]:
                to_delete.append(identifier)

        for identifier in to_delete:
            del self.requests[identifier]
            if identifier in self.last_request:
                del self.last_request[identifier]


# Global rate limiter instance
# In production with Lambda, each instance has its own memory
# For true distributed rate limiting, use DynamoDB or Redis
rate_limiter = RateLimiter()


def validate_message_content(message: str) -> Tuple[bool, str]:
    """
    Validate message content for per-request limits.

    Args:
        message: The user's message

    Returns:
        (valid, error_message): Tuple of boolean and error message (empty if valid)
    """
    # Check if message is empty or only whitespace
    if not message or not message.strip():
        return False, "Message cannot be empty."

    # Check minimum length (prevent spam of very short messages)
    if len(message.strip()) < 2:
        return False, "Message is too short. Please provide a meaningful message."

    # Check maximum length (prevent token exhaustion)
    # Rough estimate: 1 token ≈ 4 characters
    # With 2000 max tokens output, we should limit input to reasonable size
    MAX_MESSAGE_LENGTH = 2000  # characters (roughly 500 tokens)
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message is too long. Maximum length is {MAX_MESSAGE_LENGTH} characters."

    # Check for suspicious patterns (basic security)
    suspicious_patterns = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard previous",
        "forget everything",
        "new instructions",
        "system: ",
        "system:",
        "<script",
        "javascript:",
        "eval(",
        "exec(",
    ]

    message_lower = message.lower()
    for pattern in suspicious_patterns:
        if pattern in message_lower:
            return False, "Your message contains content that cannot be processed. Please rephrase."

    return True, ""


def get_client_identifier(request_headers: dict, session_id: str = None) -> str:
    """
    Get a unique identifier for rate limiting.

    Priority:
    1. User ID (when authentication is implemented)
    2. Session ID (if provided)
    3. IP Address (from headers)

    Args:
        request_headers: Request headers dictionary
        session_id: Session ID if provided

    Returns:
        Unique identifier string
    """
    # For now, use session_id or IP address
    # When authentication is added, use user_id

    if session_id:
        return f"session:{session_id}"

    # Try to get real IP from headers (considering proxies/load balancers)
    # Check common headers in order of preference
    ip_headers = [
        "x-forwarded-for",  # CloudFront, API Gateway
        "x-real-ip",
        "cf-connecting-ip",  # Cloudflare
    ]

    for header in ip_headers:
        ip = request_headers.get(header)
        if ip:
            # x-forwarded-for can be a comma-separated list
            return f"ip:{ip.split(',')[0].strip()}"

    # Fallback to a generic identifier
    return "anonymous"
