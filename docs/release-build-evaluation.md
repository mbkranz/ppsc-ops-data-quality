# Release build graph evaluation

Decision (2026-10-22): **defer DVC adoption**, retaining the explicit locked Poe
sequence. There is a real branching build graph; the reason to defer is the
current reuse benefit, not the absence of a graph. Smoke execution remains a
verification gate. STS, deployment, submission, catalog registration, live
configuration and live results must never become cached build stages.

## Candidate stage boundaries

| Stage | Explicit inputs | Exclusive outputs | Invalidation/reuse |
| --- | --- | --- | --- |
| Requirements export | `pyproject.toml`, `uv.lock`, uv version and export flags | `requirements/requirements.txt` | Lock or export-tool changes rebuild; retain a fixed output path/header policy. |
| Dependency acquisition | Hashed requirements, CPython 3.11, Linux platform/ABI list, pip 25.3 | `dependencies/wheels/` | Reuse across source-only changes; platform, resolver/downloader or requirements changes invalidate. |
| Project wheel | `src/`, README, project/build metadata, lockfile, Hatchling/build tooling, `SOURCE_DATE_EPOCH` | `project/*.whl` | Source/packaging changes invalidate; no dependency-wheel overlap. |
| Release assembly | Dependency and project wheels, driver, requirements, lockfile, explicit revision and supported runtime | `bundle/` | Both branches converge; revision must invalidate the manifest even when wheel bytes are unchanged. |

These are proposed DVC ownership boundaries, not an installed DVC pipeline. The
current sequence uses `build/release/requirements.txt`, `wheels/`, `project/` and
`bundle/`. A future pipeline must give each stage its own directory and let DVC
remove stale outputs before execution: `package_release` deliberately rejects an
existing bundle. Do not cache the entire release directory as one stage while
also assigning its children to other stages. A revision file generated explicitly
by Poe is preferable to relying on hidden `.git/HEAD` state or stale parameters.

## Executed evidence

Used the actual project wheel and all locked CPython 3.11/Linux dependency wheels.
The official `build-release` sequence completed, followed by `smoke-release`:
index-free installation, dependency verification, installed-package location,
installed CLI help/invalid-configuration behavior, isolated compilation, and
synthetic execution with all 53 expectation rows and two validation summaries.
All 97 tests passed on Python 3.11 and 3.12, including profile-aware Poe task
rehearsal and configurable Glue SDK payloads.

The repeat/invalidation experiment built the project wheel twice with
`SOURCE_DATE_EPOCH=315532800`, exported requirements twice using an identical
command/output path, and assembled fresh bundles from the downloaded wheels.
Mutations used temporary copies, leaving source and locked versions intact.

| Experiment | Observed result |
| --- | --- |
| Repeat requirements export | Identical bytes. |
| Repeat project wheel | Identical SHA256: `f03c14ba67b65bd81d80418d99baf06ca54edd7a05d6eec8ead5a45ce755f080`. |
| Source comment change in copied package | Wheel SHA256 changed to `7484006204e23c6871cb10b3bf6c465c80dd3803d00eecc7e6afb128a560444c`; assembled wheel archive changed. |
| Repeat assembly, identical inputs/revision | Identical archive SHA256 `2e24ec8679a9a89883c888428d79c7012478b13948d9b2f8b4c463b7a448438a` and manifest SHA256 `3439849256c00f7ce93407698b3b8042607b790d63c788b6ff336932c067a0b6`. |
| Driver-only change | Manifest/driver hashes changed; wheel archive stayed identical. |
| Lockfile comment change | Lock/manifest hashes changed; wheel archive stayed identical. This tests provenance invalidation, not a dependency-version upgrade. |
| Explicit revision change (`a…a` → `b…b`) | Manifest changed; wheel archive stayed identical. Experiment SHAs were synthetic inputs, not release identities. |
| Manifest runtime changed to Python 3.12 | Bundle verification rejected the unsupported target. Python 3.11/Glue 5.0/x86_64 is the only supported release target. |

Changing a dependency version or adding another platform still requires a fresh
locked export/download and smoke installation. Those upgrades were not simulated.
The wheel hashes above identify the experiment tree, including its README, rather
than promising identical bytes for later documentation/source revisions.

## Toolchain assumptions and recommendation

Zip entries use sorted filenames and fixed timestamps; wheel builds set a fixed
`SOURCE_DATE_EPOCH`. The experiments used one host, Python 3.11.17, uv 0.12.23 and
pip 25.3. The build backend is currently bounded by `hatchling>=1.26,<2`, not pinned
to one version by the runtime lock. ZIP compression libraries, platform choices,
export headers/paths and build-tool changes can affect bytes. These local repeat
results do not establish reproducibility across arbitrary hosts/toolchains. A
future cached DAG must pin or record those inputs before claiming that guarantee.

Dependency acquisition offers the clearest reusable stage. Its downloads already
benefit from the downloader's cache; the project wheel is small and source edits
usually require a new revision/manifest. There is currently one release target
and no demonstrated shared artifact consumer. DVC's extra ownership, revision and
fresh-directory machinery does not yet provide enough practical benefit here.
Revisit when dependency download/assembly dominates repeated release builds,
multiple target bundles share dependencies, or durable artifact retrieval is
needed across projects. Keep the present manifest/hash and installed smoke gates
regardless of that decision.
