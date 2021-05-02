"""Test decorators.py."""

from .arguments import Arg
from .command import Command
from .decorators import command


def test_command_decorator() -> None:
    """command decorator should get Command.args from decorated class."""

    def test(arg):  # type: ignore
        return arg

    test_arg = Arg()

    @command(test)
    class TestCommand:  # pylint: disable=too-few-public-methods
        """Customizes test command."""
        arg = test_arg

    test_command = TestCommand()
    assert isinstance(test_command, Command)
    assert test_command.args["arg"] == test_arg  # pylint: disable=no-member
    assert test(True)  # type: ignore
