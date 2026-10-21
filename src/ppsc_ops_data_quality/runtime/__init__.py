"""Runtime adapters prepare native GX definitions; the runner executes them.

Athena compiles Ibis to a SQL Query Asset. DuckDB executes Ibis locally and
supplies a bounded pandas DataFrame to GX. Import adapters explicitly; there is
no engine registry, custom ValidationDefinition class or automatic backend choice.
TODO: authored SQL-file execution and metadata/comment conventions are tracked
in runtime/TODO.md; the current adapters do not read SQL files.
"""

from .runner import run_validations

__all__ = ["run_validations"]
