@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PDIR=%ProgramData%\AgentLite"
set "ENV_DST=%PDIR%\agent.env"
set "ENV_TEMPLATE=%SCRIPT_DIR%agent.env.template"

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Run as Administrator.
  exit /b 1
)

mkdir "%PDIR%" >nul 2>&1

python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Python not found in PATH.
  exit /b 1
)

python -m pip install --upgrade pip >nul
python -m pip install -r "%SCRIPT_DIR%requirements.txt"
if %errorlevel% neq 0 (
  echo ERROR: pip install -r requirements.txt failed.
  exit /b 1
)

if not exist "%ENV_DST%" (
  if exist "%ENV_TEMPLATE%" (
    copy /Y "%ENV_TEMPLATE%" "%ENV_DST%" >nul
  ) else (
    echo ERROR: Missing config.
    echo Create "%ENV_DST%" OR provide "%ENV_TEMPLATE%".
    exit /b 1
  )
)

pushd "%SCRIPT_DIR%"
python Service.py install
if %errorlevel% neq 0 (
  popd
  echo ERROR: Service install failed.
  exit /b 1
)

sc failure AgentLite reset= 86400 actions= restart/60000/restart/60000/restart/60000 >nul
sc config AgentLite start= auto >nul
net start AgentLite >nul 2>&1

popd
exit /b 0
