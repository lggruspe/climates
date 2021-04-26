"""Opts and args."""

from dataclasses import dataclass
from inspect import Parameter
from typing import Any, Dict, Literal, Optional, Sequence, Tuple, Union

from infer_parser import infer_length

from climux.errors import InvalidFlag
from climux.utils import collect_annotation


def infer_nargs(param: Parameter) -> Union[int, Literal["*"]]:
    """Infer nargs."""
    if param.annotation == param.empty:
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            return "*"
        return 1
    length = infer_length(collect_annotation(param))
    return length if isinstance(length, int) else "*"


@dataclass
class Arg:
    """Named positional argument.

    There's no name member, because it's inferred from inspect.Parameter.
    """
    help: Optional[str] = None  # pylint: disable=redefined-builtin


class Opt:  # pylint: disable=too-few-public-methods
    """Flag options."""
    def __init__(self, flag: str, *flags: str, help: Optional[str] = None):  # pylint: disable=redefined-builtin; # noqa: E501
        self.flags = (flag,) + flags
        self.help = help
        for flag_ in self.flags:
            if not flag_.startswith("-"):  # pylint: disable=no-member
                raise InvalidFlag(flag_)


class InferredParameter:  # pylint: disable=too-few-public-methods
    """Inferred CLI arguments and options (from inspect.Parameter).

    Contains args and kwargs members, which can be passed to
    ArgumentParser.add_argument(*args, **kwargs).
    """
    def __init__(self, param: Parameter):
        self.param = param

        variadic = param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
        nargs = infer_nargs(param)
        default: Optional[Sequence[Any]] = [] if variadic else None
        required = False if variadic else param.default == param.empty

        self.args: Tuple[str, ...] = (f"--{param.name}",)
        self.kwargs: Dict[str, Any] = dict(
            default=default,
            nargs=nargs,
            required=required,
            dest=param.name,
        )

    def update(self, new: Union[Arg, Opt]) -> None:
        """Override inferred defaults with Arg or Opt.

        Also removes parameters that don't work with positional arguments.
        """
        if new.help is not None:
            self.kwargs["help"] = new.help

        if isinstance(new, Opt):
            self.args = new.flags
        else:
            assert isinstance(new, Arg)
            self.args = (self.param.name,)
            self.kwargs.pop("dest", None)
            self.kwargs.pop("required", None)
