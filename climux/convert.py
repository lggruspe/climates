"""Convert argparse parsed args to function args."""

from inspect import Parameter, signature
from shlex import join
from typing import Any, Callable, Dict, Sequence, Tuple, Union

from infer_parser import CantInfer, CantParse, infer


Function = Callable[..., Any]
FunctionArgs = Tuple[Tuple[Any, ...], Dict[str, Any]]


class CantConvert(Exception):
    """Returned by convert function on failure."""


def get_parser(param: Parameter) -> Union[Function, CantInfer]:
    """Wrap infer to work with inspect.Parameters.

    Converts *args into a tuple and **kwargs into a dict.
    """
    annotation: Any = str
    if param.annotation != param.empty:
        annotation = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        annotation = Tuple[annotation, ...]
    elif param.kind == param.VAR_KEYWORD:
        annotation = Dict[str, annotation]
    return infer(annotation)


def convert(func: Function, inputs: Dict[str, Sequence[str]]
            ) -> Union[FunctionArgs, CantConvert]:
    """Construct args and kwargs for function from argparse inputs.

    Assumes all function parameters are in inputs (raises KeyError).
    """
    args = []
    kwargs = {}
    sig = signature(func)

    for name, param in sig.parameters.items():
        parse = get_parser(param)
        if isinstance(parse, CantInfer):
            return CantConvert(f"unsupported type: {param.annotation}")

        string = join(inputs[name])
        value = parse(string)
        if isinstance(value, CantParse):
            return CantConvert(f"'{string}' is an invalid value for {name}")

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
