# Frozen compiler dependency

`7f4f3108/ppsc_metadata-0.3.0-py3-none-any.whl` is built from
[`projects/metadata` at `7f4f3108ea0910ebd3649c770242f69e0301917c`](https://github.com/mbkranz/ppsc-salesforce/tree/7f4f3108ea0910ebd3649c770242f69e0301917c/projects/metadata).

- Package: `ppsc-metadata==0.3.0`, Ibis 12.0.0, SQLGlot 30.24.0.
- Wheel SHA256: `c26afb47820ecabc654f4f73b098af3e96062329815d09304e8f5c3686074ecf`.
- Installed source fingerprint: `a74bb14dd0640a500d3050b32d22ae2c7a08c2f188107df8c98d8f7e11e5124a`.
- Build backend used: Hatchling 1.32.4; source and package version inspected from the actual wheel.

The runtime verifies the installed compiler source bytes against the fingerprint
derived from this wheel, along with installed input hashes and request identity.
`uv.lock` records this local wheel; DVC includes `vendor/` in the actual release
graph. The packaged APMP/native inputs are generated from the same producer
definition revision and preserve their own original source revision separately.
Edits originate in APMP and are regenerated; do not maintain an edited schema copy here.

To refresh: build the compiler from a named producer commit, place its wheel in
a new revision directory, regenerate selected APMP inputs, update constants and
example hashes, lock/sync, regenerate queries/suites/diagrams, reproduce DVC and
run the installed-bundle smoke with `--no-index --no-cache`. Rollback restores
the complete prior wheel/lock/input selection.
