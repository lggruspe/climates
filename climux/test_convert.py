"""Test convert.py"""

from typing import Callable

import pytest

from .convert import CantConvert, convert


def test_convert_empty() -> None:
    """convert should work on functions that take no parameters.

    It should ignore inputs that aren't parameters.
    """
    def func() -> None:
        """Does nothing."""

    assert convert(func, {}) == ((), {})
    assert convert(func, {"ignore": "this"}) == ((), {})


def test_convert() -> None:
    """convert should map inputs to args and kwargs.

    Missing arguments should cause a KeyError.
    """
    def func(a: int, /, b: int, *c: int, d: int, **e: int) -> None:  # pylint: disable=C0103,W0613; # noqa: E501
        """Does nothing."""

    with pytest.raises(KeyError) as exc_info:
        convert(func, {"a": ["1"]})
    assert "b" in exc_info.value.args

    result = convert(func, dict(
        a=["1"],
        b=["2"],
        c=["3", "4"],
        d=["5"],
        e=["6", "7", "8", "9"],
    ))
    assert result == (
        (1, 2, 3, 4),
        {"d": 5, "6": 7, "8": 9},
    )


def test_convert_without_annotation() -> None:
    """convert should work even with unannotated parameters.

    It should treat input as str.
    """
    def func(arg):  # type: ignore
        """Does nothing."""
        return arg

    assert convert(func, dict(arg=["1", "2", "3"])) == (
        ("1 2 3",),
        {}
    )
    assert func(True)  # type: ignore


def test_convert_unsupported_type() -> None:
    """convert should raise an error if type hint is unsupported."""
    def func(arg: Callable[..., int]) -> None:  # pylint: disable=unused-argument; # noqa: E501
        """Does nothing."""

    result = convert(func, {"arg": ""})
    assert isinstance(result, CantConvert)
    assert "unsupported type" in result.args[0]
    assert "Callable[..., int]" in result.args[0]


def test_convert_invalid_value() -> None:
    """convert should raise an error if string can't be parsed."""
    def func(arg: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    result = convert(func, {"arg": ["5.0"]})
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "arg" in result.args[0]
    assert "5.0" in result.args[0]
