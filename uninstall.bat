@echo off
setlocal enabledelayedexpansion

echo === Starting Gweeb uninstallation...
echo Current directory: %CD%

:: Check if running with admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Warning: You are running this script as administrator.
    echo This is not recommended but will be allowed.
    echo.
    choice /C YN /M "Do you want to continue?"
    if !errorLevel! == 2 (
        echo.
        echo Uninstallation cancelled.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo.
)

:: Confirm uninstallation
echo This will completely remove Gweeb from your system.
echo  - Remove the application from %LOCALAPPDATA%\Gweeb
echo  - Remove the Start Menu shortcut
echo  - Stop any running instances
echo.
choice /C YN /M "Are you sure you want to uninstall Gweeb?"
if !errorLevel! == 2 (
    echo.
    echo Uninstallation cancelled.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
echo.

:: Kill any running instances
echo === Stopping Gweeb...
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq Gweeb" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Gweeb" >nul 2>&1

:: Remove Start Menu shortcut
echo === Removing Start Menu shortcut...
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Gweeb.lnk"
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    if !errorLevel! NEQ 0 (
        echo Warning: Failed to remove Start Menu shortcut
        echo You may need to remove it manually from:
        echo %SHORTCUT%
        echo.
    )
)

:: Remove application directory
echo === Removing application files...
set "APP_DIR=%LOCALAPPDATA%\Gweeb"
if exist "%APP_DIR%" (
    :: Try to deactivate virtual environment if it exists
    if exist "%APP_DIR%\venv\Scripts\deactivate.bat" (
        call "%APP_DIR%\venv\Scripts\deactivate.bat" >nul 2>&1
    )
    
    :: Remove the directory
    rd /s /q "%APP_DIR%" >nul 2>&1
    if !errorLevel! NEQ 0 (
        echo Error: Failed to remove application directory
        echo You may need to close any running instances of Gweeb
        echo and remove the directory manually from:
        echo %APP_DIR%
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

echo.
echo === Uninstallation complete!
echo Gweeb has been removed from your system.
echo.
echo Press any key to exit...
pause >nul
endlocal 