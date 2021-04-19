Climates
========

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/climates/Python%20package)
![PyPI](https://img.shields.io/pypi/v/climates)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/climates)
![GitHub](https://img.shields.io/github/license/lggruspe/climates)

Command-line interfaces made accessible to even simpletons.

Installation
------------

```bash
pip install climates
```

Usage
-----

```python
# Step 1: import Climate
from climates import Climate, Command
# Step 2: create Climate object
cli = Climate("hello", description="Hello world app.")
# Step 3: ???
# Step 4: add commands to CLI
cli.add(Command(hello))
cli.add(Command(bye))
# Step 5: run CLI
cli.run()
# Step 6: PROFIT!!!
```

See `example.py` for details.

Features
--------

- Generate CLI help and options from docstrings and type annotations
- Automatic dispatch to command handling functions

License
-------

MIT.
