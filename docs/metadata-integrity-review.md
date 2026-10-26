> Historical pre-migration review. The active v2 boundary is documented in [metadata-compiler.md](metadata-compiler.md).

# Verified compilation snapshot

Follow-up to the cached-metadata finding in the October 24 Spaces plan. The
baseline reproduction changed a native assignment to NULL, changed compiled SQL,
and retained an accepted receipt. The regression now passes.

The private cache holds serialized verified inputs, the Flow request, and the
installed compiler version. Every public input/request load returns a fresh
parse. Lineage and query construction use the same snapshot. ODCS aliases and
authored presence are preserved with `by_alias=True, exclude_unset=True`.

Receipt creation rechecks artifact hashes, the manifest, configuration, and
compiler version. `CompilationReceipt` adds `flow_request_sha256` to the existing
producer receipt. Existing `projection-inputs/v1` handoffs remain unchanged;
unchanged verified bytes remain usable. Receipt metadata gains one additive field.

PPSC review: structured evidence is validated; configuration parsing has no
effects; query functions still return native Ibis expressions; operational work
remains in Poe and DVC. No additional runtime, registry, or acquisition path was
introduced. The immutable representation is internal, not a second source model.

Executed checks: 16 focused integrity/compiler regressions; query compilation;
native synthetic GX (28 Flow and 25 rollup checks); real four-stage DVC reproduction;
index-free installed-bundle compilation and native validation smoke. Python
3.11.17, uv 0.12.23, pip 25.3, GX 1.24.0, Ibis 12.0.0, DuckDB 2.0.0.

The initial broader run passed 170 tests; its remaining failures were missing
local Graphviz and a missing prepared `.venv-release` executable. These are
environment prerequisites, not evidence of live Athena/Glue acceptance.
