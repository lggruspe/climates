"""Climux command builder and runner."""

import argparse
import dataclasses
import inspect
import typing as t

from .args import Argument, opt
from .convert import CantConvert, convert


Function = t.Callable[..., t.Any]


@dataclasses.dataclass
class Command:
    """Represent CLI commands."""
    function: Function
    alias: t.Optional[str] = None
    show_result: bool = True
    custom: t.Dict[str, Argument] = dataclasses.field(default_factory=dict)

    subparser: t.Optional[argparse.ArgumentParser] = \
        dataclasses.field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize unset custom arguments."""
        sig = inspect.signature(self.function)
        for name in sig.parameters:
            self.custom.setdefault(name, opt())
        self.infer_options()

    @property
    def name(self) -> str:
        """Get command name as it appears in the command-line."""
        if self.alias is not None:
            return self.alias
        return self.function.__name__

    @property
    def description(self) -> t.Optional[str]:
        """Get command description from function docstring."""
        return self.function.__doc__

    def infer_options(self) -> None:
        """Infer ArgumentParser options from function signature."""
        sig = inspect.signature(self.function)
        for name, param in sig.parameters.items():
            custom = self.custom[name]
            custom.fill_in(param)

    def set_options(self, parser: argparse.ArgumentParser) -> None:
        """Set parser options from command function signature."""
        self.subparser = parser
        sig = inspect.signature(self.function)
        for param in sig.parameters.values():
            self.custom[param.name].add_to(parser)

    def invoke(self, inputs: t.Mapping[str, t.Sequence[str]]) -> t.Any:
        """Invoke command on argparse.Namespace dictionary."""
        assert self.subparser is not None
        parsers = {name: arg.parser for name, arg in self.custom.items()}

        # parsers are not null because of Argument.fill_in
        all_args = convert(self.function, inputs, parsers)  # type: ignore
        if isinstance(all_args, CantConvert):
            self.subparser.error(all_args.args[0])
        args, kwargs = all_args
        result = self.function(*args, **kwargs)
        if self.show_result:
            print(result)
        return result


__all__ = ["Command"]
