@echo off
REM ============================================================
REM iOS Backup Explorer — One-Click Launcher (Windows)
REM Double-click this file from Explorer to launch the app.
REM ============================================================

title iOS Backup Explorer
cd /d "%~dp0"

REM --- Check if uv is available ---
where uv >nul 2>&1
if %ERRORLEVEL% == 0 goto :HAS_UV

REM --- Auto-install uv ---
echo [*] 'uv' non trovato. Installazione automatica...
powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
if %ERRORLEVEL% neq 0 (
    echo [!] Installazione di uv fallita. Tentativo con pip...
    goto :TRY_PIP
)

REM Refresh PATH
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"

:HAS_UV
REM --- Validate or Sync dependencies ---
if exist ".venv" (
    uv run python -c "pass" >nul 2>&1 || (
        echo [*] Ambiente virtuale corrotto (probabile cloud-sync da altro OS). Ricreazione...
        rmdir /s /q .venv
    )
)
if not exist ".venv" (
    echo [*] Installazione dipendenze...
    uv sync
)
echo [*] Avvio iOS Backup Explorer...
uv run python gui.py
goto :END

:TRY_PIP
REM --- Fallback: use pip + venv ---
if exist ".venv" (
    .venv\Scripts\python.exe -c "pass" >nul 2>&1 || (
        echo [*] Ambiente virtuale corrotto. Ricreazione...
        rmdir /s /q .venv
    )
)
if not exist ".venv" (
    echo [*] Creazione ambiente virtuale con pip...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt 2>nul || .venv\Scripts\pip install iphone-backup-decrypt python-dotenv phonenumbers sv-ttk
)
echo [*] Avvio iOS Backup Explorer...
.venv\Scripts\python gui.py

:END
pause
