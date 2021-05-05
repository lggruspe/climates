"""Library for writing command-line interfaces."""

from infer_parser import Parser

from .args import InvalidFlag, arg, opt, switch, toggle
from .cli import Cli, run
from .command import Command
from .utils import make_simple_parser


__all__ = [
    "Parser",

    "InvalidFlag",
    "arg",
    "opt",
    "switch",
    "toggle",

    "Cli",
    "run",

    "Command",

    "make_simple_parser",
]
