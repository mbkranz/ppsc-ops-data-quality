# Portable release build implementation plan

## Review and decision

The four release producers target Linux x86_64/Python 3.11. The installed ppsc-dq CLI remains the application interface. Poe currently contains Bash/jq release checks and Glue/Athena operations. Preserve authored Ibis/GX rules, the after-launch row conditions and reporting behavior.

## Implementation

1. Add validated auto/local/github build routing using the same concrete handoff contract as NIOCCS, without introducing a shared framework. Compatible Linux uses the prepared producer; Windows and other incompatible hosts dispatch Linux preparation. Keep an explicit backend override and prevent Actions redispatch.
2. Prepare the exact clean pushed source SHA in GitHub Actions, run the existing DVC graph and installed smoke, push the graph to the canonical DVC remote and return the generated lock with source provenance. Track the exact dispatched run and preserve local source/lock changes. Restore the original lock if retrieval fails.
3. Keep build preparation separate from publication: review/commit generated lock changes, then use existing independent retrieval and release publication. Do not turn builds into deployments or put live operations in DVC.
4. Move installed smoke into Python. Move account validation, exact job comparison, Glue run/status and Athena catalog submission from Bash/jq to small explicit boto3 functions with validated requests/results and retained receipts. Preserve profile, region, immutable artifacts, failure exit codes and query/run IDs.
5. Replace the GitHub release-artifact shell gate with a PyGithub verification function. Keep simple native commands in Poe and add dependencies only to tooling groups.
6. Add Windows tests for launcher and SDK operations, plus Linux actual release/retrieval/smoke and existing required query/synthetic checks. Document native Windows invocation and one-time workflow/environment setup.

## PPSC reference review

Apply design-python-contracts to revised public operations: validated configuration/results, explicit SDK sessions and paths, effect-free model construction, visible sequence and failures. Keep operation models/functions together where cohesive. Use Poe for names and sequencing; DVC retains exactly four producers. No generic orchestration framework or duplicate build manifest.

## Verification and delivery

Exercise routing, exact SHA/run identity, failed/expired remote builds, handoff validation and rollback, wrong AWS account, job drift, failure status, partial catalog submission and receipt preservation. Run repository-required lint, format, full tests, check-queries and check-synthetic. Rebuild real outputs to finalize dvc.lock. Record pending canonical S3/OIDC/managed runtime acceptance. Complete a second PPSC review, apply findings and push to existing PR #7.
