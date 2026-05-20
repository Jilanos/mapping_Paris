# ADR 0002: Use a Dedicated Strava B2 Backend for Activity Sync and Segment Proposal Generation

Status: Proposed

Date: 2026-05-20

## Context

The current Android app is local-first and manual-first. It stores the segment
dataset locally, stores completion state in Room, renders segments with
osmdroid, and can use device GPS to propose segments. The next major Strava
integration would need OAuth token handling, activity sync, GPS stream download,
trace matching, sync history, and proposal output.

Putting all Strava responsibility inside the APK would increase security and
maintenance risk because Strava secrets and refresh behavior do not fit well in
a personal APK-only model.

## Decision

Use a dedicated Strava B2 backend as the target direction for Strava activity
sync and segment proposal generation.

For the first implementation, prefer:

- Python FastAPI backend;
- single-user first;
- SQLite for local and first personal deployment state;
- environment variables for Strava client id, client secret, redirect URL, and
  database path;
- no secrets committed to Git;
- a clear future path to PostgreSQL and multi-user support without implementing
  either in the first milestone.

B2 should own:

- Strava OAuth and token refresh.
- Secure token storage.
- Strava activity and stream synchronization.
- Sync history and rate limit handling.
- GPS trace to segment matching.
- Proposed segment output for Android.

Android should remain responsible for:

- displaying proposals;
- letting the user review, edit, accept, or reject proposals;
- writing confirmed completions into local Room state;
- preserving manual confirmation as mandatory.

## Consequences

Positive:

- Strava secrets and refresh tokens can stay outside the APK.
- Sync history and rate limit handling can be centralized.
- Matching can evolve without rebuilding the APK for every algorithm change.
- Android can remain focused on display and user confirmation.

Negative:

- The project becomes more complex than a pure local APK.
- Deployment, database, backup, and monitoring decisions become necessary.
- The app is no longer fully offline for Strava proposal generation.
- Security and privacy responsibilities increase because GPS traces and tokens
  are sensitive.

## Alternatives Considered

### Direct Strava Integration Inside APK

Rejected as the default direction for B2 evaluation. It keeps the architecture
simple but makes token security, refresh, sync history, and rate limit handling
harder to manage safely in a personal APK.

### Minimal Token Proxy Backend

Useful as an intermediate option, but it does not fully address activity sync,
stream download, matching, proposal history, or retry behavior.

### Full B2 Backend

Preferred direction to evaluate. It centralizes sensitive and long-running work
while keeping Android as the review and confirmation surface.

Implementation recommendation: start with FastAPI plus SQLite because the
matching work benefits from Python's geospatial ecosystem later, while the
first milestone can remain lightweight and personal-use oriented.

### Node.js/Express Backend

Viable, especially for simple REST APIs, but less attractive for the matching
pipeline because GPS and geospatial processing are likely to benefit from
Python libraries and scripts already aligned with the segment-generation
tooling direction.

### Cloudflare Worker

Potentially attractive for lightweight OAuth and API hosting, but not a good
first target for GPS stream matching and local segment dataset processing. The
runtime and storage constraints would make B2 more complex too early.

### Desktop Sync Script With JSON Import

Potentially useful as a fallback or prototype. It avoids deployment but creates
a manual workflow and does not provide a clean Android sync experience.

## Security Implications

- No Strava client secret should be stored in Android or committed to Git.
- Refresh tokens must be encrypted or stored in a managed secret-capable store.
- GPS streams and activity metadata should be treated as sensitive personal
  data.
- Logs must avoid raw tokens and should avoid unnecessary raw GPS traces.
- Revocation and deletion flows must be defined before implementation.

## Local-First Impact

The Android app should remain local-first for confirmed completion state. B2 may
generate proposals, but accepted completions should still pass through explicit
Android user confirmation and local Room storage. B2 should not become the sole
source of truth for completed segments unless a future ADR changes that.

## Open Questions

- Which first deployment target should host the FastAPI service?
- Should B2 store raw GPS streams or only derived matching results?
- How should segment dataset versions be shared between Android, tools, and B2?
- What is the exact rollback path if B2 produces poor proposals?
- When should SQLite be migrated to PostgreSQL, if ever?
