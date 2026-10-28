# eMAG business evidence plan

User requested progressing price investigation, FBE inventory reconciliation and order/return/fee evidence together. Purchase costs are explicitly unavailable and remain missing.

Implement only fixed official read endpoints: existing offer pagination plus order/read and rma/read separately for types2/3, invoice/read and vat/read. Window1–29 days, sequential rate limiting, fail closed on incomplete/error/duplicate/schema results. Invoice results have a nested invoices list and total_results; VAT is a nonpaginated catalog. Strip customer/supplier identities, addresses, attachments, free text, and product serial numbers before persistence.

Keep signed invoice values exactly as returned, grouped by category/currency. No revenue-minus-invoice shortcut or profit/recommended-price output. Preserve the distinction between order creation window, return request window, invoice date and service period. UTC filter strings have unverified platform timezone and must be labelled.

Use selected offer aging bands as evidence only: compare totals with general_stock, identify differences without inferring reserved/transit quantities. Import one complete combined immutable snapshot; the existing admin board can display counts, coverage and unknowns. Failed collection preserves the previous snapshot.

Verify synthetic identity redaction, fixed endpoints/no redirects, pagination/total checks, signed discounts and inventory discrepancies; run backend and frontend regressions, review, live read-only validation, then merge/cleanup under the user's standing authorization. Prepare source-bound investigation proposals locally, never approve or execute seller changes without concrete values and authorization.
