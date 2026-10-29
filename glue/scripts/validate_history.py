"""Glue 5.0 driver for the installed, released Athena validation runtime."""

from ppsc_ops_data_quality.glue import main

if __name__ == "__main__":
    # Glue marks nonzero exits FAILED; published evidence distinguishes data/errors.
    raise SystemExit(main())
