"""Convert argparse parsed args to function args."""

import inspect
import shlex
import types
import typing as t

from infer_parser import Parser


Function = t.Callable[..., t.Any]
FunctionArgs = t.Tuple[t.Tuple[t.Any, ...], t.Dict[str, t.Any]]


class CantConvert(Exception):
    """Returned by convert function on failure."""


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


def get_type_name(param: inspect.Parameter) -> str:
    """Get type name.

    Also fixes type names of *args and **kwargs.
    """
    assert param.annotation != param.empty
    hint = collect_annotation(param)
    if hasattr(types, "GenericAlias") and \
            isinstance(hint, getattr(types, "GenericAlias")):
        return str(hint)
    return str(getattr(hint, "__name__", hint))


def convert_value(param: inspect.Parameter,
                  parser: Parser,
                  tokens: t.Optional[t.Sequence[str]] = None
                  ) -> t.Union[t.Any, CantConvert]:
    """Convert tokens to value.

    None tokens means to use the default value.
    """
    name = param.name
    if tokens is None:
        if param.default == param.empty:
            return CantConvert(f"missing parameter: {name}")
        return param.default
    try:
        return parser(tokens)
    except ValueError:
        message = "argument {}: invalid value: '{}'".format(
            name,
            " ".join(shlex.quote(token) for token in tokens),
        )
        if param.annotation != param.empty:
            type_name = get_type_name(param)
            message += f" (expected {type_name})"
            return CantConvert(message)
        return CantConvert(message)


def convert(func: Function,
            inputs: t.Mapping[str, t.Optional[t.Sequence[str]]],
            custom_parsers: t.Optional[t.Mapping[str, Parser]] = None,
            ) -> t.Union[FunctionArgs, CantConvert]:
    """Construct args and kwargs for function from argparse inputs.

    Assumes all function parameters are in inputs (raises KeyError) and in
    custom_parsers (also raises KeyError).
    If inputs[name] is None, apply default value.
    Raise error if there's no default.

    The custom parsers are defined by climux.Command.
    """
    if custom_parsers is None:
        custom_parsers = {}

    args = []
    kwargs = {}
    sig = inspect.signature(func)

    for name, param in sig.parameters.items():
        value = convert_value(param, custom_parsers[name], inputs[name])
        if isinstance(value, CantConvert):
            return value

        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            args.append(value)
        elif param.kind == param.KEYWORD_ONLY:
            kwargs[name] = value
        elif param.kind == param.VAR_POSITIONAL:
            args.extend(value)
        else:
            assert param.kind == param.VAR_KEYWORD
            kwargs.update(value)
    return (tuple(args), kwargs)


__all__ = ()
