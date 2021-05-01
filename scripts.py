#!/usr/bin/env python
from climux import Cli, Command
from subprocess import run
import sys


def sh(cmd):
    """Run command, exit if returncode is non-zero."""
    print("$", cmd)
    proc = run(cmd, shell=True)
    if proc.returncode != 0:
        print('> ', cmd, file=sys.stderr)
        sys.exit(proc.returncode)


def dist():
    """Make release."""
    sh("python setup.py sdist bdist_wheel")
    sh("twine upload dist/*")


def lint():
    """Run linters."""
    sh("mypy -p climux --strict")
    sh("pylint climux --fail-under=10")
    sh("flake8 climux --max-complexity=10")


def test():
    """Run tests."""
    sh("pytest --cov=climux --cov-report=term-missing --cov-fail-under=90 "
       "--cov-branch -x")


if __name__ == "__main__":
    cli = Cli("scripts.py", description="Dev scripts.")
    for func in (dist, lint, test):
        cli.add(Command(func, result=None))
    cli.run()
