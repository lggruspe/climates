"""Command-line interfaces made accessible to even simpletons."""

from argparse import ArgumentParser
from dataclasses import dataclass
from functools import wraps
from inspect import signature, Parameter
from typing import Any, Callable, Dict, NoReturn, Optional, Sequence, Tuple


Function = Callable[..., Any]
Error = Callable[..., NoReturn]


def parse_pair(pair: str,
               converter: Function,
               error: Error) -> Tuple[str, Any]:
    """Parse key:value string.

    Runs error function on failure (error function should abort the program).
    Catches ValueError raised by converter.
    """
    try:
        key, val = pair.split(":", 1)
    except ValueError:
        error("key value pair should be separated by ':' as in 'key:value'")
    try:
        return key, converter(val)
    except ValueError as exc:
        error(exc)


def make_converter(func: Function) -> Function:
    """Make converter (parser) out of function.

    Rethrows all exceptions as ValueError so ArgumentParser can handle them.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            raise ValueError(f"could not parse into {func.__name__}") from exc
    return wrapper


@dataclass
class Command:
    """Represent CLI commands."""
    function: Function
    alias: Optional[str] = None
    result: bool = True
    parsers: Optional[Dict[str, Function]] = None
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

    def converter(self, param: Parameter) -> Function:
        """Get converter for parameter."""
        converter: Function = str
        if param.annotation != param.empty:
            converter = param.annotation
        if self.parsers:
            converter = self.parsers.get(param.name, converter)
        return make_converter(converter)

    def set_options(self, parser) -> None:
        """Set parser options from command function signature."""
        self.subparser = parser
        sig = signature(self.function)
        for name, param in sig.parameters.items():
            # NOTE add_argument(help=...) should be taken from docstring params
            converter = self.converter(param)
            default = param.default if param.default != param.empty else None
            if param.kind == param.POSITIONAL_ONLY:
                if default is None:
                    parser.add_argument(name, type=converter)
                else:
                    parser.add_argument(
                        name,
                        nargs="?",
                        default=default,
                        type=converter,
                    )
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                parser.add_argument(
                    f"--{name}",
                    default=default,
                    type=converter,
                    required=param.default == param.empty,
                    dest=name,
                )
            elif param.kind == param.VAR_POSITIONAL:
                parser.add_argument(
                    name,
                    nargs="*",
                    type=converter,
                )
            elif param.kind == param.KEYWORD_ONLY:
                parser.add_argument(
                    f"--{name}",
                    default=default,
                    type=converter,
                    required=param.default == param.empty,
                    dest=name,
                )
            else:
                assert param.kind == param.VAR_KEYWORD
                parser.add_argument(
                    f"--{name}",
                    default=[],
                    nargs="*",
                    type=str,  # --name key1:val1 key2:val2 ... (parsed later)
                )

    def invoke(self, args: Dict[str, Any]) -> Any:
        """Invoke command on argparse.Namespace dictionary."""
        assert self.subparser is not None

        sig = signature(self.function)
        argv = []
        kwargs = {}
        for name, param in sig.parameters.items():
            value = args[name]
            if param.kind == param.POSITIONAL_ONLY:
                argv.append(value)
            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                argv.append(value)
            elif param.kind == param.VAR_POSITIONAL:
                argv.extend(value)
            elif param.kind == param.KEYWORD_ONLY:
                kwargs[name] = value
            else:
                assert param.kind == param.VAR_KEYWORD
                for pair in value:
                    error = self.subparser.error
                    key, val = parse_pair(pair, self.converter(param), error)
                    kwargs[key] = val
        result = self.function(*argv, **kwargs)
        if self.result:
            print(result)
        return result


SUBCOMMAND_DEST = "subcommand "


class Climate:
    """Climate CLI builder and dispatcher."""
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
