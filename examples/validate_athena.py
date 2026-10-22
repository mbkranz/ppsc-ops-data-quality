"""Compatibility example; prefer the installed `ppsc-dq validate` command."""

import sys

from ppsc_ops_data_quality.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["validate", *sys.argv[1:]]))
