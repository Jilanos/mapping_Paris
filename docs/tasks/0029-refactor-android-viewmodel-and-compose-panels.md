# Task 0029 - Refactor Android ViewModel and Compose panels

## Goal

Reduce Android maintenance risk by splitting the current large ViewModel and UI
file into smaller, testable units.

## Scope

- Extract Strava B2 proposal loading, filtering, validation, and reconciliation
  into a dedicated use case/service.
- Extract GPS tracking and proposal logic into a dedicated controller.
- Extract progression actions into a small local-progress service.
- Split the largest Compose panels into focused components.
- Add focused unit tests around the extracted business logic.

## Non-goals

- No UI redesign.
- No matching threshold changes.
- No segment dataset changes.
- No backend behavior changes.

## Migration and compatibility

- Preserve Room completion state semantics.
- Preserve import/export JSON compatibility.
- Preserve current B2 backend API behavior.
- Keep manual map completion behavior unchanged.

## Acceptance criteria

- `MappingParisViewModel.kt` no longer owns unrelated GPS, B2, progression,
  import/export, and selection logic directly.
- `MappingParisApp.kt` is split into smaller composables without changing user
  workflows.
- Existing Android unit tests and debug build pass.

## Status

Backlog candidate. Not implemented in the Strava B2 state-consistency patch.
