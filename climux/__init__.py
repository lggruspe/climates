"""Library for writing command-line interfaces."""

from .cli import Cli, run
from .command import Command


__all__ = [
    "Cli",
    "Command",
    "run",
]
