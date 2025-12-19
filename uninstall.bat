@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Run as Administrator.
  exit /b 1
)

sc query AgentLite >nul 2>&1
if %errorlevel%==0 (
  net stop AgentLite >nul 2>&1
  timeout /t 2 >nul
)

pushd "%SCRIPT_DIR%"
python Service.py remove >nul 2>&1
popd

exit /b 0
