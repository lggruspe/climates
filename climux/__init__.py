"""Library for writing command-line interfaces."""

from argparse import ArgumentParser
from dataclasses import dataclass
from inspect import signature, Parameter
from typing import (
    Any, Callable, Dict, Literal, Mapping, NoReturn, Optional, Sequence, Tuple,
    Union
)

from infer_parser import infer_length

from .convert import CantConvert, convert
from .utils import collect_annotation


Function = Callable[..., Any]
Error = Callable[..., NoReturn]
Arg = Tuple[Tuple[Any, ...], Dict[str, Any]]


def arg(*args: Any, **kwargs: Any) -> Arg:
    """Return arguments."""
    return args, kwargs


def infer_nargs(param: Parameter) -> Union[int, Literal["*"]]:
    """Infer nargs."""
    if param.annotation == param.empty:
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            return "*"
        return 1
    length = infer_length(collect_annotation(param))
    return length if isinstance(length, int) else "*"


def make_argument(param: Parameter) -> Arg:
    """Make ArgumentParser argument."""
    variadic = param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
    nargs = infer_nargs(param)
    default: Optional[Sequence[Any]] = [] if variadic else None
    required = False if variadic else param.default == param.empty
    return (f"--{param.name}",), dict(
        default=default,
        nargs=nargs,
        required=required,
        dest=param.name,
    )


def update_argument(old: Arg, new: Arg) -> Arg:
    """Update argument.

    Also removes parameters that don't make sense for positional arguments.
    """
    _, old_kwargs = old
    new_args, new_kwargs = new
    old_kwargs.update(new_kwargs)
    if len(new_args) == 1 and not new_args[0].startswith("-"):
        old_kwargs.pop("dest", None)
        old_kwargs.pop("required", None)
    return (new_args, old_kwargs)


@dataclass
class Command:
    """Represent CLI commands."""
    function: Function
    alias: Optional[str] = None
    result: bool = True
    parsers: Optional[Dict[str, Function]] = None
    args: Optional[Dict[str, Arg]] = None

    subparser: Optional[ArgumentParser] = None

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
            args, kwargs = make_argument(param)
            if self.args and param.name in self.args:
                args, kwargs = update_argument((args, kwargs),
                                               self.args[param.name])
            parser.add_argument(*args, **kwargs)

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
