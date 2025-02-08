@echo off
setlocal enabledelayedexpansion

:: Colors for pretty output
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

:: Function to print status messages
:print_status
echo %GREEN%=^>%NC% %~1
exit /b

:: Function to print warnings
:print_warning
echo %YELLOW%Warning:%NC% %~1
exit /b

:: Function to print errors
:print_error
echo %RED%Error:%NC% %~1
exit /b

:: Function to handle errors
:handle_error
call :print_error %~1
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:: Check if running with admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    call :print_error "Please do not run this script as administrator. It will ask for permissions when needed."
    pause
    exit /b 1
)

call :print_status "Starting Gweeb installation..."

:: Check for Visual C++ Redistributable
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if %errorLevel% NEQ 0 (
    call :print_status "Installing Visual C++ Redistributable..."
    :: Download VC++ Redistributable
    curl -L -o vc_redist.exe https://aka.ms/vs/17/release/vc_redist.x64.exe || (
        call :handle_error "Failed to download Visual C++ Redistributable"
        exit /b 1
    )
    
    :: Install VC++ Redistributable
    start /wait vc_redist.exe /quiet /norestart
    if %errorLevel% NEQ 0 (
        call :handle_error "Failed to install Visual C++ Redistributable"
        exit /b 1
    )
    
    :: Clean up
    del vc_redist.exe
)

:: Check for Python
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
    call :print_status "Python not found. Installing Python..."
    
    :: Download Python installer
    curl -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe || (
        call :handle_error "Failed to download Python installer"
        exit /b 1
    )
    
    :: Install Python
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1
    if %errorLevel% NEQ 0 (
        call :handle_error "Failed to install Python"
        exit /b 1
    )
    
    :: Clean up
    del python_installer.exe
    
    :: Refresh environment variables
    call :print_status "Refreshing environment variables..."
    setx PATH "%PATH%" >nul 2>&1
)

:: Verify Python installation
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
    call :handle_error "Python installation failed. Please try installing Python 3.11 manually."
    exit /b 1
)

:: Create application directory
set "APP_DIR=%LOCALAPPDATA%\Gweeb"
if not exist "%APP_DIR%" (
    call :print_status "Creating application directory..."
    mkdir "%APP_DIR%" || (
        call :handle_error "Failed to create application directory"
        exit /b 1
    )
)

:: Copy files to application directory
call :print_status "Installing Gweeb..."
xcopy /E /I /Y "." "%APP_DIR%" || (
    call :handle_error "Failed to copy files to application directory"
    exit /b 1
)

:: Create virtual environment
cd "%APP_DIR%" || (
    call :handle_error "Failed to change to application directory"
    exit /b 1
)

if not exist "venv" (
    call :print_status "Creating virtual environment..."
    python -m venv venv || (
        call :handle_error "Failed to create virtual environment"
        exit /b 1
    )
)

:: Activate virtual environment and install requirements
call :print_status "Installing dependencies..."
call venv\Scripts\activate.bat || (
    call :handle_error "Failed to activate virtual environment"
    exit /b 1
)

python -m pip install --upgrade pip || (
    call :handle_error "Failed to upgrade pip"
    exit /b 1
)

python -m pip install -r requirements.txt || (
    call :handle_error "Failed to install requirements"
    exit /b 1
)

:: Create start menu shortcut
call :print_status "Creating start menu shortcut..."
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

cscript //nologo "%VBS_SCRIPT%" || (
    call :handle_error "Failed to create start menu shortcut"
    exit /b 1
)
del "%VBS_SCRIPT%"

call :print_status "Installation complete!"
call :print_status "You can now run Gweeb from the Start Menu"

:: Ask if user wants to run Gweeb now
set /p LAUNCH="Would you like to run Gweeb now? (y/n) "
if /i "%LAUNCH%"=="y" (
    call :print_status "Starting Gweeb..."
    start "" "%SHORTCUT%"
)

echo.
echo Press any key to exit...
pause >nul
endlocal 