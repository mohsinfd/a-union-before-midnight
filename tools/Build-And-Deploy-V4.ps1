param(
    [string]$GameRoot,
    [string]$TargetName = "A Union Before Midnight V4",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "[$Label]"
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Get-OverlayHashes {
    $overlay = Join-Path $repositoryRoot "mod"
    $resolved = [System.IO.Path]::GetFullPath($overlay)
    $hashes = @{}
    foreach ($file in Get-ChildItem -LiteralPath $resolved -Recurse -File) {
        $relative = $file.FullName.Substring($resolved.Length + 1)
        $hashes[$relative] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    }
    return $hashes
}

$python = Get-Command python -ErrorAction Stop
$rebaseArguments = @{
    RepositoryRoot = $repositoryRoot
}
if ($GameRoot) {
    $rebaseArguments.GameRoot = $GameRoot
}

Write-Host "Rebuilding the V4 overlay from Darkest Hour Full..."
& (Join-Path $PSScriptRoot "Rebase-V4-DirectDH.ps1") @rebaseArguments

Write-Host ""
Write-Host "[Repeat-build stability]"
$firstPass = Get-OverlayHashes
& (Join-Path $PSScriptRoot "Rebase-V4-DirectDH.ps1") @rebaseArguments
$secondPass = Get-OverlayHashes
$unstable = @(
    $firstPass.Keys |
        Where-Object {
            -not $secondPass.ContainsKey($_) -or $firstPass[$_] -ne $secondPass[$_]
        }
)
$unstable += @($secondPass.Keys | Where-Object { -not $firstPass.ContainsKey($_) })
if ($unstable.Count -gt 0) {
    throw "The V4 rebase is not idempotent; $($unstable.Count) overlay file(s) changed on the second pass."
}
Write-Host "Repeat-build stability passed for $($secondPass.Count) overlay files."

Write-Host ""
Write-Host "[Installer manifest]"
& (Join-Path $PSScriptRoot "Generate-V4-InstallerManifest.ps1") -RepositoryRoot $repositoryRoot

Invoke-Checked "Static validation" {
    & $python.Source (Join-Path $PSScriptRoot "validate_v4.py") --root $repositoryRoot
}
Invoke-Checked "Art release gate" {
    & $python.Source (Join-Path $PSScriptRoot "audit_v4_art.py") --strict
}
Invoke-Checked "Service-sprite gate" {
    & $python.Source (Join-Path $PSScriptRoot "audit_v4_sprites.py")
}
Invoke-Checked "Opening economy" {
    & $python.Source (Join-Path $PSScriptRoot "analyze_v4_opening.py")
}
Invoke-Checked "Combat pacing" {
    & $python.Source (Join-Path $PSScriptRoot "analyze_combat_pacing.py")
}
Invoke-Checked "Construction caps" {
    & $python.Source (Join-Path $PSScriptRoot "analyze_construction_caps.py") --root (Join-Path $repositoryRoot "mod")
}

if ($ValidateOnly) {
    Write-Host ""
    Write-Host "V4 rebuilt and validated. Deployment was skipped and the game was not launched."
    exit 0
}

$installerArguments = @{
    TargetName = $TargetName
}
if ($GameRoot) {
    $installerArguments.GameRoot = $GameRoot
}

Write-Host ""
Write-Host "[Verified deployment]"
& (Join-Path $repositoryRoot "installer\Install-A-Union-Before-Midnight.ps1") @installerArguments

Write-Host ""
Write-Host "V4 rebuilt, validated and deployed. The game was not launched."
