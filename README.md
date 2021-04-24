Climux
======

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/climux/Python%20package)
[![PyPI](https://img.shields.io/pypi/v/climux)](https://pypi.org/project/climux/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/climux)](https://pypi.org/project/climux/)
[![GitHub](https://img.shields.io/github/license/lggruspe/climux)](./LICENSE)

Command-line interfaces made accessible to even simpletons.

Installation
------------

```bash
pip install climux
```

Usage
-----

```python
from climux import Cli, Command

def hello(name="stranger", /):
    """Say hello."""
    return f"Hello, {name}!"

cli = Cli("hello", description="Hello world app.")
cli.add(Command(hello))
cli.run()
```

See `example.py` for details.

Features
--------

- Subcommands
- Generate CLI help and options from function signature and docstring
- Automatic dispatch to command handling functions

License
-------

[MIT](./LICENSE).
