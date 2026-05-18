# Android Build Notes

## Local Toolchain

The current local APK build is validated on Windows with:

- JDK: `C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot`
- Android SDK: `C:\Users\Pmondou\AppData\Local\Android\Sdk`
- Gradle: repository wrapper `gradlew.bat`

Installed Android SDK packages:

- `platform-tools` 37.0.0
- `platforms;android-35`
- `build-tools;35.0.0`

The Android SDK licenses have been accepted locally through `sdkmanager`.

## Environment

The following user environment variables are configured:

```text
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot
ANDROID_HOME=C:\Users\Pmondou\AppData\Local\Android\Sdk
ANDROID_SDK_ROOT=C:\Users\Pmondou\AppData\Local\Android\Sdk
```

The user `Path` also includes:

```text
C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot\bin
C:\Users\Pmondou\AppData\Local\Android\Sdk\cmdline-tools\latest\bin
C:\Users\Pmondou\AppData\Local\Android\Sdk\platform-tools
```

Open a new terminal after environment changes so PowerShell reloads the updated
user variables.

## Build Command

From the repository root:

```powershell
.\gradlew.bat assembleDebug
```

If a reused Gradle daemon hangs, run:

```powershell
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

## Expected APK

The debug APK should be produced at:

```text
app\build\outputs\apk\debug\app-debug.apk
```

## Last Validation

Executed:

```powershell
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

Result:

- build successful;
- debug APK produced at `app\build\outputs\apk\debug\app-debug.apk`;
- APK signature verified with `apksigner`;
- certificate CN: `Android Debug`.
