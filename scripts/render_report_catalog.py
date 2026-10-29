"""Bind the checked-in report DDL to one runtime configuration; no AWS calls."""

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from ppsc_ops_data_quality.io import load_yaml


def render_report_catalog(*, config: Path, database: str, first_run_date: str, output: Path):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", database):
        raise ValueError("Use an unquoted Glue database identifier")
    date.fromisoformat(first_run_date)
    settings = load_yaml(config)
    athena = settings["athena"]
    reports = settings["reports"]["s3_uri"].rstrip("/")
    uri = urlsplit(reports)
    if uri.scheme != "s3" or not uri.netloc or uri.query or uri.fragment or "'" in reports:
        raise ValueError("Reports must use an S3 prefix without SQL quotes")
    template = "\n".join(
        line
        for line in Path("sql/validation_reports_catalog.sql").read_text().splitlines()
        if not line.lstrip().startswith("--")
    )
    sql = template.replace("s3://REPLACE_WITH_REPORTS_BUCKET/ppsc-data-quality", reports)
    sql = sql.replace("REPLACE_WITH_FIRST_RUN_DATE", first_run_date)
    if "REPLACE_WITH_" in sql or "REPLACE_WITH_" in json.dumps(athena):
        raise ValueError("Replace catalog and Athena configuration placeholders")
    # The maintained template contains exactly two DDL statements, not authored checks.
    statements = [part.strip() + ";\n" for part in sql.split(";") if part.strip()]
    if len(statements) != 2:
        raise ValueError("Expected two report catalog DDL statements")
    output.mkdir(parents=True, exist_ok=False)
    for index, statement in enumerate(statements):
        (output / f"{index:02}.sql").write_text(statement)
    (output / "target.json").write_text(
        json.dumps(
            {
                "region": athena["region"],
                "work_group": athena["work_group"],
                "context": {
                    "Database": database,
                    "Catalog": athena.get("catalog_name", "AwsDataCatalog"),
                },
                "results": {"OutputLocation": athena["s3_staging_dir"]},
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--first-run-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    render_report_catalog(**vars(parser.parse_args()))
