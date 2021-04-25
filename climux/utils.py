"""Some utilities."""

from inspect import Parameter
from typing import Any, Dict, Tuple


def collect_annotation(param: Parameter) -> Any:
    """Return param.annotation.

    Converts *args into tuple and **kwargs into dict.
    Assumes param is annotated.
    """
    assert param.annotation != param.empty
    hint: Any = param.annotation
    if param.kind == param.VAR_POSITIONAL:
        hint = Tuple[hint, ...]
    elif param.kind == param.VAR_KEYWORD:
        hint = Dict[str, hint]
    return hint
