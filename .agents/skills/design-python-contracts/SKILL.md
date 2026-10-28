---
name: design-python-contracts
description: Design, implement, refactor, and review Python functions and modules with Pydantic public contracts, explicit dependencies, and visible workflow composition. Use for new application operations, substantial Python refactoring, or reviews asking for clean, simple, explicit code, especially in PPSC repositories. Apply only the relevant checks to a small helper; skip for prose-only, formatting-only, or non-Python tasks. Preserve established framework interfaces and compatibility.
---

# Design Python Contracts

Use validated request models, ordinary named functions, and validated result models at structured application boundaries. Keep computations and workflow handoffs easy to follow. Apply this convention to new or deliberately revised interfaces within the repository's existing execution model.

## Establish the contract

1. Read applicable repository instructions, the target module, its callers, and the nearest relevant checks. Identify the installed Pydantic version and existing model and error conventions. Prefer established dependencies and public interfaces.
2. Identify the operation's data inputs, configuration, runtime dependencies, effects, result, and meaningful failure or incomplete states. Resolve routine choices from the code and task; ask only when an unresolved choice materially changes behavior.
3. Draft the request model, public function signature, result shape, and one representative call before filling in the implementation. For a small change, do this within the implementation; create a separate design document only when requested or required locally.
4. Read the matching section of [PPSC design examples](references/ppsc-design-examples.md). Use the bundled excerpts directly; consult the pinned source when a specific uncertainty requires more context. Transfer the annotated design decision to the current project.

## Select the matching example

| Work | Reference section | Decision to apply |
| --- | --- | --- |
| Configurable transformation | Authored model and explicit transformation | Let the adapter extract model fields for a narrow computation. |
| Related configuration fields | Configuration validation and computation | Validate configuration relationships before calculating facts. |
| File or other effectful operation | Pydantic input, explicit writer, Pydantic receipt | Pass runtime dependencies explicitly and construct a useful result. |
| Authored execution plan | Parse, check compatibility, then execute | Separate actual representation and compatibility boundaries. |
| Multi-stage application workflow | Explicit workflow order and visible data handoffs | Name intermediate results and show stage inputs and retained partitions. |
| External detection or reusable evidence | Explicit dependencies and reusable evidence | Inject the dependency; preserve incomplete evidence and separate its interpretation. |

The NIOCCS snapshot uses Pydantic input models and several dataclass outputs. The Pydantic writer result in the reference is a proposed adaptation. Preserve that distinction when describing or reusing the examples.

## Implement a cohesive module

### Public request and result models

- Use Pydantic for structured authored configuration and structured public results. Give fields domain names, supported options, defaults, and relevant constraints. Reuse an existing suitable model.
- Choose coercion, strictness, unknown-field handling, and mutability deliberately for the boundary. Prefer rejecting unknown fields in authored operation configuration. Do not impose one model configuration on every external payload.
- Put cross-field configuration invariants in model validation. Keep construction and validation free of file reads, writes, network requests, and client creation. Check schema and resource compatibility in the execution boundary when needed.
- Construct the result model or explicitly validate a returned payload. A return annotation alone does not validate the output.
- Represent meaningful incomplete, unknown, and failed outcomes explicitly. Let exceptions follow the repository's error contract; do not silently turn failures into empty successful results.

### Functions and dependencies

- Annotate public function parameters and return values. Use a concrete verb and domain noun when the module does not already make the operation clear. Preserve concise framework hooks such as `compute`, `condition`, and `apply` when their scope is clear.
- Pass only the values a computation needs. Pass clients, detectors, paths, and other runtime dependencies explicitly; use keyword-only arguments where they clarify configuration or dependencies.
- Keep a runtime context at adapters that genuinely need shared runtime services. Avoid passing the whole context into a scalar or expression helper.
- Return native scalars, expressions, and dataframes from computations where those are the useful interfaces. A native dataframe can be a separate data argument beside a Pydantic request. Avoid converting its rows to model objects solely for uniformity.
- Keep model methods focused on coherent representation behavior such as serialization. Put effectful operation execution in named functions.

### Modules and workflows

- Keep a small operation's request, function, and result together when they form one cohesive unit. Extract helpers or shared modules for concrete consumers or independently meaningful operations.
- Use existing framework and SDK capabilities. Add registries, adapters, base classes, factories, or compilation stages only when a demonstrated execution requirement needs them.
- Compose stages with visible calls and named intermediate results. Show filtering, eligibility, retained/quarantined partitions, and other consequential handoffs at the next stage's input.
- Run applicable compatibility checks before expensive or external work. Keep evidence generation, interpretation, and disposition identifiable. Do not imply transactionality or idempotency unless implemented.
- Respect local orchestration ownership. Where the repository assigns operational CLI work to Poe and the build DAG to DVC, preserve those boundaries; reserve Python for the domain, SDK, or validation work it owns.

## Review and verify

Check the implementation against these questions:

1. Can a caller see the structured inputs, runtime dependencies, result, and effects from the interface and a representative call?
2. Are constraints and result invariants enforced at the relevant boundary, including meaningful unknown and incomplete states?
3. Does each helper accept only the data it uses and return the natural result type?
4. Can a reader follow workflow order and data handoffs directly?
5. Does each abstraction serve a concrete caller or execution requirement?
6. Are existing public compatibility, dependency choices, framework contracts, and repository orchestration rules preserved?

Use the repository's existing checks. Add focused behavioral verification when a change creates a concrete risk; avoid tests that merely restate the implementation. Once the relevant behavior and required gates are verified, stop optional testing.

Report what changed, the important interface choices, and the checks actually run. Distinguish inspected code, syntax checks, executed tests, and proposed examples. For a review-only request, report actionable findings without making unrequested edits.
