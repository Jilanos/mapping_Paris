# Release 0.3.3: GPS Coverage Threshold and Zoom QOL

Date: 2026-05-19

Version: `0.3.3`

Version code: `10`

Branch: `main`

APK:

- `app/build/outputs/apk/debug/mapping-paris-0.3.3-debug.apk`

## Summary

Release 0.3.3 improves the GPS-assisted prototype after background tracking was
validated on device.

The main changes are:

- GPS proposals now require segment coverage instead of a single nearby point.
- The default coverage threshold is `70%`.
- The threshold is configurable in settings with a slider from `30%` to `95%`.
- The GPS button is hidden while panels are open to avoid close-button clashes.
- Zoom controls are now Compose controls on the right side above the bottom
  validation bar area.
- Pinch zoom performance was adjusted by removing the custom zoom amplifier and
  culling segment drawing to the current viewport.

## GPS Proposal Rule

A segment is proposed only when:

- GPS assistance is enabled;
- at least two GPS positions match the segment within the configured matching
  distance;
- those positions project onto the segment far enough apart to cover at least
  the configured threshold;
- the segment is not already completed;
- the segment was not manually dismissed from current GPS proposals.

Segments are still never completed automatically. GPS proposals remain editable
selections and require explicit user validation.

## Validation

Commands run:

```powershell
.\gradlew.bat --no-daemon --stacktrace :app:compileDebugKotlin
cmd /c tools\build-and-install-debug-apk.cmd
```

Result:

- Kotlin compilation successful.
- Debug APK build successful.
- `mapping-paris-0.3.3-debug.apk` installed successfully on device
  `37290DLJH004PP`.

Installed package confirmed with ADB:

- `versionName=0.3.3`
- `versionCode=10`

## Remaining Manual Checks

- Walk-test the 70% threshold on real Paris streets.
- Confirm a short pass near one segment end does not propose the whole segment.
- Confirm a pass spanning most of a segment does propose it.
- Confirm changing the threshold affects subsequent proposals.
- Confirm pinch zoom feels smoother on the target phone in dense map areas.
- Confirm the GPS button and zoom controls no longer clash with panels or the
  bottom validation bar.
