"""Test climux."""
from argparse import ArgumentParser
from typing import Callable, Dict, Tuple

from pytest import CaptureFixture
import pytest

from climux import Cli, Command, run
from climux.arguments import Arg, Opt, Switch, Toggle
from climux.errors import UnsupportedType


def test_command_name() -> None:
    """Command name should be taken from function.__name__ or from alias."""
    def foobar() -> None:
        """Foobar."""

    assert Command(foobar).name == "foobar"
    assert Command(foobar, alias="foobaz").name == "foobaz"


def test_command_description() -> None:
    """Command description should be taken from function docstrings."""
    def foobar() -> None:
        pass

    def foobaz() -> None:
        """Foobaz."""

    assert Command(foobar).description is None
    description = Command(foobaz).description
    assert isinstance(description, str)
    assert "Foobaz." in description
    foobar()


def test_command_unsupported_type() -> None:
    """Command should raise an error if type hint is unsupported."""
    def func(arg_: Callable[..., int]) -> None:  # pylint: disable=unused-argument; # noqa: E501
        """Does nothing."""

    with pytest.raises(UnsupportedType) as exc_info:
        Command(func)
    assert "typing.Callable[..., int]" in exc_info.value.args[0]


def test_cli_constructor() -> None:
    """Cli constructor must set description and empty commands."""
    cli = Cli("test", description="Test CLI app")
    assert cli.prog == "test"
    assert cli.description == "Test CLI app"
    assert not cli.commands


def test_cli_build(cli: Cli) -> None:
    """Cli.build should create an ArgumentParser object."""
    assert isinstance(cli.build(), ArgumentParser)


def test_cli_build_description() -> None:
    """Cli.build should get description from Cli.description."""
    cli = Cli("test", description="Test CLI app")
    parser = cli.build()
    assert isinstance(parser, ArgumentParser)
    assert cli.description == parser.description


def test_cli_run_dispatch(cli: Cli) -> None:
    """Cli.run should dispatch automatically."""
    def fn_foo() -> str:
        return "Foo."

    def fn_bar() -> str:
        return "Bar."

    def fn_baz() -> str:
        return "Baz."

    cli.add(Command(fn_foo, alias="foo"))
    cli.add(Command(fn_bar, alias="bar"))
    cli.add(Command(fn_baz, alias="baz"))
    assert cli.run(["foo"]) == "Foo."
    assert cli.run(["bar"]) == "Bar."
    assert cli.run(["baz"]) == "Baz."


def test_cli_run_invalid_subcommand(cli: Cli,
                                    capsys: CaptureFixture[str]) -> None:
    """Subcommand should be required and checked."""
    with pytest.raises(SystemExit):
        cli.run([])
    _, err = capsys.readouterr()
    assert "required: subcommand" in err

    with pytest.raises(SystemExit):
        cli.run(["invalid"])
    _, err = capsys.readouterr()
    assert "invalid choice" in err


def test_run() -> None:
    """run should build and run argparse with no subcommands."""
    Result = Tuple[int, Tuple[int, ...], Dict[str, int]]

    def func(arg_: int, *args: int, **kwargs: int) -> Result:
        return arg_, args, kwargs

    result = run(Command(func), [
        "--arg_", "1",
        "--args", "2", "3",
        "--kwargs", "a", "4", "b", "5",
    ])
    assert result == (1, (2, 3,), {"a": 4, "b": 5})


def test__parameter_with_default(cli: Cli,
                                 capsys: CaptureFixture[str]) -> None:
    """Parameter should turn into CLI --option."""
    def func(oof="oof", /, rab="rab", *, zab="zab"):  # type: ignore
        return dict(oof=oof, rab=rab, zab=zab)

    cli.add(Command(func))
    assert cli.run(["func"]) == dict(oof="oof", rab="rab", zab="zab")
    assert cli.run(["func", "--oof", "1", "--rab", "2", "--zab", "3"]) == dict(  # noqa: E501
        oof="1", rab="2", zab="3"
    )

    with pytest.raises(SystemExit):
        cli.run(["func", "oof"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: oof" in err


def test__parameter_without_default(cli: Cli,
                                    capsys: CaptureFixture[str]) -> None:
    """Parameter should turn into required CLI --option."""
    def func(oof, /, rab, *, zab):  # type: ignore
        return dict(oof=oof, rab=rab, zab=zab)

    cli.add(Command(func))
    assert cli.run(["func", "--oof", "1", "--rab", "2", "--zab", "3"]) == dict(
        oof="1", rab="2", zab="3"
    )

    with pytest.raises(SystemExit):
        cli.run(["func"])
    _, err = capsys.readouterr()
    assert "the following arguments are required: --oof, --rab, --zab" in err


def test__var_positional_parameters(cli: Cli,
                                    capsys: CaptureFixture[str]) -> None:
    """Corresponding option should be optional list."""
    def func(*args):  # type: ignore
        return args

    cli.add(Command(func))
    assert cli.run(["func"]) == ()
    assert cli.run("func --args foo bar baz".split()) == ("foo", "bar", "baz")

    with pytest.raises(SystemExit):
        cli.run(["func", "foo"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: foo" in err


def test__var_keyword_parameters(cli: Cli,
                                 capsys: CaptureFixture[str]) -> None:
    """Corresponding option should be an optional flag that takes in a list.

    The list should be an alternating sequence of keys and values separated by
    spaces.
    """
    def func(**kwargs: int) -> Dict[str, int]:
        return kwargs

    cli.add(Command(func))

    assert cli.run(["func"]) == {}
    assert cli.run(["func", "--kwargs"]) == {}
    assert cli.run("func --kwargs a 1 b 2".split()) == {"a": 1, "b": 2}

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "invalid"])
    _, err = capsys.readouterr()
    assert "invalid value: 'invalid'" in err

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "a", "1", "b"])
    _, err = capsys.readouterr()
    assert "invalid value: 'a 1 b'" in err

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "x", "42.0"])
    _, err = capsys.readouterr()
    assert "invalid value: 'x 42.0'" in err
    assert "expected typing.Dict[str, int]" in err


def test__annotated_parameters(cli: Cli) -> None:
    """Options should be converted using annotation."""
    Result = Tuple[float, Tuple[int, ...], Dict[str, float]]

    def func(arg_: float, *args: int, **kwargs: float) -> Result:
        return arg_, args, kwargs

    cli.add(Command(func))
    arg_, args, kwargs = cli.run([
        "func",
        "--arg_", "1.5",
        "--args", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "--kwargs", "a", "1.1", "b", "2.2",
    ])
    assert arg_ == 1.5
    assert args == tuple(range(11))
    assert kwargs == {"a": 1.1, "b": 2.2}


def test__failed_option_parsing(cli: Cli, capsys: CaptureFixture[str]) -> None:
    """Program should abort if it can't parse an option."""
    def func(arg_: int) -> int:
        return arg_

    cli.add(Command(func))
    assert cli.run(["func", "--arg_", "42"]) == 42

    with pytest.raises(SystemExit):
        cli.run(["func", "--arg_", "a"])
    _, err = capsys.readouterr()
    assert "invalid value" in err
    assert "expected int" in err


def test__command_with_custom_parser(cli: Cli) -> None:
    """Options should be passed to the parser if there is one."""
    def func(arg_):  # type: ignore
        return arg_

    cli.add(Command(func, parsers={"arg_": lambda s: s[::-1]}))
    assert cli.run(["func", "--arg_", "foo"]) == "oof"
    assert cli.run(["func", "--arg_", "bar"]) == "rab"
    assert cli.run(["func", "--arg_", "baz"]) == "zab"


def test__command_with_result(cli: Cli, capsys: CaptureFixture[str]) -> None:
    """Print function result if Command.result is True.

    Cli.run should still return the result regardless of the value of
    Command.result.
    """
    def func(arg_):  # type: ignore
        return arg_

    cli.add(Command(func, alias="foo"))
    cli.add(Command(func, alias="bar", result=False))

    assert cli.run(["foo", "--arg_", "1"]) == "1"
    out, _ = capsys.readouterr()
    assert "1" in out

    assert cli.run(["bar", "--arg_", "1"]) == "1"
    out, _ = capsys.readouterr()
    assert not out


def test__command_with_custom_args(cli: Cli,
                                   capsys: CaptureFixture[str]) -> None:
    """Use custom args when specified."""
    def func(pos, short):  # type: ignore
        return pos, short

    cli.add(Command(func, args=dict(
        pos=Arg(),
        short=Opt("-s"),
    )))

    assert cli.run(["func", "foo", "-s", "bar"]) == ("foo", "bar")

    with pytest.raises(SystemExit):
        cli.run(["func"])
    _, err = capsys.readouterr()
    assert "the following arguments are required: pos, -s" in err


def test__command_with_arg_help(capsys: CaptureFixture[str]) -> None:
    """CLI should use Arg.help if specified."""
    def func(pos):  # type: ignore
        return pos

    with pytest.raises(SystemExit):
        run(Command(func, args=dict(pos=Arg(help="Positional argument"))),
            ["-h"])
    out, _ = capsys.readouterr()
    assert "Positional argument" in out
    assert func(True)  # type: ignore


def test__command_with_switch() -> None:
    """Switch flag should be false by default and true if either short or long
    flag is specified."""
    def func(arg: bool):  # type: ignore
        return arg

    func(True)
    command = Command(func, args=dict(arg=Switch("-a", "--arg")))
    assert run(command, []) is False
    assert run(command, ["-a"]) is True
    assert run(command, ["--arg"]) is True


def test__command_with_toggle_with_true_default() -> None:
    """If function param is True by default, specifying the flag should set the
    value to False."""
    def func(arg: bool = True):  # type: ignore
        return arg

    func(True)
    command = Command(func, args=dict(arg=Toggle("-a", "--arg")))
    assert run(command, []) is True
    assert run(command, ["-a"]) is False
    assert run(command, ["--arg"]) is False


def test__command_with_toggle_without_default() -> None:
    """If function param has no default, Toggle should behave like Switch."""
    def func(arg: bool):  # type: ignore
        return arg

    func(True)
    command = Command(func, args=dict(arg=Toggle("-a", "--arg")))
    assert run(command, []) is False
    assert run(command, ["-a"]) is True
    assert run(command, ["--arg"]) is True


def test__nested_parameters() -> None:
    """Arguments should be parsed correctly."""
    def func(arg: dict[tuple[str, int], tuple[str, float]]):  # type: ignore
        return arg

    command = Command(func)
    assert run(command, ["--arg"]) == {}
    assert run(command, ["--arg", "foo", "1", "bar", "2.0"]) == {
        ("foo", 1): ("bar", 2.0)
    }

    options = "--arg foo 1 bar 2.0 a 3 b 4.5".split()
    assert run(command, options) == {
        ("foo", 1): ("bar", 2.0),
        ("a", 3): ("b", 4.5),
    }
