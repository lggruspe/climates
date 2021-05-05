"""Climux CLI builder and runner."""

import argparse
import typing as t

from .command import Command

SUBCOMMAND_DEST = "subcommand "


class Cli:
    """CLI builder and dispatcher."""
    def __init__(self, prog: str, description: t.Optional[str] = None):
        self.prog = prog
        self.description = description
        self.commands: t.Dict[str, Command] = {}

    def add(self, command: Command) -> None:
        """Add command."""
        self.commands[command.name] = command

    def build(self) -> argparse.ArgumentParser:
        """Build ArgumentParser."""
        parser = argparse.ArgumentParser(prog=self.prog,
                                         description=self.description)
        subparsers = parser.add_subparsers(dest=SUBCOMMAND_DEST, required=True)
        for name, command in self.commands.items():
            subparser = subparsers.add_parser(name,
                                              description=command.description)
            command.set_options(subparser)
        return parser

    def run(self, args_: t.Optional[t.Sequence[str]] = None) -> t.Any:
        """Run argument parser and dispatcher."""
        args = vars(self.build().parse_args(args_))
        command = self.commands[args[SUBCOMMAND_DEST]]
        del args[SUBCOMMAND_DEST]
        return command.invoke(args)


def run(command: Command, args_: t.Optional[t.Sequence[str]] = None) -> t.Any:
    """Build and run argument parser for single command."""
    parser = argparse.ArgumentParser(prog=command.name,
                                     description=command.description)
    command.set_options(parser)
    args = vars(parser.parse_args(args_))
    return command.invoke(args)


__all__ = ["Cli", "run"]
