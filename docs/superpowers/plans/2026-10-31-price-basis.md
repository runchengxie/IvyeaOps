# Correct eMAG price basis

Source: official API documentation https://marketplace-api.emag.ro/api-doc, embedded OpenAPI 4.5.2, ProductOfferSave and OfferSave price fields.
Bug: scenario code divided VAT-exclusive sale_price by (1+VAT), understating net revenue.
Fix: use sale_price directly for net revenue; retain the existing explicitly entered gross-price commission scenario, constructing its gross base with the entered VAT rate. Label this as a user assumption, not a verified platform fee policy. Keep stored inputs and historical reports unchanged; current calculations use corrected semantics.

- [x] RED/GREEN net-price and zero-commission VAT-invariance regressions.
- [x] Correct calculator, source-basis metadata and UI/docs labels.
- [x] Review, relevant backend checks, frontend checks and real App harness.
- [ ] PR/CI, merge, deploy and cleanup.

No marketplace write endpoint is called; no exact clearance price or investment return is inferred from missing cost evidence.


Verification: 60 related backend tests passed; ruff/docs checks, frontend typecheck, 8 i18n tests and final production build passed. Real App harness verified net-price labels, explicit fee assumptions, accessibility names and computed layout. Independent review confirmed arithmetic and compatibility; remaining operational labels were aligned. No dependencies changed. Current private ledger contains zero saved records, so no existing complete merchant scenario was silently rewritten. Official raw-price fields and saved inputs remain unchanged.
