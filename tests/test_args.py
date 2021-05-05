"""Test args.py"""

import pytest

from climux.args import opt, InvalidFlag


def test_opt_invalid_flag() -> None:
    """opt should raise InvalidFlag if flag doesn't start with '-'."""
    with pytest.raises(InvalidFlag) as exc_info:
        opt("not-valid")
    assert "not-valid" in exc_info.value.args[0]
