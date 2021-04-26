"""Library for writing command-line interfaces."""

from argparse import ArgumentParser
from dataclasses import dataclass, field
from inspect import signature
from typing import (
    Any, Callable, Dict, Mapping, NoReturn, Optional, Sequence, Union
)

from infer_parser import CantInfer

from .arguments import InferredParameter, Arg, Opt
from .convert import (
    CantConvert, convert, get_parser, get_type_name, wrap_custom_parser
)
from .errors import UnsupportedType


Function = Callable[..., Any]
Error = Callable[..., NoReturn]


@dataclass
class Command:
    """Represent CLI commands."""
    function: Function
    alias: Optional[str] = None
    result: bool = True
    parsers: Dict[str, Function] = field(default_factory=dict)
    args: Dict[str, Union[Arg, Opt]] = field(default_factory=dict)

    subparser: Optional[ArgumentParser] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Infer unset argument parsers.

        Also wraps custom parsers."""
        sig = signature(self.function)
        for name, param in sig.parameters.items():
            if (parser := self.parsers.get(name)) is not None:
                self.parsers[name] = wrap_custom_parser(parser)
            else:
                self.parsers[name] = get_parser(param)
            if isinstance(self.parsers[name], CantInfer):
                assert param.annotation != param.empty
                raise UnsupportedType(get_type_name(param))

    @property
    def name(self) -> str:
        """Get command name as it appears in the command-line."""
        if self.alias is not None:
            return self.alias
        return self.function.__name__

    @property
    def description(self) -> Optional[str]:
        """Get command description from function docstring."""
        return self.function.__doc__

    def set_options(self, parser: ArgumentParser) -> None:
        """Set parser options from command function signature."""
        self.subparser = parser
        sig = signature(self.function)
        for param in sig.parameters.values():
            # NOTE add_argument(help=...) should be taken from docstring params
            inferred = InferredParameter(param)
            if self.args and param.name in self.args:
                inferred.update(self.args[param.name])
            parser.add_argument(*inferred.args, **inferred.kwargs)

    def invoke(self, inputs: Mapping[str, Sequence[str]]) -> Any:
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


SUBCOMMAND_DEST = "subcommand "


class Cli:
    """CLI builder and dispatcher."""
    def __init__(self, prog: str, description: Optional[str] = None):
        self.prog = prog
        self.description = description
        self.commands: Dict[str, Command] = {}

    def add(self, command: Command) -> None:
        """Add command."""
        self.commands[command.name] = command

    def build(self) -> ArgumentParser:
        """Build ArgumentParser."""
        parser = ArgumentParser(prog=self.prog, description=self.description)
        subparsers = parser.add_subparsers(dest=SUBCOMMAND_DEST, required=True)
        for name, command in self.commands.items():
            subparser = subparsers.add_parser(name,
                                              description=command.description)
            command.set_options(subparser)
        return parser

    def run(self, args_: Optional[Sequence[str]] = None) -> Any:
        """Run argument parser and dispatcher."""
        args = vars(self.build().parse_args(args_))
        command = self.commands[args[SUBCOMMAND_DEST]]
        del args[SUBCOMMAND_DEST]
        return command.invoke(args)


def build(command: Command) -> ArgumentParser:
    """Build ArgumentParser with single command."""
    parser = ArgumentParser(prog=command.name, description=command.description)
    command.set_options(parser)
    return parser


def run(command: Command, args_: Optional[Sequence[str]] = None) -> Any:
    """Build and run argument parser for single command."""
    args = vars(build(command).parse_args(args_))
    return command.invoke(args)
