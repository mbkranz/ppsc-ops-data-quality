"""One native structural check plus the subject's failing-row SQL files."""

import re
from importlib.resources import files

import great_expectations as gx
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope


def check_query(sql: str, relations: dict[str, str]) -> str:
    """Bind only table references; local CTEs, aliases, and literals keep their meaning."""
    statements = [query for query in sqlglot.parse(sql, read="athena") if query is not None]
    if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.SetOperation)):
        raise ValueError("expected one SELECT returning failing rows")
    query = statements[0]
    if any(query.find_all(exp.DML, exp.DDL, exp.Into)):
        raise ValueError("checks must be read-only")
    if query.args.get("limit") or query.args.get("offset"):
        raise ValueError("omit LIMIT/OFFSET so failure counts remain complete")

    # Choose a marker absent from all authored SQL, including literals and bindings.
    # This lets us escape literal braces for GX without altering their SQL values.
    marker = "__gx_batch__"
    while marker in sql or any(marker in source for source in relations.values()):
        marker += "_"
    sources = {**relations, "batch": f"SELECT * FROM {marker}"}
    referenced = False
    for scope in traverse_scope(query):
        for table, source in scope.selected_sources.values():
            if not isinstance(source, exp.Table):  # A local CTE or derived table.
                continue
            if source.db or source.catalog or source.name not in sources:
                raise ValueError(
                    f"unknown population {source.sql()}; use batch or a selected state"
                )
            selected = sqlglot.parse_one(sources[source.name], read="athena")
            table.replace(selected.subquery(alias=table.alias_or_name))
            referenced = True
    if not referenced:
        raise ValueError("reference batch or a selected population")
    compiled = query.sql(dialect="athena", pretty=True, comments=False)
    # GX uses str.format, then SQLAlchemy text(); keep SQL literals literal at both boundaries.
    return (
        compiled.replace("{", "{{")
        .replace("}", "}}")
        .replace(":", r"\:")
        .replace(marker, "{batch}")
    )


def sql_expectations(subject: str, relations: dict[str, str] | None = None) -> list:
    """Discover sorted SQL files; filenames identify checks and opening comments explain them."""
    expectations = []
    for path in sorted(files(__package__).joinpath(subject).iterdir(), key=lambda p: p.name):
        if not path.is_file() or not path.name.endswith(".sql"):
            continue
        text = path.read_text(encoding="utf-8")
        label = f"gx/{subject}/{path.name}"
        if not re.fullmatch(r"expect_[a-z][a-z0-9_]*\.sql", path.name):
            raise ValueError(f"{label}: name SQL files after expectations: expect_<name>.sql")
        try:
            query = check_query(text, relations or {})
        except (SqlglotError, ValueError) as error:
            raise ValueError(f"{label}: {error}") from error
        comments = []
        for line in text.strip().splitlines():
            if not line.lstrip().startswith("--"):
                break
            comments.append(line.lstrip()[2:].strip())
        expectations.append(
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=query,
                description="\n".join(comments) or path.name,
                catch_exceptions=True,
                meta={
                    "expectation_name": path.name[:-4],
                    "rule_id": f"{subject}.{path.name[:-4]}",
                    "sql_file": label,
                },
            )
        )
    if not expectations:
        raise ValueError(f"{subject}: no SQL checks found")
    return expectations


def make_suite(
    subject: str,
    columns: list[str],
    relations: dict[str, str] | None = None,
    *,
    assumptions: tuple[str, ...] = (),
) -> gx.ExpectationSuite:
    """Keep shared population evidence on the suite and rule-specific evidence in SQL."""
    return gx.ExpectationSuite(
        name=subject,
        meta={
            "sources": [{"kind": "pilot_contract", "path": "docs/sources.md"}],
            "assumptions": [
                f"The batch represents one declared {subject} population.",
                *assumptions,
            ],
        },
        expectations=[
            gx.expectations.ExpectTableColumnsToMatchSet(
                column_set=columns,
                exact_match=False,
                description="The selected population includes the columns its checks require.",
                meta={"rule_id": f"{subject}.columns"},
            ),
            *sql_expectations(subject, relations),
        ],
    )
