# Acceptance and remaining evidence

Review date: October 20, 2026.

## Current status

| Gate | Status |
| --- | --- |
| Locked Python 3.12 installation, local tests, and dry run | Verified locally October 20, 2026: 71 tests passed, Ruff lint passed, and 21 Python files passed the format check. The documented dry run completed successfully. |
| Live GX/PyAthena/Athena compatibility | Pending AWS credentials, workgroup access, and a controlled live run. |
| Live Account/ACR selection and schema | Pending actual bindings, verified physical types, temporal convention, and a completed delivery. |
| Combined operational and graph evidence | Pending. [Sources](sources.md) identifies a real job check and native Flow evidence; the saved graph subset and rule applicability still need review. |
| Full history checks | Deferred until the temporal/version/deletion contract is confirmed. There is no history CLI option yet. |

The current lock resolves GX 1.24.0, Ibis 12.0.0, PyAthena 4.2.0, and SQLAlchemy
2.1.5. Record the installed versions with every acceptance run. Local DuckDB and
SQLite checks establish their tested behavior; they do not establish Athena
compatibility. GX lists Athena and AWS Glue among integrations without an ongoing
compatibility guarantee: [GX compatibility reference][gx-compatibility].

## Local acceptance

From a fresh checkout:

```sh
uv sync --locked
uv run poe check
uv run poe validate \
  --config params.yaml \
  --as-of 2026-10-15 \
  --lake-as-of 2026-10-17T12:00:00Z \
  --dry-run
```

Check the generated directory: preview mode is explicit; SQL retains physical
snapshot clauses; suites retain rule descriptions/evidence; no validation result
or Data Docs is represented as a live result. A subsequent invocation must create
a different run directory.

CI performs this same local path on synthetic data without AWS credentials. It
does not publish run artifacts. Action releases were checked against the official
repositories: [checkout v7.0.1][checkout], [setup-python v7.0.0][setup-python],
[setup-uv v10.3.0][setup-uv], and [uv 0.12.23][uv-release].

## Controlled live GX gate

Set real Athena connection settings in ignored `params.local.yaml` and select an
authorized AWS profile/role. These probes require Athena and the configured query
result location, but use synthetic read-only SELECTs instead of participant data.
Run them before debugging Ibis or real table checks.

The gate must show:

| Case | Required observation |
| --- | --- |
| Passing query | Native row-count and `UnexpectedRowsExpectation` both pass. |
| Intentional data failure | Both expectations return a validation failure without a query exception. |
| 205 unexpected rows | Total failure count is 205; the diagnostic sample is bounded at 200. |
| Invalid column query | A query exception is recorded as an execution error, distinguishable from a data failure. |

Run this from the repository root:

```sh
uv run --locked python - <<'PY'
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import great_expectations as gx

from ppsc_ops_data_quality.athena import sqlalchemy_url
from ppsc_ops_data_quality.config import load_config, validate_config
from ppsc_ops_data_quality.run import code_identity, run_validations, write_json

config = load_config("params.local.yaml")
validate_config(config, live=True, discovery=True)
output = Path("build/acceptance") / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
output.mkdir(parents=True)

many_rows = "SELECT x FROM (VALUES " + ",".join(["(-1)"] * 205) + ") AS fixture(x)"
unexpected = "SELECT * FROM {batch} WHERE x < 0"
cases = [
    ("pass", "SELECT 1 AS x", 1, unexpected, "pass", 0),
    ("data_failure", "SELECT -1 AS x", 2, unexpected, "fail", 1),
    ("bounded_sample", many_rows, 205, unexpected, "fail", 205),
    ("query_error", "SELECT 1 AS x", 1,
     "SELECT missing_column FROM {batch}", "error", None),
]

queries = []
for name, query, row_count, unexpected_query, expected, failures in cases:
    suite = gx.ExpectationSuite(
        name=name,
        expectations=[
            gx.expectations.ExpectTableRowCountToEqual(
                value=row_count, catch_exceptions=True,
                meta={"rule_id": f"{name}.native_count"}),
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=unexpected_query, catch_exceptions=True,
                meta={"rule_id": f"{name}.unexpected"}),
        ],
    )
    queries.append((name, query, suite))

packages = ("great-expectations", "ibis-framework", "PyAthena", "SQLAlchemy")
write_json(output / "run.json", {
    "mode": "controlled_live_acceptance",
    "code": code_identity(),
    "python": sys.version,
    "versions": {name: version(name) for name in packages},
    "config": config.as_dict(),
    "queries": {name: query for name, query, suite in queries},
})
summary = run_validations(
    queries, sqlalchemy_url(config).render_as_string(hide_password=False), output
)
write_json(output / "summary.json", summary)
assert not summary["errors"], summary["errors"]
assets = {asset["asset"]: asset for asset in summary["assets"]}

for name, query, row_count, unexpected_query, expected, failures in cases:
    asset = assets[name]
    assert asset["status"] == expected, (name, expected, asset)
    if expected == "error":
        messages = asset["errors"] + [
            message for rule in asset["rules"] for message in rule["errors"]
        ]
        assert "missing_column" in "\n".join(messages), messages
    else:
        rules = {rule["rule_id"]: rule for rule in asset["rules"]}
        native = rules[f"{name}.native_count"]
        custom = rules[f"{name}.unexpected"]
        assert native["status"] == ("fail" if name == "data_failure" else "pass")
        assert custom["unexpected_count"] == failures
        assert custom["sample_count"] == min(failures, 200)
    print(name, asset["status"])

print("Controlled live gate passed; evidence:", output)
PY
```

These cases use the same validation and reporting function as the pilot. The
combined summary deliberately has status `error` because the last query is
invalid; the gate succeeds only when each expected case and count is verified.
Inspect the saved native results and Data Docs as well as the command's success.
A connection/setup error blocks the gate. An unsupported metric is an execution
error, never evidence that the corresponding data passed.

Allow roughly 60–90 minutes for initial compatibility diagnosis. If only the
unexpected-row path fails, investigate one bounded fallback: make the violations
SELECT the query asset, apply native `ExpectTableRowCountToEqual(0)`, and retrieve
a separately bounded diagnostic sample. Verify full counts and document the
difference before adopting it. The current implementation does not select this
fallback automatically.

If basic SQL datasource execution fails, retain the minimal reproduction and exact
versions, then keep live acceptance pending. Do not build a private GX
compatibility layer to make the first demonstration appear complete.

## Pilot acceptance on real lake tables

1. Discover and inspect sources using the README commands. Confirm required
   columns and physical types, and inspect available Iceberg snapshot metadata.
2. Confirm effective interval boundaries and set
   `interval_convention_confirmed: true` for an as-of run. Confirm deletion and
   parent-population assumptions. Record completed-delivery evidence separately
   from the snapshot timestamp.
3. Run the pilot on that selection. Review Account and ACR state checks and the
   relationship findings at child-row grain. Verify the SQL uses the intended
   physical bindings and snapshot on both sources.
4. Inspect native results, summaries, and Data Docs. Confirm that configuration
   and query errors produce exit code 2, data failures produce 1, and a successful
   validation produces 0.
5. Record the commit, installed versions, configuration, selected timestamps,
   completion evidence, and result directory in the private acceptance record.
   Keep actual bindings and record-level output outside Git and public CI.

A meaningful combined-evidence demonstration additionally requires promoting an
accepted operational rule with reviewed graph/native pointers and useful fixtures;
the initial structural pilot alone does not complete that milestone.

[gx-compatibility]: https://docs.greatexpectations.io/docs/help/compatibility_reference/
[checkout]: https://github.com/actions/checkout/releases/tag/v7.0.1
[setup-python]: https://github.com/actions/setup-python/releases/tag/v7.0.0
[setup-uv]: https://github.com/astral-sh/setup-uv/releases/tag/v10.3.0
[uv-release]: https://github.com/astral-sh/uv/releases/tag/0.12.23
