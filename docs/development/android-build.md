# Android Build Notes

## Requirement

The project needs a local Android toolchain before APK validation can run:

- JDK 17 or newer;
- Android SDK;
- Android platform matching `compileSdk`;
- Gradle, Android Studio, or a generated Gradle wrapper.

The current machine did not expose `java`, `gradle`, `sdkmanager`, `ANDROID_HOME`, or `ANDROID_SDK_ROOT` during MVP execution.

## Expected build command

Once the Android toolchain is installed, run:

```powershell
gradle assembleDebug
```

or, if a Gradle wrapper is added later:

```powershell
.\gradlew.bat assembleDebug
```

## Expected APK

The debug APK should be produced at:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Current limitation

The Android project files are present, but APK generation could not be validated in this environment until the Android toolchain is installed or exposed in the shell.
