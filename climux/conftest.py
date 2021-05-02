"""Pytest fixtures."""
import pytest
from climux import Cli


@pytest.fixture
def cli() -> Cli:
    """Create Cli object."""
    return Cli("test", description="Test CLI app")
