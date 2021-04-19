#!/usr/bin/env python
from climates import Climate, Command
from subprocess import run
import sys


def sh(cmd):
    """Run command, exit if returncode is non-zero."""
    proc = run(cmd, shell=True)
    if proc.returncode != 0:
        print('> ', cmd, file=sys.stderr)
        sys.exit(proc.returncode)


def init():
    """Initialize repository."""
    sh("pip install --upgrade pip wheel")
    sh("pip install -r requirements.txt")


def dist():
    """Make release."""
    sh("python setup.py sdist bdist_wheel")
    sh("twine upload dist/*")


def lint():
    """Run linters."""
    sh("flake8 climates --max-complexity=8")
    sh("pylint climates --fail-under=10 -d E1136")
    sh("mypy -p climates")


def test():
    """Run tests."""
    sh("pytest --cov=climates --cov-report=term-missing --cov-fail-under=99 "
       "--cov-branch -x")


if __name__ == "__main__":
    cli = Climate("scripts.py", description="Dev scripts.")
    for func in (init, dist, lint, test):
        cli.add(Command(func, result=None))
    cli.run()
