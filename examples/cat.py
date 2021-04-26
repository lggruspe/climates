from pathlib import Path
from climux import Command, Arg, run


def cat(*paths: Path) -> str:
    """Concatenate files to standard output."""
    return "".join(path.read_text() for path in paths)


run(Command(cat, args=dict(paths=Arg())))
