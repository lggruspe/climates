from climux import Cli, Command


def hello(name="world", /):
    """Say hello."""
    return f"Hello, {name}!"


def example(a, b=1, /, c=2, *d: int, e=3, h, **f: int):
    """Run example."""
    return repr((a, b, c, d, e, f))


def bye(name=None):
    """Say bye."""
    if name:
        return f"Bye-bye, {name}."
    else:
        return "Bye-bye."


cli = Cli("hello", description="Hello world app.")
for func in (hello, example, bye):
    cli.add(Command(func))
cli.run()
