@echo off
setlocal
set "REPOROOT=%~dp0"

echo.
echo ============================================================
echo  A Union Before Midnight 4.2 Alpha 20 - Installer
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%REPOROOT%installer\Install-A-Union-Before-Midnight.ps1"
if errorlevel 1 goto :failed

echo.
echo Installation completed successfully.
pause
exit /b 0

:failed
echo.
echo Installation failed. No source files were modified.
pause
exit /b 1

