"""Convert argparse parsed args to function args."""

from functools import wraps
from inspect import Parameter, signature
import shlex
import types
from typing import (
    Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union
)

from .utils import collect_annotation


Function = Callable[..., Any]
FunctionArgs = Tuple[Tuple[Any, ...], Dict[str, Any]]
CustomParser = Callable[[Sequence[str]], Any]


class CantConvert(Exception):
    """Returned by convert function on failure."""


def get_type_name(param: Parameter) -> str:
    """Get type name.

    Also fixes type names of *args and **kwargs.
    """
    assert param.annotation != param.empty
    hint = collect_annotation(param)
    if hasattr(types, "GenericAlias") and \
            isinstance(hint, getattr(types, "GenericAlias")):
        return str(hint)
    return str(getattr(hint, "__name__", hint))


def wrap_custom_parser(parser: CustomParser) -> CustomParser:
    """Wrap custom parser so that it returns CantParse on error."""
    @wraps(parser)
    def wrapper(tokens: Sequence[str]) -> Any:
        assert len(tokens) == 1
        try:
            return parser(tokens[0])
        except Exception as exc:  # pylint: disable=broad-except
            raise ValueError(f"can parse {tokens} using {parser}") from exc
    return wrapper


def convert(func: Function,
            inputs: Mapping[str, Optional[Sequence[str]]],
            custom_parsers: Optional[Dict[str, CustomParser]] = None,
            ) -> Union[FunctionArgs, CantConvert]:
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
    sig = signature(func)

    for name, param in sig.parameters.items():
        parse = custom_parsers[name]
        input_ = inputs[name]
        if input_ is None:
            if param.default == param.empty:
                return CantConvert(f"missing parameter: {name}")
            value = param.default
        else:
            try:
                value = parse(input_)
            except ValueError:
                message = "argument {}: invalid value: '{}'".format(
                    name,
                    shlex.join(input_),
                )

                # unannotated params don't cause parse errors
                assert param.annotation != param.empty
                type_name = get_type_name(param)
                message += f" (expected {type_name})"
                return CantConvert(message)

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
