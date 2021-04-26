"""Climux error types."""


class ClimuxError(Exception):
    """Climux base exception class."""


class UnsupportedType(ClimuxError):
    """Unsupported type hints."""
