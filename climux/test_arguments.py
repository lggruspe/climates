"""Test arguments.py."""

import pytest

from .arguments import Opt
from .errors import InvalidFlag


def test_opt_invalid_flag() -> None:
    """Opt should raise InvalidFlag if flag doesn't start with '-'."""
    with pytest.raises(InvalidFlag) as exc_info:
        Opt("not-valid")
    assert "not-valid" in exc_info.value.args[0]
