# PPSC design examples

**Preferred convention:** Pydantic input contracts, explicit functions, and Pydantic output contracts for structured public results.

**Source:** [ppsc-nioccs PR #2](https://github.com/mbkranz/ppsc-nioccs/pull/2), repository state at commit [`4f93663303ce7f5a2cb94ab4ef9ad13c353d5602`](https://github.com/mbkranz/ppsc-nioccs/commit/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602). Source excerpts reviewed October 22, 2026.

These examples come from the PR snapshot, including changes before its final commit. Exact source excerpts and proposed adaptations are labeled separately. Apply the demonstrated decision using the current project's types and dependencies; the NIOCCS package is not a dependency of this skill.

## Contents

- [What the reference actually implements](#what-the-reference-actually-implements)
- [Authored model and explicit transformation](#an-authored-model-and-explicit-transformation)
- [Configuration validation and computation](#configuration-validation-and-computation-have-different-jobs)
- [Pydantic input, explicit writer, Pydantic receipt](#pydantic-input-explicit-writer-pydantic-receipt)
- [Parse, check compatibility, then execute](#parse-check-compatibility-then-execute)
- [Explicit workflow order and visible data handoffs](#explicit-workflow-order-and-visible-data-handoffs)
- [Explicit dependencies and reusable evidence](#explicit-dependencies-and-reusable-evidence)
- [What to adopt selectively](#what-to-adopt-selectively)

## What the reference actually implements

The snapshot demonstrates **Pydantic authored input → explicit functions → structured results**. Pydantic output models and consistently annotated public signatures are the desired refinement, not a description of every existing function.

| Contract or return value | Actual representation at this commit |
| --- | --- |
| `Operation`, `ColumnOperation`, `OperationPlan` | Pydantic models |
| `ReplaceColumnValuesExactly`, `DetectColumnValuesPII`, `SummarizeRowsPIIEvidence` | Pydantic operation models |
| `ReadTable`, `WriteTable`, `RequestNioccsCodes`, `BoundaryPlan` | Pydantic models |
| `CompiledPlan`, `CallBatchResult`, `CleaningResult` | Dataclasses |
| `TableReadResult`, `ArtifactReceipt`, `FileFlowResult` | Dataclasses |
| PII detection and summary computations | Lists/dictionaries |
| PII evidence condition | `bool | None` |
| Column expression computations | Narwhals expressions |

Some handlers are unannotated in the source. Exact excerpts retain those signatures. The proposed writer in the writer example adds a Pydantic result and annotations deliberately.

Primary references: [runtime/models.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/runtime/models.py), [io/write_table.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/io/write_table.py), and [io/boundaries.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/io/boundaries.py).

## An authored model and explicit transformation

**Use this example when:** implementing a configurable transformation or an operation selected by authored rules.

The shared authoring base owns configuration validation and serialization:


```python
class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    type: ClassVar[str]
    meta: dict[str, JsonValue] = Field(default_factory=dict)

    def to_spec(self) -> dict:
        return {
            "type": self.type,
            "kwargs": self.model_dump(mode="json", exclude={"meta"}),
            "meta": self.meta,
        }
```


```python
class ColumnOperation(Operation):
    column: str = Field(min_length=1)
```

The operation-specific model declares the meaningful choices:


```python
class ReplaceColumnValuesExactly(ColumnOperation):
    type = "replace_column_values_exactly"
    original_value: Scalar
    replacement: Scalar
    match_scope: Literal["cell", "cell_or_token"] = "cell"
```

The underlying expression function accepts only the values it needs:


```python
def replace_exact(column, original_value, replacement):
    return set_where(column, equal(column, original_value), replacement)
```

The execution adapter connects that function to the dataframe and authored instruction:


```python
def apply(frame, rule):
    if rule.match_scope != "cell":
        return replace_tokens(frame, rule.column, rule.original_value, rule.replacement)
    return frame.with_columns(
        replace_exact(rule.column, rule.original_value, rule.replacement).alias(rule.column)
    )
```

**What to imitate**

The model describes a valid request; the semantic function describes the transformation; the adapter supplies the execution representation. The semantic function has no dependency on the registry, workflow, or full runtime context. The relevant pieces are colocated in one module.

`Operation.to_spec()` derives serialized kwargs from the model. Future operations should not maintain a second handwritten dictionary of parameters or defaults. In this snapshot, `ColumnOperation` supplies the column field and `Scalar` uses strict scalar types plus `None`.

**Limits of the lesson**

The expression/dataframe outputs are appropriate native values. They do not need a Pydantic wrapper. Token replacement is explicitly pandas-only in this snapshot. `frozen=True` prevents field reassignment; it does not make all nested values deeply immutable.

**Source:** [replace_column_values_exactly.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/cleaning/transforms/replace_column_values_exactly.py) and [runtime/models.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/runtime/models.py).

## Configuration validation and computation have different jobs

**Use this example when:** configuration has cross-field invariants and the operation produces facts that other rules will interpret.

The input model owns relationships among its configuration fields:


```python
class SummarizeRowsPIIEvidence(Operation):
    type = "summarize_rows_pii_evidence"
    text_columns: list[StrictStr] = Field(min_length=1)
    detector_prefixes: list[StrictStr] = Field(min_length=1)
    entity_types: list[StrictStr] = Field(min_length=1)
    threshold: float = Field(ge=0, le=1)
    output_prefix: str = Field(default="pii", min_length=1)

    @model_validator(mode="after")
    def validate_columns(self):
        if len(self.text_columns) != len(self.detector_prefixes):
            raise ValueError("Each text column needs its detector evidence prefix")
        for values in (self.text_columns, self.detector_prefixes, self.entity_types):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError("Column, evidence, and entity names must be nonempty and unique")
        return self
```

The computation is a separate ordinary function:


```python
def compute(texts, detector_results, *, entity_types, threshold):
    conditions = [
        contains_pii(text, evidence, entity_types=entity_types, threshold=threshold)
        for text, evidence in zip(texts, detector_results, strict=True)
    ]
    complete = all(value is not None for value in conditions)
    return {
        "status": "complete" if complete else "incomplete",
        "detected": any(value is True for value in conditions) if complete else None,
        "input_hash": values_hash(texts),
    }
```

**What to imitate**

The model checks nonempty and unique names, aligned text/evidence columns, and a bounded threshold. The computation reports completeness, detection, and input identity. It does not decide quarantine or outbound eligibility. Its explicit arguments allow reuse outside the cleaning runtime.

**Pydantic-output refinement**

The returned dictionary is a useful candidate for a result model because its fields have a stable meaning and a relationship to one another. A future `PIIEvidenceSummary` could enforce that complete evidence has a Boolean detection result and incomplete evidence has `detected=None`. This type is proposed; it is not present in the reference commit. Preserve the existing unknown-state semantics when introducing it.

Keep tiny predicates and expression builders direct. The PR's metric conventions expressly distinguish those computations from operation handlers.

**Sources:** [rows_pii_evidence_summary.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/metrics/rows/rows_pii_evidence_summary.py) and [metric-family-conventions.md](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/docs/specs/metric-family-conventions.md).

## Pydantic input, explicit writer, Pydantic receipt

**Use this example when:** an operation performs a side effect and should return a validated, serializable description of what it produced.

### Existing implementation

The source input model is:


```python
class WriteTable(Operation):
    type = "write_table"
    uri: str = Field(min_length=1)
    format: Literal["csv", "json", "jsonl"]
    write_mode: Literal["error", "overwrite"]
```

The source function and named output are:


```python
def write(operation, *, context, frame):
    from .providers.filesystem import local_path, table_bytes, write_bytes

    data = table_bytes(frame, format=operation.format)
    digest = write_bytes(
        local_path(operation.uri, context.root), data, write_mode=operation.write_mode
    )
    return ArtifactReceipt(operation.uri, digest, len(frame), operation.format)
```


```python
@dataclass(frozen=True)
class ArtifactReceipt:
    uri: str
    sha256: str
    rows: int
    format: str
```

This already provides a clear request/result pair: explicit destination, format, and overwrite behavior; a returned URI, hash, row count, and format. Constructing `WriteTable` does not write anything.

### Proposed adaptation for the preferred convention

The following is an adapted, pandas-specific example. It is not copied from the commit and is not a patch to the existing runtime handler. It uses the source's `WriteTable` and filesystem functions, gives the public function a descriptive name and explicit dependency, and changes the receipt to Pydantic.


```python
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from ppsc_nioccs_coding_for_eeoh.io.providers.filesystem import (
    local_path,
    table_bytes,
    write_bytes,
)
from ppsc_nioccs_coding_for_eeoh.io.write_table import WriteTable


class ArtifactReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    uri: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rows: int = Field(ge=0)
    format: Literal["csv", "json", "jsonl"]


def write_table(
    request: WriteTable,
    frame: pd.DataFrame,
    *,
    root: Path,
) -> ArtifactReceipt:
    path = local_path(request.uri, root)
    data = table_bytes(frame, format=request.format)
    digest = write_bytes(path, data, write_mode=request.write_mode)

    return ArtifactReceipt(
        uri=request.uri,
        sha256=digest,
        rows=len(frame),
        format=request.format,
    )
```

**What to imitate**

- A public request has a named, validated model.
- Runtime data stays in its native dataframe representation.
- The function advertises its dependency on a filesystem root.
- The implementation follows a visible sequence: resolve path, serialize, write, construct receipt.
- The return is a named Pydantic object. Returning an arbitrary dictionary with a return annotation would not perform result validation.
- Serialized receipts can be obtained from the model without defining a parallel result schema.

The narrower `root` argument is a proposed standalone API choice. Inside the existing operation runtime, retaining its standard `context` adapter interface can be appropriate. Do not add a second wrapper unless it is actually needed to connect these two interfaces.

Use the backend's real type in each project. This example selects pandas explicitly; it does not claim the original writer is pandas-only. Pydantic validates the receipt's fields, not the dataframe's schema or whether an external artifact still exists.

**Limits of the example:** the reference provider implements local CSV, JSON, and JSONL. This example does not add S3, Parquet, distributed writing, or transaction guarantees. Exceptions from the write propagate. The adapted code has been syntax-checked, not integration-tested.

**Sources:** [io/write_table.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/io/write_table.py) and [io/providers/filesystem.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/io/providers/filesystem.py).

## Parse, check compatibility, then execute

**Use this example when:** syntactically valid configuration can still be invalid for a schema, backend, or execution environment.

These are exact signatures from the engine, with bodies omitted:


```python
def parse_operations(document: Mapping) -> OperationPlan:
    ...
```


```python
def compile_operations(
    plan: OperationPlan,
    *,
    schema: Mapping[str, object],
    backend: str,
    mode: str = "offline",
    pipeline: str | None = None,
) -> CompiledPlan:
    ...
```


```python
def execute_operations(
    frame, plan: CompiledPlan, *, context: ExecutionContext | None = None
) -> CleaningResult:
    ...
```

**What to imitate**

Pydantic validates authored configuration. Compilation checks column dependencies, key protection, supported operations/backends/modes, and output collisions. Execution performs the transformation and returns named results. A valid model is not proof that its referenced columns exist or that a provider is available.

The compiler snapshots the authored plan through serialization and parsing. This is distinct from the model's `frozen` setting. Client/resource preparation is explicit and separate; it can include local resource reads and connection checks.

`CompiledPlan` and `CleaningResult` are dataclasses in this snapshot. Preserve that source fact. Use Pydantic for an output contract when it provides useful validation/serialization; do not force native frames or live clients into a JSON-oriented result just for uniformity.

The parse/compile/execute sequence is warranted by this runtime's real authored operations and preflight requirements. A small standalone transformation may need only model construction and a function call.

**Source:** [runtime/engine.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/runtime/engine.py).

## Explicit workflow order and visible data handoffs

**Use this example when:** multiple stages must run in a known order and each stage's output controls the next stage's input.


```python
def run_screening_and_coding(frame, plan, *, context):
    phases = _prepare_screening_and_coding(frame, plan, context)
    screened = execute_operations(frame, phases[0], context=context)
    coded = execute_operations(screened.partitions.retained, phases[1], context=context)
    return screened, coded
```

The workflow visibly passes `screened.partitions.retained` to coding. The optional checkpoint variant similarly passes `validated.partitions.retained`, after checking the stable-key contract. Both phases are preflighted/prepared before service requests begin.

**What to imitate**

Name intermediate values for their role. Show which result is passed onward. Keep application sequencing in a workflow function. Keep the rule engine responsible for execution mechanics, not implicit application scheduling.

The current workflow returns a tuple, not a Pydantic model. A named workflow result is a possible refinement when callers need one. For persisted summaries, use a Pydantic contract of meaningful stage metadata or receipts; retain native dataframes in appropriate runtime containers. Do not create placeholder empty result types merely to satisfy a pattern.

The separate `run_file_flow` boundary makes input reads, selected phases, and output writes visible, returning a named `FileFlowResult` dataclass. Multiple writes are not transactional.

**Sources:** [flows/eeoh.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/flows/eeoh.py) and [io/boundaries.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/io/boundaries.py).

## Explicit dependencies and reusable evidence

**Use this example when:** external work produces evidence that several consumers can interpret.

Actual scalar signatures, with bodies omitted:


```python
def compute(text, *, detector, language="en"):
    ...
```


```python
def normalize_pii_entities(response, *, text_length):
    ...
```


```python
def condition(text, evidence, *, entity_types, threshold) -> bool | None:
    ...
```

`compute` receives the detector callable explicitly. It can perform external I/O, while `condition` interprets materialized evidence without another detector request. The runtime adapter owns client binding, request budgeting, stable keys, hashes, and keyed error outcomes. Instruction construction performs no request.

The condition returns `None` for incomplete or stale evidence. That result must not be collapsed to `False`, which would incorrectly communicate a completed negative finding. A Pydantic evidence result should preserve status, provenance, and uncertainty when introduced.

A dependency-injected function is not necessarily pure. The actual provider currently expects a Comprehend-shaped response; support for other response shapes requires an explicit adapter.

**Sources:** [column_values_pii_entities.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/metrics/column_values/column_values_pii_entities.py), [column_values_contain_pii.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/metrics/column_values/column_values_contain_pii.py), and [tests/test_shared_metrics.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/tests/test_shared_metrics.py).

## What to adopt selectively

| Reference design | Transferable decision | Boundary |
| --- | --- | --- |
| Co-located operation module | Keep a small request, implementation, result, and definition together | Do not create four separate files for every tiny operation |
| Explicit registry assembly | List real operation definitions and reject duplicate names | Do not introduce a registry for a fixed standalone function |
| Shared `compute` / `condition` functions | Pass explicit values and give the function a clear local role | Use qualified imports or descriptive aliases when those short names become ambiguous |
| Pydantic input | Keep parameters, validation, schema, and serialization in one definition | Do not perform network or storage work in validators |
| Proposed Pydantic output | Validate meaningful structured receipts/evidence at a public boundary | Native expressions, frames, and scalar helpers can remain native |
| Separate preflight | Find incompatible later steps before external work begins | Avoid adding a compiler layer to trivial workflows |
| Named status/evidence | Preserve failure, incompleteness, provenance, and result meaning | A successful configuration parse is not a successful execution |

The explicit registry in [runtime/registry.py](https://github.com/mbkranz/ppsc-nioccs/blob/4f93663303ce7f5a2cb94ab4ef9ad13c353d5602/src/ppsc_nioccs_coding_for_eeoh/runtime/registry.py) is justified by the existing authored operation set and common execution requirements. The definition stores direct callable references. It does not use scanning or decorator-driven discovery.

Unfinished casting, mapping, and preferred-record contracts are not examples of completed implementations. The separate WD-FAB Spark validation slice does not establish Spark support for the cleaning runtime. Choose the implemented examples above for teaching style.

## Source and example verification

The source excerpts were checked against the pinned commit when this reference was prepared. The Python blocks were syntax-checked. The adapted writer is a proposed, pandas-specific example; it has not been integrated into or tested against the NIOCCS runtime. Evaluate any adaptation within the target repository's current dependencies and execution contract.
