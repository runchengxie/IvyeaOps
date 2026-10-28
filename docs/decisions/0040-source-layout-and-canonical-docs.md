# ADR-0040: Source layout and canonical documentation

Date: 2026-10-28. Status: accepted for this changeset.

## Context

The user requested a clean root, English script names, source under `src/client` and `src/server`, and eMAG-first navigation. A subsequent audit request established English documentation as canonical with priority `zh-CN` translations, without a whole-product i18n rewrite.

## Decision

Move source inputs and update their consumers. Preserve frozen archive output layout through a code-root resolver. Preserve ignored legacy source configuration through runtime fallback and atomic no-clobber installer migration. Block detected old systemd source units before an automatic restart. Keep conventional GitHub/agent entry names while placing document bodies under `docs`.

English management dispatch reuses specialized scripts and offers side-effect-free DryRun. Stop operations verify process ownership. The catalog includes daily eMAG/task pages and advanced categories without changing backend permissions. Docs describe current implementation and explicit limits rather than an announced release.

## Consequences

Hand-written services/shortcuts need migration. Frozen resource locations remain compatible. Actual installation/update/stop and binary/Docker deployment need target-environment validation. Agent localization does not imply a global UI language switch. Existing dependency vulnerabilities are reported separately rather than hidden or upgraded during documentation work.
