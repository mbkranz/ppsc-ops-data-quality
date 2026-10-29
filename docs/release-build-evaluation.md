# Release build decision

Historical record. Current interfaces and acceptance are described in [the native Flow SQL plan](specs/minimal-implementation-plan.md).

DVC now owns the real requirements → dependency wheels and application wheel →
runtime bundle graph. Durable retrieval and promotion of the same bytes justify
this narrow adoption. Live validation, deployment and report publication remain
explicit uncached operations.

The implementation replaces the build manifest with committed native DVC output
identities. The final Git SHA is release identity and deployment provenance, not
a build input: committing the lock necessarily changes that SHA. Git-owned drivers
are not copy-only DVC outputs. Each producer owns only its own output path.

The cheap requirements boundary permits a package-version or release-tool change
to export identical runtime requirements and reuse dependency-wheel downloads.
Pip 25.3 and platform/ABI flags are explicit producer inputs. Python 3.11.17,
uv 0.12.23, Hatchling 1.27.0 plus its locked dependencies and fixed wheel timestamps
bound the supported producer environment. Repeated byte equality is checked on
that environment; it is not a promise across arbitrary hosts.

Ops supplies the dependency-download, deterministic archive and installed-smoke
pattern used in NIOCCS. NIOCCS supplies immutable conditional S3 uploads and the
exact-release deployment boundary. Salesforce demonstrates why a stage-local
freshness check and explicit source refresh matter: artifact availability alone
cannot establish current source/lock agreement.

See [the runbook](build-deployment.md) for canonical commands and the implementation
review for executed checks and still-open live acceptance. Historical hashes and
claims from the superseded manifest experiment are intentionally not used as
current release evidence.
