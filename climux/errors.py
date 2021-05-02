"""Climux error types."""


class UnsupportedType(TypeError):
    """Unsupported type hints."""


class InvalidFlag(ValueError):
    """Invalid option flags (-f, --foo, etc.).

    The flag string should start with '-'.
    """
