# Pinned shared compiler distribution

`1eedb2ab/ppsc_metadata-0.2.0-py3-none-any.whl` is built from
[`projects/metadata` at producer commit 1eedb2abcf5cac6471fb6cc45e5a40c007982854](https://github.com/mbkranz/ppsc-salesforce/tree/1eedb2abcf5cac6471fb6cc45e5a40c007982854/projects/metadata).

SHA256: `fd0934ef5b8234554446358aa4471c8be1257d9e0fb8b6f9ae3ec408e4d502b8`.

The source is independently installable; the Salesforce application is not a
runtime dependency. The small wheel is a temporary transport while independent
package hosting is pending. uv's path source binds the ordinary versioned project
requirement, and `uv.lock` records the actual artifact hash. DVC tracks this folder
for requirements/dependency production; Glue receives it through the normal frozen
wheel bundle. No source rule implementation is copied into the consumer.

To update, review and build the selected producer revision, copy the resulting
wheel, update version/source bindings and this provenance, refresh the uv lock,
and reproduce the release graph to obtain actual DVC output hashes. The compiler
version is distinct from the Flow/native-metadata input revision in its manifest.

The source-revision directory prevents reusing a stale path hash when an unreleased
compiler version is rebuilt. The package includes assignment and determinism evidence,
presence predicates, general rollups and ODCS source/field definitions.
