"""Convert argparse parsed args to function args."""

from functools import wraps
from inspect import Parameter, signature
from shlex import join
import types
from typing import (
    Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union
)

from infer_parser import CantInfer, CantParse, infer

from .utils import collect_annotation


Function = Callable[..., Any]
FunctionArgs = Tuple[Tuple[Any, ...], Dict[str, Any]]


class CantConvert(Exception):
    """Returned by convert function on failure."""


def get_parser(param: Parameter) -> Union[Function, CantInfer]:
    """Wrap infer to work with inspect.Parameters.

    Converts *args into a tuple and **kwargs into a dict.
    Uses str for unannotated parameters.
    """
    annotation: Any = str
    if param.annotation != param.empty:
        annotation = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        annotation = Tuple[annotation, ...]
    elif param.kind == param.VAR_KEYWORD:
        annotation = Dict[str, annotation]
    return infer(annotation)


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


def wrap_custom_parser(parser: Function) -> Function:
    """Wrap custom parser so that it returns CantParse on error."""
    @wraps(parser)
    def wrapper(string: str) -> Any:
        try:
            return parser(string)
        except Exception as exc:  # pylint: disable=broad-except
            return CantParse(exc)
    return wrapper


def convert(func: Function,
            inputs: Mapping[str, Optional[Sequence[str]]],
            custom_parsers: Optional[Dict[str, Function]] = None,
            ) -> Union[FunctionArgs, CantConvert]:
    """Construct args and kwargs for function from argparse inputs.

    Assumes all function parameters are in inputs (raises KeyError).
    If inputs[name] is None, apply default value.
    Raise error if there's no default.

    If a custom parser exists for a parameter, it is used instead of the
    inferred parser.
    """
    args = []
    kwargs = {}
    sig = signature(func)

    for name, param in sig.parameters.items():
        parse = get_parser(param)
        if custom_parsers and name in custom_parsers:
            parse = wrap_custom_parser(custom_parsers[name])

        if isinstance(parse, CantInfer):
            assert param.annotation != param.empty
            return CantConvert(f"unsupported type: {get_type_name(param)}")

        input_ = inputs[name]
        if input_ is None:
            if param.default == param.empty:
                return CantConvert(f"missing parameter: {name}")
            value = param.default
        else:
            string = join(input_)
            value = parse(string)
        if isinstance(value, CantParse):
            message = "argument {}: invalid value: '{}'".format(name, string)

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
