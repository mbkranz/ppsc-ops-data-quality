# Pinned shared compiler distribution

`ppsc_metadata-0.2.0-py3-none-any.whl` is built from
[`projects/metadata` at producer commit 36c9c9c078e1b065d8c217c56ab90a09bad52d47](https://github.com/mbkranz/ppsc-salesforce/tree/36c9c9c078e1b065d8c217c56ab90a09bad52d47/projects/metadata).

SHA256: `c098612aad3c66fe9938ba7b2b98f4d4d8108af5208c79f9dca4e7073a91a111`.

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
