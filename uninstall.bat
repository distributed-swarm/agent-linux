@echo off
setlocal

REM Headless Agent-Lite uninstaller (ADMIN ONLY)

set "SCRIPT_DIR=%~dp0"
set "PROGRAM_DATA=%ProgramData%\AgentLite"

echo ========================================
echo Agent-Lite Service Uninstaller
echo ========================================

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Run this as Administrator.
  exit /b 1
)

REM Stop service if present
sc query AgentLite >nul 2>&1
if %errorlevel%==0 (
  net stop AgentLite >nul 2>&1
  timeout /t 2 >nul
)

pushd "%SCRIPT_DIR%"
python Service.py remove >nul 2>&1
popd

echo Removed service (if it existed).
echo Logs/config remain in: "%PROGRAM_DATA%"
exit /b 0
