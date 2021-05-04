"""Some utilities."""

import functools
import inspect
import typing as t

from infer_parser import Parser


def collect_annotation(param: inspect.Parameter) -> t.Any:
    """Return param.annotation.

    Converts *args into tuple and **kwargs into dict.
    Assumes param is annotated.
    """
    assert param.annotation != param.empty
    hint: t.Any = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        hint = t.Tuple[hint, ...]
    elif param.kind == param.VAR_KEYWORD:
        hint = t.Dict[str, hint]
    return hint


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
