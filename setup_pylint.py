#!/usr/bin/env python

import pathlib
import sys

import pylint.lint


def main() -> int:
    rcfile = pathlib.Path(__file__).parent / ".pylintrc"
    args = [f"--rcfile={rcfile}"] + sys.argv[1:]

    # Pylint >=2.5 uses do_exit, older releases used exit
    try:
        # new API
        run = pylint.lint.Run(args, do_exit=False)  # type: ignore[call-arg] # pylint: disable=unexpected-keyword-arg
    except TypeError:
        # old API
        run = pylint.lint.Run(args, exit=False)  # type: ignore[call-arg] # pylint: disable=unexpected-keyword-arg

    return run.linter.msg_status  # 0 = success


if __name__ == "__main__":
    raise SystemExit(main())
