# ADR-0041: Use a shared patched KaTeX version

Date: 2026-10-29. Status: accepted for this changeset.

## Context

Formula plugins declare KaTeX 0.16, which remains affected by a low-severity advisory. The application already uses KaTeX 0.19.1 directly. npm otherwise installs the older release separately for both plugins.

## Decision

Use an npm override referencing the direct KaTeX dependency, so both plugins resolve to the patched version. Run the complete npm audit in CI and exercise formula rendering and untrusted links in regression tests.

## Consequences

KaTeX 0.19 is outside the plugins' declared ranges. Clean installation and tests verify the current integration, but do not guarantee compatibility with every formula or future release. Revisit the override when upstream plugins update their supported ranges.
