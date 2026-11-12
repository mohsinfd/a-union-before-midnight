param([string]$GameRoot,[string]$BloodIronRoot)
$ErrorActionPreference = 'Stop'
if (-not $GameRoot) { $GameRoot = Read-Host 'Darkest Hour folder containing Darkest Hour.exe' }
if (-not $BloodIronRoot) { $BloodIronRoot = Read-Host 'Blood and Iron v1.1 mod folder' }
$taskPython = Get-Command py -ErrorAction SilentlyContinue
$taskPrefix = @('-3')
if (-not $taskPython) { $taskPython = Get-Command python -ErrorAction SilentlyContinue; $taskPrefix = @() }
if (-not $taskPython) { throw 'Install Python 3.11 or later, then run this installer again.' }
& $taskPython.Source @taskPrefix -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
& $taskPython.Source @taskPrefix (Join-Path $PSScriptRoot 'japan_expansion\install_portable.py') --game-root $GameRoot --base-root $BloodIronRoot
if ($LASTEXITCODE -ne 0) { throw 'Japan Rising installation or verification failed. The game was not started.' }
Write-Host 'Ready. Use the Japan Rising JX1 Alpha2 desktop shortcut when you want to play.'
