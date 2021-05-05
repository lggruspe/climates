# pylint: disable=redefined-builtin
"""Opts and args."""

import argparse
import dataclasses
import enum
import inspect
import typing as t

from infer_parser import Parser, UnsupportedType, make_parser

from .convert import get_type_name


def get_parser(param: inspect.Parameter) -> Parser:
    """Get parser for type hint.

    Normalizes parameter types (i.e. *args to tuple and **kwargs to dict).
    Uses str for unannotated parameters.
    May raise UnsupportedType (from make_parser).
    """
    hint: t.Any = str
    if param.annotation != param.empty:
        hint = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        hint = t.Tuple[hint, ...]
    elif param.kind == param.VAR_KEYWORD:
        hint = t.Dict[str, hint]
    return make_parser(hint)


class ArgumentTag(enum.Enum):
    """Custom argument tags."""
    ARG = enum.auto()
    OPT = enum.auto()
    SWITCH = enum.auto()
    TOGGLE = enum.auto()


@dataclasses.dataclass
class Argument:
    """ArgumentParser argument."""
    tag: ArgumentTag
    args: t.Tuple[str, ...] = dataclasses.field(default_factory=tuple)
    kwargs: t.Dict[str, t.Any] = dataclasses.field(default_factory=dict)
    parser: t.Optional[Parser] = None

    def fill_in(self, param: inspect.Parameter) -> None:
        """Fill in unset members based on parameter signature."""
        if self.parser is None:
            try:
                self.parser = get_parser(param)
            except UnsupportedType as exc:
                assert param.annotation != param.empty
                raise TypeError(get_type_name(param)) from exc

        variadic = param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
        default: t.Optional[t.Sequence[t.Any]] = []
        nargs = self.parser.length
        required = False
        if not variadic:
            default = None
            required = param.default == param.empty

        if not self.args:
            self.args = (f"--{param.name}",)
        self.kwargs.setdefault("default", default)
        self.kwargs.setdefault("nargs", nargs)
        self.kwargs.setdefault("required", required)
        self.kwargs.setdefault("dest", param.name)

        if self.tag == ArgumentTag.ARG:
            self.args = (param.name,)
            self.kwargs.pop("dest", None)
            self.kwargs.pop("required", None)
        elif self.tag == ArgumentTag.OPT:
            pass
        else:
            self.kwargs.pop("nargs", None)
            const = ["0"]
            default = ["1"]
            if param.default is not True or self.tag == ArgumentTag.SWITCH:
                const = ["1"]
                default = ["0"]
            self.kwargs.update(dict(
                action="store_const",
                const=const,
                default=default,
                required=False,
            ))

    def add_to(self, parser: argparse.ArgumentParser) -> None:
        """Add argument to ArgumentParser."""
        parser.add_argument(*self.args, **self.kwargs)


def arg(*, parser: t.Optional[Parser] = None, **kwargs: t.Any) -> Argument:
    """Create positional argument."""
    return Argument(ArgumentTag.ARG, kwargs=kwargs, parser=parser)


def opt(*flags: str,
        parser: t.Optional[Parser] = None,
        **kwargs: t.Any) -> Argument:
    """Create named argument with parameters."""
    _check_flags(flags)
    return Argument(
        ArgumentTag.OPT,
        args=flags,
        kwargs=kwargs,
        parser=parser,
    )


def switch(*flags: str, **kwargs: t.Any) -> Argument:
    """Create switch flag (off by default)."""
    _check_flags(flags)
    return Argument(ArgumentTag.SWITCH, flags, kwargs)


def toggle(*flags: str, **kwargs: t.Any) -> Argument:
    """Create toggle flag (toggles default)."""
    _check_flags(flags)
    return Argument(ArgumentTag.TOGGLE, flags, kwargs)


class InvalidFlag(ValueError):
    """Invalid option flag.

    Flags should start with '-'.
    """


def _check_flags(flags: t.Sequence[str]) -> None:
    """Check if all flags are valid."""
    for flag in flags:
        if not flag.startswith("-"):
            raise InvalidFlag(flag)


__all__ = ["InvalidFlag", "arg", "opt", "switch", "toggle"]
