"""Climux error types."""


class ClimuxError(Exception):
    """Climux base exception class."""


class UnsupportedType(ClimuxError):
    """Unsupported type hints."""


class InvalidArgument(ClimuxError):
    """Invalid argument name (shouldn't start with '-')."""


class InvalidFlag(ClimuxError):
    """Invalid option flags (-f, --foo, etc.).

    The flag string should start with '-'.
    """
