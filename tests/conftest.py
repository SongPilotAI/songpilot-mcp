"""Configuration file for pytest."""

import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests (>5 seconds)")
    config.addinivalue_line("markers", "external: Tests requiring external services")
