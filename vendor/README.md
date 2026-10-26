# Frozen Salesforce compiler

`1d59b5b8/ppsc_salesforce-0.1.0-py3-none-any.whl` is the existing `ppsc-salesforce==0.1.0`
distribution, built from [source revision 1d59b5b8](https://github.com/mbkranz/ppsc-salesforce/tree/1d59b5b87b69e2b7da52c3c0bdb008c2af37c200).

SHA256: `7d588d32c56c1890a5b2988b3d7b4981042aa6ee1de5b829d58e936c93b240ec`.

Ops selects the `ibis` extra. Salesforce acquisition SDKs and APMP's ODCS and
workbook dependencies are absent from this runtime. Flow queries and rollups live
in the existing Salesforce domain modules; there is no metadata distribution.

Build with `SOURCE_DATE_EPOCH=315532800 python -m build --wheel --no-isolation`.
For a reviewed compiler update, replace the wheel in a new revision directory,
refresh APMP-generated inputs, update the lockfile, regenerate SQL/suites/diagrams,
and reproduce the DVC release and installed smoke through Poe.
