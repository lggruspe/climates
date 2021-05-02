"""Decorators for customizing CLI commands.

Example:

def hello(name: str = 'stranger') -> str:
    '''Say hello.'''
    return f'Hello, {name}!'

@command(hello, alias='say-hello', show_result=True)
class HelloCommand:
    name = Arg()

run(HelloCommand())
"""

import inspect
import typing as t
from .arguments import Arg, Opt
from .command import Command


Function = t.Callable[..., t.Any]
AnalyzeResult = tuple[
    t.Dict[str, Function],
    t.Dict[str, t.Union[Arg, Opt]],
]


def _analyze(cls: type[t.Any]) -> AnalyzeResult:
    """Analyze class to return dict of parsers and args for Command."""
    return {}, {
        k: v for k, v in inspect.getmembers(cls)
        if not k.startswith("_")
        if not inspect.ismethod(v)
    }


CommandResult = t.Callable[
    [type[t.Any]],
    t.Callable[[], Command],
]


def command(function: Function,
            alias: t.Optional[str] = None,
            result: bool = True) -> CommandResult:
    """Decorate custom command class.

    Replaces decorated class with function that returns Command object.
    """
    def decorator(cls: type[t.Any]) -> t.Callable[[], Command]:
        parsers, args = _analyze(cls)

        def func() -> Command:
            return Command(function, alias, result, parsers, args)
        return func
    return decorator


__all__ = ["command"]
