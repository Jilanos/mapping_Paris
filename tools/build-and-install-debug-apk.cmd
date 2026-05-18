@echo off
setlocal

cd /d "%~dp0\.."

set "ADB=%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if exist "%ADB%" goto adb_found

for /f "delims=" %%A in ('where adb 2^>nul') do (
    set "ADB=%%A"
    goto adb_found
)

echo [ERROR] adb.exe introuvable.
echo Installe Android SDK Platform-Tools ou verifie LOCALAPPDATA\Android\Sdk\platform-tools.
exit /b 1

:adb_found
echo [INFO] ADB: "%ADB%"

echo [INFO] Build APK debug...
call gradlew.bat --no-daemon assembleDebug
if errorlevel 1 exit /b %errorlevel%

set "APK="
for /f "delims=" %%F in ('dir /b /a-d /o-d "app\build\outputs\apk\debug\mapping-paris-*-debug.apk" 2^>nul') do (
    set "APK=app\build\outputs\apk\debug\%%F"
    goto apk_found
)

echo [ERROR] APK debug introuvable dans app\build\outputs\apk\debug.
exit /b 1

:apk_found
echo [INFO] APK: "%CD%\%APK%"

echo [INFO] Appareils connectes:
"%ADB%" devices

echo [INFO] Installation sur l'appareil Android connecte...
"%ADB%" install -r "%CD%\%APK%"
if errorlevel 1 exit /b %errorlevel%

echo [OK] APK installe.
