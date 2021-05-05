"""Test utils.py."""

import pytest

from climux.utils import make_simple_parser


def test_make_simple_parser() -> None:
    """make_simple_parser should convert str function to function on tokens."""
    def reverse(string: str) -> str:
        """Reverse string."""
        return string[::-1]

    assert reverse("foo") == "oof"

    parse = make_simple_parser(reverse)
    assert parse(["foo"]) == "oof"

    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse(["foo", "bar"])
