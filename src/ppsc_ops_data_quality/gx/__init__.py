"""Load one failing-row SELECT per SQL file beside its owning suite module."""

from importlib.resources import files

import great_expectations as gx
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from sqlglot.optimizer.scope import traverse_scope


def sql_expectations(subject: str, relations: dict[str, str] | None = None) -> list:
    """A filename is the rule ID; leading comments explain the check in Data Docs.

    {batch} names the selected subject population. Named *_state relations are
    supplied by the runner, with the same effective and physical time selections.
    """
    checks = sorted(files(__package__).joinpath(subject).iterdir(), key=lambda p: p.name)
    expectations = []
    for path in checks:
        if not path.name.endswith(".sql"):
            continue
        text = path.read_text(encoding="utf-8")
        label = f"{subject}/{path.name}"
        try:
            statements = [
                q
                for q in sqlglot.parse(text.replace("{batch}", "__dq_batch"), read="athena")
                if q is not None
            ]
        except ParseError as error:
            raise ValueError(f"{label}: {error}") from error
        if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.SetOperation)):
            raise ValueError(f"{label}: expected one SELECT returning failing rows")
        query = statements[0]
        if any(query.find_all(exp.DML, exp.DDL, exp.Into)):
            raise ValueError(f"{label}: checks must be read-only")
        if query.args.get("limit") or query.args.get("offset"):
            raise ValueError(f"{label}: omit LIMIT/OFFSET so failure counts remain complete")
        used = set()
        for scope in traverse_scope(query):
            for _, source in scope.sources.items():
                if isinstance(source, exp.Table):
                    if source.db or source.catalog:
                        raise ValueError(
                            f"{label}: use selected logical populations, not physical tables"
                        )
                    used.add(source.name)
        unknown = used - {"__dq_batch"} - (relations or {}).keys()
        if unknown:
            raise ValueError(f"{label}: unknown populations: {', '.join(sorted(unknown))}")
        if not used:
            raise ValueError(f"{label}: reference {{batch}} or a selected population")
        for name in sorted(used - {"__dq_batch"}):
            query = query.with_(name, as_=sqlglot.parse_one(relations[name], read="athena"))
        for table in query.find_all(exp.Table):
            if table.name == "__dq_batch":
                table.set("this", exp.Identifier(this="{batch}", quoted=False))
        sql = query.sql(dialect="athena")
        description = "\n".join(line[3:] for line in text.splitlines() if line.startswith("-- "))
        expectations.append(
            gx.expectations.UnexpectedRowsExpectation(
                unexpected_rows_query=sql,
                description=description or path.name,
                catch_exceptions=True,
                meta={
                    "rule_id": f"{subject}.{path.name[:-4]}",
                    "sql_file": f"gx/{label}",
                    "rationale": description or path.name,
                    "sources": [{"path": f"gx/{label}"}, {"path": "docs/sources.md"}],
                    "assumptions": [
                        "The runner supplies the declared state and physical snapshot."
                    ],
                    "investigation": "Read the SQL comments and inspect the failing-row sample.",
                    "violation_grain": "row returned by the SQL check",
                },
            )
        )
    if not expectations:
        raise ValueError(f"{subject}: no SQL checks found")
    return expectations
