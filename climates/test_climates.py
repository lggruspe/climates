# type: ignore
"""Test climates."""
from argparse import ArgumentParser
import pytest
from climates import Climate, Command


def test_command_name():
    """Command name should be taken from function.__name__ or from alias."""
    def foobar():
        """Foobar."""

    assert Command(foobar).name == "foobar"
    assert Command(foobar, alias="foobaz").name == "foobaz"


def test_command_description():
    """Command description should be taken from function docstrings."""
    def foobar():
        pass

    def foobaz():
        """Foobaz."""

    assert Command(foobar).description is None
    assert "Foobaz." in Command(foobaz).description
    foobar()


def test_climate_constructor():
    """Climate constructor must set description and empty commands."""
    cli = Climate("test", description="Test CLI app")
    assert cli.prog == "test"
    assert cli.description == "Test CLI app"
    assert not cli.commands


def test_climate_build(cli):
    """Climate.build should create an ArgumentParser object."""
    assert isinstance(cli.build(), ArgumentParser)


def test_climate_build_description():
    """Climate.build should get description from Climate.description."""
    cli = Climate("test", description="Test CLI app")
    parser = cli.build()
    assert isinstance(parser, ArgumentParser)
    assert cli.description == parser.description


def test_climate_run_dispatch(cli):
    """Climate.run should dispatch automatically."""
    def fn_foo():
        return "Foo."

    def fn_bar():
        return "Bar."

    def fn_baz():
        return "Baz."

    cli.add(Command(fn_foo, alias="foo"))
    cli.add(Command(fn_bar, alias="bar"))
    cli.add(Command(fn_baz, alias="baz"))
    assert cli.run(["foo"]) == "Foo."
    assert cli.run(["bar"]) == "Bar."
    assert cli.run(["baz"]) == "Baz."


def test_climate_run_invalid_subcommand(cli, capsys):
    """Subcommand should be required and checked."""
    with pytest.raises(SystemExit):
        cli.run([])
    _, err = capsys.readouterr()
    assert "required: subcommand" in err

    with pytest.raises(SystemExit):
        cli.run(["invalid"])
    _, err = capsys.readouterr()
    assert "invalid choice" in err


def test__positional_only_parameters_with_default(cli, capsys):
    """Corresponding option should be positional and optional."""
    def func(arg="default", /):
        return arg

    cli.add(Command(func))
    assert cli.run(["func"]) == "default"
    assert cli.run(["func", "foo"]) == "foo"

    with pytest.raises(SystemExit):
        cli.run(["func", "--arg", "bar"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: --arg" in err


def test__positional_only_parameters_without_default(cli, capsys):
    """Corresponding option should be positional and required."""
    def func(arg, /):
        return arg

    cli.add(Command(func))
    assert cli.run(["func", "foo"]) == "foo"

    with pytest.raises(SystemExit):
        cli.run(["func", "--arg", "bar"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: --arg" in err

    with pytest.raises(SystemExit):
        cli.run(["func"])
    _, err = capsys.readouterr()
    assert "required: arg" in err


def test__keyword_only_parameters_with_default(cli, capsys):
    """Corresponding option should be an optional flag."""
    def func(*, arg="default"):
        return arg

    cli.add(Command(func))
    assert cli.run(["func"]) == "default"
    assert cli.run(["func", "--arg", "foo"]) == "foo"

    with pytest.raises(SystemExit):
        cli.run(["func", "foo"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: foo" in err


def test__keyword_only_parameters_without_default(cli, capsys):
    """Corresponding option should be a required flag."""
    def func(*, arg):
        return arg

    cli.add(Command(func))
    assert cli.run(["func", "--arg", "foo"]) == "foo"

    with pytest.raises(SystemExit):
        cli.run(["func", "foo"])
    _, err = capsys.readouterr()
    assert "required: --arg" in err

    with pytest.raises(SystemExit):
        cli.run(["func"])
    _, err = capsys.readouterr()
    assert "required: --arg" in err


def test__var_positional_parameters(cli, capsys):
    """Corresponding option should be optional list."""
    def func(*args):
        return args

    cli.add(Command(func))
    assert cli.run(["func"]) == ()
    assert cli.run(["func", "foo", "bar", "baz"]) == ("foo", "bar", "baz")

    with pytest.raises(SystemExit):
        cli.run(["func", "--args", "foo"])
    _, err = capsys.readouterr()
    assert "unrecognized arguments: --args" in err


def test__var_keyword_parameters(cli, capsys):
    """Corresponding option should be an optional flag that takes in a list.

    Keys and values should be separated by ':' and pairs should be separated
    by spaces.
    """
    def func(**kwargs):
        return kwargs

    cli.add(Command(func))

    assert cli.run(["func"]) == {}
    assert cli.run(["func", "--kwargs"]) == {}
    assert cli.run(["func", "--kwargs", "a:1", "b:2"]) == {"a": "1", "b": "2"}

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "invalid"])
    _, err = capsys.readouterr()
    assert "'key:value'" in err


def test__annotated_parameters(cli):
    """Options should be converted using annotation."""
    def func(arg: float, *args: int, **kwargs: float):
        return arg, args, kwargs

    cli.add(Command(func))
    arg, args, kwargs = cli.run([
        "func",
        "--arg", "1.5",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "--kwargs", "a:1.1", "b:2.2",
    ])
    assert arg == 1.5
    assert args == tuple(range(11))
    assert kwargs == {"a": 1.1, "b": 2.2}


def test__failed_option_parsing(cli, capsys):
    """Program should abort if it can't parse an option."""
    def func(arg: int, /):
        return arg

    cli.add(Command(func))
    assert cli.run(["func", "42"]) == 42

    with pytest.raises(SystemExit):
        cli.run(["func", "a"])
    _, err = capsys.readouterr()
    assert "invalid int value" in err


def test__failed_keyword_parsing(cli, capsys):
    """Program should abort if it can't parse a key-value pair."""
    def func(**kwargs: int):
        return kwargs

    cli.add(Command(func))
    assert cli.run(["func", "--kwargs", "x:42"]) == {"x": 42}

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "invalid"])
    _, err = capsys.readouterr()
    assert "'key:value'" in err

    with pytest.raises(SystemExit):
        cli.run(["func", "--kwargs", "x:42.0"])
    _, err = capsys.readouterr()
    assert "could not parse into int" in err


def test__command_with_custom_parser(cli):
    """Options should be passed to the parser if there is one."""
    def func(arg):
        return arg

    cli.add(Command(func, parsers={"arg": lambda s: s[::-1]}))
    assert cli.run(["func", "--arg", "foo"]) == "oof"
    assert cli.run(["func", "--arg", "bar"]) == "rab"
    assert cli.run(["func", "--arg", "baz"]) == "zab"


def test__command_with_result(cli, capsys):
    """Print function result if Command.result is True.

    Climate.run should still return the result regardless of the value of
    Command.result.
    """
    def func(arg):
        return arg

    cli.add(Command(func, alias="foo"))
    cli.add(Command(func, alias="bar", result=False))

    assert cli.run(["foo", "--arg", "1"]) == "1"
    out, _ = capsys.readouterr()
    assert "1" in out

    assert cli.run(["bar", "--arg", "1"]) == "1"
    out, _ = capsys.readouterr()
    assert not out
