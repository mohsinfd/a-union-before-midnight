@echo off
setlocal
set "REPOROOT=%~dp0"

echo.
echo ============================================================
echo  A Union Before Midnight V4 - Build, Validate and Deploy
echo ============================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%REPOROOT%tools\Build-And-Deploy-V4.ps1" %*
if errorlevel 1 goto :failed

echo.
echo Build and deployment completed successfully.
echo Darkest Hour was not launched.
pause
exit /b 0

:failed
echo.
echo Build or deployment failed. The game was not launched.
pause
exit /b 1
