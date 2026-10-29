# ADR-0047: Source-labelled eMAG dashboard views

Date: 2026-10-29. Status: accepted.

## Context

The [LinkFox store operations guide](https://wiki.linkfox.com/features/store-operations) describes management and specialist views. The eMAG snapshot has a different scope and does not provide all Amazon metrics.

## Decision

Provide management and specialist presentations of existing eMAG snapshot data. Show the source, capture time and available order window. Mark absent metrics unavailable and link issue observations to the existing inspection workflow.

## Consequences

The views do not perform platform writes, infer missing sales or advertising data, or change snapshot and API contracts. Their appearance is informed by the public LinkFox guide; the interactive demo still uses synthetic data.
