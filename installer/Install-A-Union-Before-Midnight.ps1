param(
    [string]$GameRoot,
    [string]$TargetName = "A Union Before Midnight V4",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$overlayRoot = Join-Path $repositoryRoot "mod"
$manifestPath = Join-Path $PSScriptRoot "manifest.txt"
$hashPath = Join-Path $PSScriptRoot "manifest-sha256.txt"
$version = (Get-Content -LiteralPath (Join-Path $repositoryRoot "VERSION") -Raw).Trim()

function Resolve-GameRoot {
    param([string]$Requested)

    if ($Requested) {
        return [System.IO.Path]::GetFullPath($Requested)
    }

    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Darkest Hour A HOI Game"),
        (Join-Path $env:ProgramFiles "Steam\steamapps\common\Darkest Hour A HOI Game"),
        (Join-Path $env:ProgramFiles "Darkest Hour A HOI Game")
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $candidate "Darkest Hour.exe")) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Darkest Hour was not found. Run the installer with -GameRoot pointing to the game folder."
}

function Read-HashManifest {
    $expected = @{}
    foreach ($line in Get-Content -LiteralPath $hashPath) {
        if (-not $line) { continue }
        if ($line -notmatch '^([0-9A-Fa-f]{64}) \*(.+)$') {
            throw "Malformed hash-manifest line: $line"
        }
        $expected[$Matches[2]] = $Matches[1].ToUpperInvariant()
    }
    return $expected
}

function Assert-SafeChildPath {
    param([string]$Root, [string]$Relative)

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $Relative))
    if (-not $resolved.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Unsafe path in installer manifest: $Relative"
    }
    return $resolved
}

if (-not (Test-Path -LiteralPath $overlayRoot -PathType Container)) {
    throw "The mod overlay folder is missing: $overlayRoot"
}
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "The installer manifest is missing: $manifestPath"
}
if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) {
    throw "The installer hash manifest is missing: $hashPath"
}

$GameRoot = Resolve-GameRoot $GameRoot
$launcher = Join-Path $GameRoot "Darkest Hour Launcher.exe"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "The selected folder is not a Darkest Hour installation: $GameRoot"
}

$modsRoot = Join-Path $GameRoot "Mods"
$baseMod = Join-Path $modsRoot "Darkest Hour Full"
$targetRoot = [System.IO.Path]::GetFullPath((Join-Path $modsRoot $TargetName))
$expectedParent = [System.IO.Path]::GetFullPath($modsRoot)
if ([System.IO.Path]::GetDirectoryName($targetRoot) -ne $expectedParent) {
    throw "TargetName must be a single safe folder name."
}
if (-not (Test-Path -LiteralPath $baseMod -PathType Container)) {
    throw "Darkest Hour Full is required at: $baseMod"
}

$managed = @(
    Get-Content -LiteralPath $manifestPath |
        Where-Object { $_ } |
        ForEach-Object { $_.Replace("/", "\") }
)
$expectedHashes = Read-HashManifest
if ($managed.Count -ne $expectedHashes.Count) {
    throw "Manifest and hash-manifest counts do not match."
}

Write-Host "Verifying $($managed.Count) A Union Before Midnight overlay files..."
foreach ($relative in $managed) {
    $source = Assert-SafeChildPath $overlayRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Overlay file is missing: $relative"
    }
    $actual = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    if ($actual -ne $expectedHashes[$relative.Replace("\", "/")]) {
        throw "Overlay hash verification failed: $relative"
    }
}

$markerPath = Join-Path $targetRoot "A_UNION_BEFORE_MIDNIGHT_INSTALL.json"
$oldManagedPath = Join-Path $targetRoot "A_UNION_BEFORE_MIDNIGHT_MANAGED_FILES.txt"
if (Test-Path -LiteralPath $targetRoot -PathType Container) {
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf) -and -not $Force) {
        throw "The target folder already exists and was not created by this installer. Use -Force only after checking it: $targetRoot"
    }
    Write-Host "Updating existing A Union Before Midnight installation..."
} else {
    Write-Host "Creating an isolated Darkest Hour Full foundation..."
    New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
    & robocopy $baseMod $targetRoot /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NP /NFL /NDL
    if ($LASTEXITCODE -ge 8) {
        throw "Darkest Hour Full foundation copy failed with robocopy code $LASTEXITCODE."
    }
}

$oldManaged = @()
if (Test-Path -LiteralPath $oldManagedPath -PathType Leaf) {
    $oldManaged = @(Get-Content -LiteralPath $oldManagedPath | Where-Object { $_ })
}
foreach ($relative in $oldManaged) {
    if ($relative -notin $managed) {
        $stale = Assert-SafeChildPath $targetRoot $relative
        $foundation = Assert-SafeChildPath $baseMod $relative
        if (Test-Path -LiteralPath $foundation -PathType Leaf) {
            $staleDirectory = Split-Path -Parent $stale
            if (-not (Test-Path -LiteralPath $staleDirectory -PathType Container)) {
                New-Item -ItemType Directory -Path $staleDirectory -Force | Out-Null
            }
            Copy-Item -LiteralPath $foundation -Destination $stale -Force
        } elseif (Test-Path -LiteralPath $stale -PathType Leaf) {
            Remove-Item -LiteralPath $stale -Force
        }
    }
}

Write-Host "Installing A Union Before Midnight $version..."
foreach ($relative in $managed) {
    $source = Assert-SafeChildPath $overlayRoot $relative
    $target = Assert-SafeChildPath $targetRoot $relative
    $targetDirectory = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDirectory)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $target -Force
}

Write-Host "Verifying installed files..."
foreach ($relative in $managed) {
    $target = Assert-SafeChildPath $targetRoot $relative
    $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($actual -ne $expectedHashes[$relative.Replace("\", "/")]) {
        throw "Installed-file hash verification failed: $relative"
    }
}

$managed | Set-Content -LiteralPath $oldManagedPath -Encoding ASCII
@{
    name = "A Union Before Midnight"
    version = $version
    installed_at = (Get-Date).ToString("o")
    foundation = "Darkest Hour Full"
} | ConvertTo-Json | Set-Content -LiteralPath $markerPath -Encoding UTF8

Write-Host ""
Write-Host "A Union Before Midnight $version is installed and verified:"
Write-Host "  $targetRoot"
Write-Host ""
Write-Host "Select '$TargetName' in the Darkest Hour launcher."

