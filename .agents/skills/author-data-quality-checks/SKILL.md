---
name: author-data-quality-checks
description: Author or update operational quality checks in ppsc-ops-data-quality from existing job or notebook logic and relevant Salesforce graph/native metadata. Use for adding a subject suite, relationship rule, SQL validation population, or meaningful check fixtures.
---

# Author data quality checks

Read `AGENTS.md`, `docs/sources.md`, and the existing subject suite before editing.
Use `gx/account_contact_relation_to_account.py` and `tests/test_gx.py` as the worked
example of a native rule with separate missing-key, missing-parent, and ambiguous-parent findings.

1. Identify the operational question and the source job/notebook. Read its upstream
   filters, joins, missing-value handling, and treatment of findings. Record the
   repository, path, revision, and relevant code locations.
2. Retrieve the relevant Salesforce graph subset and source pointers using the
   existing ppsc-salesforce helpers. Follow its lineage guide: include incident
   edges and association links when needed, inspect the native metadata, and keep
   graph org/revision explicit. Treat illustrative SQL as evidence to review.
3. Verify the physical table/column bindings and declare the population, effective
   date/current selection, and physical snapshot selection. Keep older unchanged
   records. Confirm the half-open interval convention before live as-of validation.
4. State the failure condition, violation grain, null/blank behavior, duplicate
   behavior, and timing assumptions. Preserve monitoring versus blocking treatment.
   Event-triggered Flow assignments need event evidence or an explicit business
   state requirement; a current MIN/MAX does not establish Flow conformance.
5. Add ordinary SQL functions to `batches.py` when relational composition is needed.
   Put each integrity query in `gx/<subject>/<rule>.sql`; the filename becomes its
   rule ID and SQL comments describe its evidence and assumptions. Use `{batch}`,
   `account_state`, or `account_contact_relation_state` for selected populations.
   Native structural checks remain in the existing Python suite module. Make any
   additional relation and its selection explicit; never deduplicate away an integrity finding.
6. Keep rule metadata compact: stable `rule_id`, native description, rationale,
   violation grain, source revision/pointer, assumptions, and investigation guidance.
   Keep run-specific bindings and dates in `run.json`.
7. Add fixtures that demonstrate the meaningful passing and failing records,
   temporal boundaries, and duplicate/null behavior. Verify full failure counts
   separately from bounded diagnostic samples. Run `uv run poe check` and a dry run.
8. New SQL files in an existing selected subject run automatically; keep candidates
   outside these directories. Explicitly add a new subject query/suite pair
   to `build_queries` in `run.py`, only when its contract is established. Record
   unresolved candidates in `docs/sources.md` and leave them outside selection.
   Metadata such as `status: candidate` does not control execution.

Keep graph retrieval and source interpretation at authoring time. Routine validation
runs committed modules. Use the existing native GX API, explicit runner, and source
modules; introduce abstractions only for a demonstrated requirement.
