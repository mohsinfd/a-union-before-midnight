@echo off
setlocal
set "REPOROOT=%~dp0"

echo.
echo ============================================================
echo  A Union Before Midnight 4.2.0-alpha.22 - Installer
echo  Alpha 22 - 29 Aug 2026
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

