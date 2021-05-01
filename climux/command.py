"""Climux command builder and runner."""

import argparse
import dataclasses
import inspect
import typing as t

from infer_parser import UnsupportedType, make_parser

from . import errors
from .arguments import Arg, Opt, InferredParameter
from .convert import CantConvert, convert, get_type_name, wrap_custom_parser


Function = t.Callable[..., t.Any]
Error = t.Callable[..., t.NoReturn]


def get_parser(param: inspect.Parameter) -> Function:
    """Wrap infer to work with inspect.Parameters.

    Converts *args into a tuple and **kwargs into a dict.
    Uses str for unannotated parameters.
    May raise UnsupportedType (from make_parser).
    """
    annotation: t.Any = str
    if param.annotation != param.empty:
        annotation = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        annotation = t.Tuple[annotation, ...]
    elif param.kind == param.VAR_KEYWORD:
        annotation = t.Dict[str, annotation]
    return make_parser(annotation)


@dataclasses.dataclass
class Command:
    """Represent CLI commands."""
    function: Function
    alias: t.Optional[str] = None
    result: bool = True
    parsers: t.Dict[str, Function] = dataclasses.field(default_factory=dict)
    args: t.Dict[str, t.Union[Arg, Opt]] = \
        dataclasses.field(default_factory=dict)

    subparser: t.Optional[argparse.ArgumentParser] = \
        dataclasses.field(default=None, init=False)
    inferred_options: t.List[InferredParameter] = \
        dataclasses.field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Infer unset argument parsers.

        Also wraps custom parsers."""
        sig = inspect.signature(self.function)
        for name, param in sig.parameters.items():
            if (parser := self.parsers.get(name)) is not None:
                self.parsers[name] = wrap_custom_parser(parser)
                continue
            try:
                self.parsers[name] = get_parser(param)
            except UnsupportedType as exc:
                assert param.annotation != param.empty
                raise errors.UnsupportedType(get_type_name(param)) from exc

        self.infer_options()

    @property
    def name(self) -> str:
        """Get command name as it appears in the command-line."""
        if self.alias is not None:
            return self.alias
        return self.function.__name__

    @property
    def description(self) -> t.Optional[str]:
        """Get command description from function docstring."""
        return self.function.__doc__

    def infer_options(self) -> None:
        """Infer ArgumentParser options from function signature.

        Result is appended into self.inferred_options."""
        sig = inspect.signature(self.function)
        for param in sig.parameters.values():
            inferred = InferredParameter(param)
            if self.args and param.name in self.args:
                inferred.update(self.args[param.name])
            self.inferred_options.append(inferred)

    def set_options(self, parser: argparse.ArgumentParser) -> None:
        """Set parser options from command function signature."""
        self.subparser = parser
        for inferred in self.inferred_options:
            args = inferred.args
            kwargs = inferred.kwargs
            parser.add_argument(*args, **kwargs)

    def invoke(self, inputs: t.Mapping[str, t.Sequence[str]]) -> t.Any:
        """Invoke command on argparse.Namespace dictionary."""
        assert self.subparser is not None

        all_args = convert(self.function, inputs, self.parsers)
        if isinstance(all_args, CantConvert):
            self.subparser.error(all_args.args[0])
        args, kwargs = all_args
        result = self.function(*args, **kwargs)
        if self.result:
            print(result)
        return result
