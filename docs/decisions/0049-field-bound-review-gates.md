# 0049: Field-bound deterministic review gates

Date: 2026-10-31

## Decision
Keep the shared Evidence/Finding/Action contract backward compatible with additive fields. Legacy evidence defaults to inference. Version snapshot envelopes explicitly, treating unversioned historical files as version 1 without rewriting them. Add a separate eMAG verifier for same-store/product/version field references and a registered status-review template.

## Alternatives
Copying a third-party ledger would duplicate existing snapshots and reports and introduce unresolved licensing. Requiring new fields from every legacy Amazon consumer would break unrelated workflows. Hashes alone do not establish identity, dependency completeness or source accuracy.

## Consequences
New local proposals retain structured diagnoses and approvals revalidate them. Arbitrary estimates, derived values and freeform action templates are not certified by this first verifier. Historical proposals lacking diagnostics need fresh source-bound proposals. Report truncation is explicit; verified output is distinct from verification of every store finding. Return VOC and Listing checks remain bounded observational/advisory projections, not marketplace execution or compliance certification.
