Climates
========

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/climates/Python%20package)
[![PyPI](https://img.shields.io/pypi/v/climates)](https://pypi.org/project/climates/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/climates)](https://pypi.org/project/climates/)
[![GitHub](https://img.shields.io/github/license/lggruspe/climates)](./LICENSE)

Command-line interfaces made accessible to even simpletons.

Installation
------------

```bash
pip install climates
```

Usage
-----

```python
from climates import Climate, Command

def hello(name="stranger", /):
    """Say hello."""
    return f"Hello, {name}!"

cli = Climate("hello", description="Hello world app.")
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
