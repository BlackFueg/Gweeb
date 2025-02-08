@echo off
setlocal enabledelayedexpansion

echo === Starting Gweeb installation...
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
        echo Installation cancelled.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo.
)

:: Check for Python installation
echo === Checking for Python installation...
set "PYTHON_CMD=python"

:: Try Python in PATH
%PYTHON_CMD% --version >nul 2>&1
if %errorLevel% == 0 goto :python_found

:: Try Python 3.13
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
    goto :python_found
)

:: Try Python 3.11
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    goto :python_found
)

:: Try system Python
if exist "C:\Python311\python.exe" (
    set "PYTHON_CMD=C:\Python311\python.exe"
    goto :python_found
)

:: No Python found - ask to install
echo Warning: Python is not found in PATH or common locations
echo.
echo Python 3.8 or higher is required to run Gweeb.
echo Would you like to download and install Python 3.11.0?
echo.
set /p INSTALL_PYTHON="Install Python now? (y/n): "
if /i "!INSTALL_PYTHON!"=="y" (
    echo.
    echo === Downloading Python installer...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    if !errorLevel! NEQ 0 (
        echo Error: Failed to download Python installer
        echo Please download and install Python 3.11 manually from:
        echo https://www.python.org/downloads/
        echo Then run this installer again.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )

    echo === Running Python installer...
    echo Please follow the installer prompts and ensure you check:
    echo  - [X] Add Python to PATH
    echo  - [X] Install for all users (recommended)
    echo.
    echo The installer will start in 5 seconds...
    timeout /t 5 >nul
    start /wait python_installer.exe
    del python_installer.exe

    echo.
    echo === Checking Python installation...
    python --version >nul 2>&1
    if !errorLevel! NEQ 0 (
        echo Error: Python installation may have failed
        echo Please ensure Python is installed and added to PATH
        echo Then run this installer again.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    set "PYTHON_CMD=python"
) else (
    echo.
    echo Error: Python is required to run Gweeb
    echo Please install Python 3.8 or higher and add it to PATH
    echo Then run this installer again.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:python_found
:: Get Python version using a simpler method
for /f "tokens=2" %%I in ('%PYTHON_CMD% -V 2^>^&1') do set PYTHON_VERSION=%%I
echo Found Python version: %PYTHON_VERSION%

:: Parse version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

:: Check version requirements
if %MAJOR% LSS 3 (
    echo Error: Python version %PYTHON_VERSION% is too old
    echo Gweeb requires Python 3.8 or higher
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
if %MAJOR%==3 if %MINOR% LSS 8 (
    echo Error: Python version %PYTHON_VERSION% is too old
    echo Gweeb requires Python 3.8 or higher
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo === Found Python %PYTHON_VERSION%

:: Check for Visual C++ Redistributable
echo === Checking for Visual C++ Redistributable...
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Warning: Visual C++ Redistributable not found
    echo This is required for some Python packages
    echo.
    set /p INSTALL_VCREDIST="Install Visual C++ Redistributable now? (y/n): "
    if /i "!INSTALL_VCREDIST!"=="y" (
        echo.
        echo === Downloading Visual C++ Redistributable...
        curl -L -o vc_redist.exe https://aka.ms/vs/17/release/vc_redist.x64.exe
        if %errorLevel% NEQ 0 (
            echo Error: Failed to download Visual C++ Redistributable
            echo Please download and install it manually from:
            echo https://aka.ms/vs/17/release/vc_redist.x64.exe
            echo Then run this installer again.
            echo.
            echo Press any key to exit...
            pause >nul
            exit /b 1
        )

        echo === Installing Visual C++ Redistributable...
        start /wait vc_redist.exe /passive /norestart
        del vc_redist.exe
    )
)

:: Create application directory
echo === Setting up application directory...
set "APP_DIR=%LOCALAPPDATA%\Gweeb"
echo Application directory will be: %APP_DIR%
if not exist "%APP_DIR%" (
    mkdir "%APP_DIR%"
    if %errorLevel% NEQ 0 (
        echo Error: Failed to create application directory
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Copy files to application directory
echo === Installing Gweeb...
echo Copying files to %APP_DIR%...
xcopy /E /I /Y "." "%APP_DIR%"
if %errorLevel% NEQ 0 (
    echo Error: Failed to copy files to application directory
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Create virtual environment
echo === Setting up Python environment...
cd "%APP_DIR%"
if %errorLevel% NEQ 0 (
    echo Error: Failed to change to application directory
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if %errorLevel% NEQ 0 (
        echo Error: Failed to create virtual environment
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
)

:: Activate virtual environment and install requirements
call venv\Scripts\activate.bat
if %errorLevel% NEQ 0 (
    echo Error: Failed to activate virtual environment
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo === Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorLevel% NEQ 0 (
    echo Error: Failed to install requirements
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Create start menu shortcut
echo === Creating start menu shortcut...
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Gweeb.lnk"
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%SHORTCUT%" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%APP_DIR%\venv\Scripts\pythonw.exe" >> "%VBS_SCRIPT%"
echo oLink.Arguments = "%APP_DIR%\gweeb.py" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%APP_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "Gweeb Clipboard Sharing Utility" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

cscript //nologo "%VBS_SCRIPT%"
if %errorLevel% NEQ 0 (
    echo Error: Failed to create start menu shortcut
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
del "%VBS_SCRIPT%"

echo.
echo === Installation complete!
echo === You can now run Gweeb from the Start Menu
echo.

:: Ask if user wants to run Gweeb now
set /p LAUNCH="Would you like to run Gweeb now? (y/n): "
if /i "%LAUNCH%"=="y" (
    echo === Starting Gweeb...
    start "" "%SHORTCUT%"
)

echo.
echo Installation completed successfully!
echo Press any key to exit...
pause >nul
endlocal 