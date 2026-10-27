"""Validate configured Athena history and publish native GX evidence."""

import argparse
import sys
from pathlib import Path

from ppsc_ops_data_quality.account_to_survey_results.configuration import (
    load_validation_configuration,
)
from ppsc_ops_data_quality.account_to_survey_results.validation import run_validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help=__doc__)
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        configuration = load_validation_configuration(args.config)
        outcome = run_validation(configuration, run_directory=args.run_dir)
    except Exception as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(outcome.model_dump_json(indent=2))
    return outcome.exit_code
