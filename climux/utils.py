"""Some utilities."""

import functools
import typing as t

from infer_parser import Parser


def make_simple_parser(func: t.Callable[[str], t.Any]) -> Parser:
    """Wrap custom parser so that it raises ValueError on error."""
    @functools.wraps(func)
    def wrapper(tokens: t.Sequence[str]) -> t.Any:
        error = ValueError(f"cannot parse {tokens} using {func}")
        if len(tokens) != 1:
            raise error
        try:
            return func(tokens[0])
        except Exception as exc:  # pylint: disable=broad-except
            raise error from exc
    return Parser(func, wrapper, 1)


__all__ = ["make_simple_parser"]
