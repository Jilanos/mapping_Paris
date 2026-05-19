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
set "INSTALL_LOG=%TEMP%\mapping-paris-adb-install.log"
"%ADB%" install -r "%CD%\%APK%" > "%INSTALL_LOG%" 2>&1
set "INSTALL_EXIT=%ERRORLEVEL%"
type "%INSTALL_LOG%"

if "%INSTALL_EXIT%"=="0" goto install_ok

findstr /C:"INSTALL_FAILED_UPDATE_INCOMPATIBLE" "%INSTALL_LOG%" >nul
if not errorlevel 1 goto signature_mismatch

findstr /I /C:"unauthorized" "%INSTALL_LOG%" >nul
if not errorlevel 1 goto unauthorized_device

findstr /I /C:"no devices/emulators found" "%INSTALL_LOG%" >nul
if not errorlevel 1 goto no_device

exit /b %INSTALL_EXIT%

:install_ok
echo [OK] APK installe.
exit /b 0

:signature_mismatch
echo.
echo [ERROR] Installation impossible: signature Android incompatible.
echo Une app com.jilanos.mappingparis est deja installee avec une autre cle de signature.
echo Android refuse donc la mise a jour avec -r.
echo.
echo Avant de desinstaller, exporte la progression depuis l'app si elle contient des donnees a garder.
echo La desinstallation supprime la base locale Room, les reglages et la progression locale.
echo.
echo Pour repartir proprement:
echo "%ADB%" uninstall com.jilanos.mappingparis
echo cmd /c tools\build-and-install-debug-apk.cmd
exit /b %INSTALL_EXIT%

:unauthorized_device
echo.
echo [ERROR] Appareil ADB non autorise.
echo Deverrouille le telephone et accepte la demande "Autoriser le debogage USB".
echo Ensuite relance:
echo cmd /c tools\build-and-install-debug-apk.cmd
exit /b %INSTALL_EXIT%

:no_device
echo.
echo [ERROR] Aucun appareil Android detecte par ADB.
echo Branche le telephone en USB, active le debogage USB, puis verifie:
echo "%ADB%" devices
echo Relance ensuite:
echo cmd /c tools\build-and-install-debug-apk.cmd
exit /b %INSTALL_EXIT%
