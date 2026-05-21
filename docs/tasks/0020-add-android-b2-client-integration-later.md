# Task 0020: Add Android B2 Client Integration Later

From version: 0.3.3

Status: In Review

Understanding: 82%

Confidence: 68%

Progress: 90%

Complexity: High

Theme: Android Integration

## Goal

Integrate Android with B2 proposals after the backend contract is validated.

## Links

- Derived from `docs/backlog/0051-add-android-b2-client-integration-later.md`
- Spec: `docs/specs/0001-strava-b2-backend-responsibilities-and-android-contract.md`

## Scope

In:

- Configure backend URL for local testing.
- Fetch sync status and proposals.
- Display B2 proposals as editable map selections.
- Confirm accepted proposals through existing local completion flow.

Out:

- No work until backend API is stable.
- No automatic completion.
- No Play Store work.

## Validation

- Android displays B2 proposals.
- User can deselect proposals.
- User must explicitly confirm completion.
- Completion remains in local Room state.

## Report

Implemented Android B2 integration foundation:

- backend URL setting in the Strava B2 panel;
- B2 health, auth, sync, and proposal status calls;
- manual sync and proposal-generation actions;
- proposed-segment loading and map highlighting;
- backend-side accept and dismiss actions;
- documentation for emulator and physical-device backend URLs.

Accepting a proposal still does not update local Room completion state. That
manual application flow remains a future task.
