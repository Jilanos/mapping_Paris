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
app\build\outputs\apk\debug\mapping-paris-<version>-debug.apk
```

For example, version `0.3.2` produces:

```text
app\build\outputs\apk\debug\mapping-paris-0.3.2-debug.apk
```

## Build And Install Helper

From the repository root:

```powershell
cmd /c tools\build-and-install-debug-apk.cmd
```

The helper:

- builds the latest debug APK;
- finds the newest `mapping-paris-*-debug.apk`;
- lists connected ADB devices;
- installs with `adb install -r`;
- detects common ADB failures and prints the next action.

## Signature Mismatch / Reinstall Required

If install fails with:

```text
INSTALL_FAILED_UPDATE_INCOMPATIBLE
```

the phone already has `com.jilanos.mappingparis` installed with a different
Android signing key. Android prevents replacing an installed app with an APK
signed by another key, even if the package name is the same.

Typical causes:

- a previous debug APK was built from another machine;
- the previous APK used another debug keystore;
- the app was installed from another checkout or signing flow.

The script does not uninstall automatically, because uninstalling removes local
app data:

- Room progression rows;
- local settings;
- any unexported progression.

Safe recovery:

1. If the existing app opens and contains useful progress, export the
   progression from the app first.
2. Uninstall the old package:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.jilanos.mappingparis
```

3. Rebuild and reinstall:

```powershell
cmd /c tools\build-and-install-debug-apk.cmd
```

If the device is listed as `unauthorized`, unlock the phone, accept the USB
debugging authorization dialog, then rerun the helper.

If ADB reports `no devices/emulators found`, connect the phone over USB, enable
USB debugging in Android developer options, check `adb devices`, then rerun the
helper.

## Last Validation

Executed:

```powershell
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

Result:

- build successful;
- debug APK produced at
  `app\build\outputs\apk\debug\mapping-paris-<version>-debug.apk`;
- APK signature verified with `apksigner`;
- certificate CN: `Android Debug`.
