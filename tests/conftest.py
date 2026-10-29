import pytest

from app.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Start every test with empty rate-limit counters"""
    limiter.reset()
    yield
