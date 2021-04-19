# type: ignore
"""Pytest fixtures."""
import pytest
from climates import Climate


@pytest.fixture
def cli():
    """Create Climate object."""
    return Climate("test", description="Test CLI app")
