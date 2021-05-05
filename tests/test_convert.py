# pylint: disable=unsubscriptable-object
"""Test convert.py"""

import sys
import typing as t

from infer_parser import Parser
import pytest

from climux import Command
from climux.args import opt
from climux.convert import CantConvert, convert
from climux.utils import make_simple_parser


def get_parsers(command: Command) -> t.Dict[str, Parser]:
    """Get command argument parsers."""
    return {name: arg.parser  # type: ignore
            for name, arg in command.custom.items()}


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
    def func(a: int, b: int, *c: int, d: int, **e: int) -> None:  # pylint: disable=C0103,W0613; # noqa: E501
        """Does nothing."""

    command = Command(func)
    parsers = get_parsers(command)

    with pytest.raises(KeyError) as exc_info:
        convert(func, {"a": ["1"]}, parsers)
    assert "b" in exc_info.value.args

    result = convert(func, dict(
        a=["1"],
        b=["2"],
        c=["3", "4"],
        d=["5"],
        e=["6", "7", "8", "9"],
    ), parsers)
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

    command = Command(func)
    parsers = get_parsers(command)

    assert convert(func, dict(arg=["1.0"]), parsers) == (
        ("1.0",),
        {}
    )
    assert func(True)  # type: ignore


def test_convert_invalid_value() -> None:
    """convert should raise an error if string can't be parsed."""
    def func(arg: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"arg": ["5.0"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "arg" in result.args[0]
    assert "5.0" in result.args[0]
    assert "expected int" in result.args[0]


def test_convert_invalid_args() -> None:
    """convert should print proper error message for invalid *args."""
    def func(*args: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"args": ["5.0"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "args" in result.args[0]
    assert "5.0" in result.args[0]
    assert "expected typing.Tuple[int, ...]" in result.args[0]


@pytest.mark.skipif(sys.version_info < (3, 9), reason="No generic aliases")
def test_convert_invalid_generic_alias_args() -> None:
    """convert should print proper error message for invalid generic alias
    values."""
    def func(arg: tuple[str, int]):  # type: ignore
        """Does nothing."""
        return arg

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"arg": []}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "arg" in result.args[0]
    assert "expected tuple[str, int]" in result.args[0]

    result = convert(func, {"arg": ["a", "b"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "arg" in result.args[0]
    assert "a b" in result.args[0]
    assert "expected tuple[str, int]" in result.args[0]

    assert func(("", 0))


def test_convert_invalid_kwargs() -> None:
    """convert should print proper error message for invalid **kwargs."""
    def func(**kwargs: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"kwargs": ["a", "5.0"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "kwargs" in result.args[0]
    assert "a 5.0" in result.args[0]
    assert "expected typing.Dict[str, int]" in result.args[0]


def test_convert_none_with_default() -> None:
    """convert should use default value if value in inputs is None."""
    def func(arg: int = 9001) -> int:
        return arg

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"arg": None}, parsers)
    assert not isinstance(result, CantConvert)

    args, kwargs = result
    assert func(*args, **kwargs) == 9001


def test_convert_none_with_missing_default() -> None:
    """convert should raise error if input is None and there's no default."""
    def func(arg: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    command = Command(func)
    parsers = get_parsers(command)

    result = convert(func, {"arg": None}, parsers)
    assert isinstance(result, CantConvert)
    assert "missing" in result.args[0]
    assert "arg" in result.args[0]


def test_convert_with_custom_parsers() -> None:
    """convert should use custom parser instead of inferring one."""
    def func(arg: str) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    result = convert(func, {"arg": ["foo"]}, custom_parsers=dict(
        arg=make_simple_parser(lambda x: x[::-1])
    ))
    assert result == (("oof",), {})


def test_convert_with_failing_custom_parsers() -> None:
    """convert should fail if custom parser fails."""
    def func(arg: int) -> None:  # pylint: disable=unused-argument
        """Does nothing."""

    parser = make_simple_parser(int)
    command = Command(func, custom=dict(arg=opt(parser=parser)))
    parsers = get_parsers(command)

    result = convert(func, {"arg": ["foo"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "arg" in result.args[0]
    assert "foo" in result.args[0]
    assert "expected int" in result.args[0]


def test_convert_with_failing_custom_parsers_without_type_hints() -> None:
    """convert should fail gracefully if custom parser fails."""
    def func(arg):  # type: ignore
        """Does nothing."""
        return arg

    def parser(string: str) -> None:
        """Parser that always fails."""
        raise NotImplementedError()

    command = Command(func, custom=dict(arg=opt(
        parser=make_simple_parser(parser))))
    parsers = get_parsers(command)

    result = convert(func, {"arg": ["foo"]}, parsers)
    assert isinstance(result, CantConvert)
    assert "invalid value" in result.args[0]
    assert "foo" in result.args[0]
    assert "arg" in result.args[0]

    assert func(True)  # type: ignore
