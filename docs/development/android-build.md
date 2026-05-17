# Android Build Notes

## Local toolchain

The MVP build was validated with a local toolchain installed under:

- JDK: `C:\Users\paulm\devtools\jdk-17`
- Gradle: `C:\Users\paulm\devtools\gradle\gradle-8.10.2`
- Android SDK: `C:\Users\paulm\devtools\android-sdk`

Installed Android SDK packages:

- `platform-tools`
- `platforms;android-35`
- `build-tools;35.0.0`
- `build-tools;34.0.0`

## Expected build command

From PowerShell:

```powershell
$env:JAVA_HOME = "$env:USERPROFILE\devtools\jdk-17"
$env:ANDROID_HOME = "$env:USERPROFILE\devtools\android-sdk"
$env:ANDROID_SDK_ROOT = "$env:USERPROFILE\devtools\android-sdk"
.\gradlew.bat assembleDebug
```

For lint:

```powershell
.\gradlew.bat lintDebug
```

## Expected APK

The debug APK should be produced at:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Last validation

- `assembleDebug`: passed.
- `lintDebug`: passed.
- APK produced: `app/build/outputs/apk/debug/app-debug.apk`.
- ADB check: no device was connected at validation time.
