# Release 0.3.0: Android Foreground GPS Assistance

Date: 2026-05-19

Version: `0.3.0`

Version code: `7`

Branch: `main`

APK:

- `app/build/outputs/apk/debug/mapping-paris-0.3.0-debug.apk`

## Summary

Release 0.3.0 adds foreground GPS assistance to the Android map while keeping
the app local-first and manual-first.

GPS is used as an orientation and proposal layer:

- the current position can be shown on the map;
- the map recenters only when the GPS button is pressed;
- the app-open GPS path can propose likely covered segments;
- proposed segments remain editable selections;
- no segment is completed until the user explicitly validates it.

## User-Facing Changes

- Added foreground location permissions:
  - `ACCESS_FINE_LOCATION`;
  - `ACCESS_COARSE_LOCATION`.
- Added a compact always-visible GPS button on the map.
- Added a current-position marker with accuracy radius.
- Added non-blocking GPS states for:
  - loading;
  - permission denied;
  - GPS unavailable.
- Added settings for:
  - enabling/disabling GPS-assisted behavior;
  - GPS-to-segment matching strictness.
- GPS-assisted behavior is disabled by default on first install.
- Added local app-open GPS path capture when GPS assistance is enabled.
- Added conservative segment proposal matching from the captured path.
- GPS-proposed segments are selected for review and use a distinct temporary
  style.
- The user can deselect or adjust proposed segments before completion.
- Android version was bumped to `0.3.0`.

## Data and Privacy

- GPS path data is kept in memory for the current app session.
- The captured path is discarded when the app closes.
- GPS data is not uploaded.
- No account or backend service is added.
- No closed-app background tracking is implemented.
- Completion state remains stored locally in Room.

## Validation

Commands run successfully:

```powershell
.\gradlew.bat --no-daemon --stacktrace :app:compileDebugKotlin --rerun-tasks
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

Recommended full release validation:

```powershell
git status --short --branch
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
py -3 tools\segment_pipeline\validate_pwa.py
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

APK verification:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.3.0-debug.apk
```

Device install attempt:

```powershell
cmd /c tools\build-and-install-debug-apk.cmd
```

Result:

- Build successful.
- Connected device detected: `37290DLJH004PP`.
- Install blocked by Android:
  `INSTALL_FAILED_UPDATE_INCOMPATIBLE`.
- Cause: the already installed `com.jilanos.mappingparis` package has a
  different signature from the newly built debug APK.
- After user approval, the existing package was uninstalled and the 0.3.0 debug
  APK was installed successfully.
- Follow-up GPS permission fix was also rebuilt and installed successfully.

Installed package:

- `versionName=0.3.0`
- `versionCode=7`

Confirmed user feedback:

- Current GPS position display works on the Pixel 8.
- GPS segment proposal selection still needs real-route validation.

## Manual GPS Test Checklist

Recommended device:

- Google Pixel 8
- Latest Android version available for that device

Check:

- Fresh install starts with GPS assistance disabled.
- GPS button asks for foreground location permission when GPS is first used.
- Permission grant shows the current-position marker.
- Permission denial leaves the map usable and shows a non-blocking state.
- Disabled or unavailable Android location services show a non-blocking state.
- GPS button recenters on the current position.
- The map does not continuously lock to the current position.
- Accuracy radius appears when accuracy is available.
- Marker remains readable in light and blue map modes.
- Walking with the app open proposes nearby segments conservatively.
- Proposed segments are selected but not completed.
- Proposed segments have a distinct temporary style.
- Proposed selection can be edited before validation.
- Matching strictness in settings changes proposal behavior.
- No proposed segment is completed until the user taps the existing completion
  action.
- Closing and reopening the app does not restore the previous GPS path.

## Known Limits

- GPS proposal matching is intentionally conservative for version 0.3.0.
- Dense Paris streets and poor GPS accuracy can still produce imperfect
  proposals.
- Manual real-device walking validation is still required.
- Offline map tiles are not part of this release.
- Long-term route history is not part of this release.
- Play Store release signing is not part of this release.
