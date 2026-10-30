#!/usr/bin/env python

import pathlib
import sys

import pylint.lint


def main() -> int:
    rcfile = pathlib.Path(__file__).parent / ".pylintrc"
    args = [f"--rcfile={rcfile}"] + sys.argv[1:]

    # exit=False returns instead of calling sys.exit (pylint >=2.5, pinned in requirements.txt)
    run = pylint.lint.Run(args, exit=False)

    return run.linter.msg_status  # 0 = success


if __name__ == "__main__":
    raise SystemExit(main())
