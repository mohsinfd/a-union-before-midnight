param(
    [string]$RepositoryRoot,
    [string]$GameRoot,
    [string]$TargetName = "A Union Before Midnight V4.2",
    [string]$BloodAndIronPath,
    [switch]$Preview
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $PSScriptRoot
}

function Resolve-GameRoot {
    param([string]$Requested)

    if ($Requested) {
        return [System.IO.Path]::GetFullPath($Requested)
    }

    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Darkest Hour A HOI Game"),
        (Join-Path $env:ProgramFiles "Steam\steamapps\common\Darkest Hour A HOI Game")
    ) | Where-Object { $_ }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $candidate "Darkest Hour.exe")) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Darkest Hour was not found. Pass -GameRoot explicitly."
}

function Resolve-SafeChildPath {
    param(
        [string]$Root,
        [string]$RelativePath
    )

    $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
    $resolvedPath = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $RelativePath))
    if (-not $resolvedPath.StartsWith($resolvedRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Unsafe personal-sprite path: $RelativePath"
    }
    return $resolvedPath
}

$repositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$gameRoot = Resolve-GameRoot $GameRoot
$modsRoot = Join-Path $gameRoot "Mods"
$targetRoot = [System.IO.Path]::GetFullPath((Join-Path $modsRoot $TargetName))
$expectedParent = [System.IO.Path]::GetFullPath($modsRoot)
if ([System.IO.Path]::GetDirectoryName($targetRoot) -ne $expectedParent) {
    throw "TargetName must be a single safe folder name."
}

$markerPath = Join-Path $targetRoot "A_UNION_BEFORE_MIDNIGHT_INSTALL.json"
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
    throw "The A Union Before Midnight installation was not found: $targetRoot"
}

if ([string]::IsNullOrWhiteSpace($BloodAndIronPath)) {
    $BloodAndIronPath = Join-Path $gameRoot "Mods\Blood and Iron v1.1"
}
$donorRoot = [System.IO.Path]::GetFullPath($BloodAndIronPath)
if (-not (Test-Path -LiteralPath $donorRoot -PathType Container)) {
    throw "The personal donor installation was not found: $donorRoot"
}

# Rebuild only the ignored local source payload.  The public unit registry has
# already been written by the ordinary AUBM build; this does not alter it.
$builder = Join-Path $PSScriptRoot "Build-Aubm-IndiaSprites.ps1"
& $builder `
    -RepositoryRoot $repositoryRoot `
    -GameRoot $gameRoot `
    -BloodAndIronPath $donorRoot `
    -SkipRegistryPatch
if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
    throw "Personal India sprite generation failed with exit code $LASTEXITCODE."
}

$modRoot = Join-Path $repositoryRoot "mod"
$manifestRelative = "gfx\map\units\AUBM-IND-GENERATED-MANIFEST.json"
$manifestPath = Resolve-SafeChildPath -Root $modRoot -RelativePath $manifestRelative
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "The local India sprite manifest was not generated: $manifestPath"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.namespace -ne "AUBM-IND" -or $manifest.country -ne "IND") {
    throw "The local sprite manifest is not an AUBM India payload."
}

$allowedPrefixes = @("gfx/map/units/", "gfx/palette/")
$records = @()
$seen = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($entry in $manifest.files) {
    $relative = ([string]$entry.path).Replace("/", "\")
    $normalized = $relative.Replace("\", "/")
    if (-not ($allowedPrefixes | Where-Object { $normalized.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) })) {
        throw "The local sprite manifest contains an unsafe path: $normalized"
    }
    if (-not $seen.Add($normalized)) {
        throw "The local sprite manifest duplicates a path: $normalized"
    }
    $source = Resolve-SafeChildPath -Root $modRoot -RelativePath $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "The generated local sprite is missing: $source"
    }
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -ne ([string]$entry.sha256).ToLowerInvariant()) {
        throw "The generated local sprite hash does not match its manifest: $normalized"
    }
    $records += [pscustomobject]@{ relative = $relative; normalized = $normalized; source = $source; sha256 = $sourceHash }
}

# The manifest itself is not listed among its files, but belongs beside the
# descriptors and is required for future local verification.
$records += [pscustomobject]@{
    relative = $manifestRelative
    normalized = $manifestRelative.Replace("\", "/")
    source = $manifestPath
    sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($Preview) {
    Write-Host "Personal India sprite overlay would copy $($records.Count) local files."
    Write-Host "Families: $($manifest.unit_count); descriptors: $($manifest.descriptor_count); bitmaps: $($manifest.bitmap_reference_count)."
    exit 0
}

$stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$backupRoot = Join-Path $targetRoot "AUBM_PERSONAL_SPRITE_BACKUP\$stamp"
$installed = @()
foreach ($record in $records) {
    $target = Resolve-SafeChildPath -Root $targetRoot -RelativePath $record.relative
    $targetDirectory = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    $replacedExisting = Test-Path -LiteralPath $target -PathType Leaf
    $alreadyCorrect = $false
    if ($replacedExisting) {
        $alreadyCorrect = (
            (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -eq $record.sha256
        )
    }
    if ($replacedExisting -and -not $alreadyCorrect) {
        $backup = Resolve-SafeChildPath -Root $backupRoot -RelativePath $record.relative
        $backupDirectory = Split-Path -Parent $backup
        if (-not (Test-Path -LiteralPath $backupDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $target -Destination $backup -Force
    }

    if (-not $alreadyCorrect) {
        Copy-Item -LiteralPath $record.source -Destination $target -Force
    }
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($targetHash -ne $record.sha256) {
        throw "Hash verification failed for personal sprite: $($record.normalized)"
    }
    $installed += [pscustomobject]@{
        path = $record.normalized
        sha256 = $targetHash
        replacedExisting = $replacedExisting
        copied = -not $alreadyCorrect
    }
}

# The public package deliberately retains Darkest Hour's stock sprite registry,
# because the donor-derived descriptors are not distributable.  This local
# overlay changes only the installed copy after all descriptors are present.
$registryRelative = "db\units\division_types.txt"
$registryPath = Resolve-SafeChildPath -Root $targetRoot -RelativePath $registryRelative
if (-not (Test-Path -LiteralPath $registryPath -PathType Leaf)) {
    throw "The installed unit registry is missing: $registryPath"
}
$registryBackup = Resolve-SafeChildPath -Root $backupRoot -RelativePath $registryRelative
$registryBackupDirectory = Split-Path -Parent $registryBackup
if (-not (Test-Path -LiteralPath $registryBackupDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $registryBackupDirectory -Force | Out-Null
}
Copy-Item -LiteralPath $registryPath -Destination $registryBackup -Force

$registryPatcher = Join-Path $PSScriptRoot "Ensure-Aubm-UniqueSpriteKeys.ps1"
& $registryPatcher -RepositoryRoot $repositoryRoot -DivisionTypesPath $registryPath
if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
    throw "Personal India sprite registry patch failed with exit code $LASTEXITCODE."
}
$registryHash = (Get-FileHash -LiteralPath $registryPath -Algorithm SHA256).Hash.ToLowerInvariant()

$statePath = Join-Path $targetRoot "AUBM_PERSONAL_INDIA_SPRITES.json"
@{
    mode = "personal-india-sprite-overlay"
    installed_at = (Get-Date).ToString("o")
    donor_root = $donorRoot
    backup_root = $backupRoot
    unit_families = $manifest.unit_count
    descriptors = $manifest.descriptor_count
    registry = @{
        path = $registryRelative.Replace("\", "/")
        sha256 = $registryHash
        backup = $registryBackup
    }
    files = $installed
    note = "Local-only personal sprite overlay. Never redistribute these donor-derived files."
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host "Personal India sprite overlay installed and verified."
Write-Host "Families: $($manifest.unit_count); descriptors: $($manifest.descriptor_count); files: $($installed.Count)."
Write-Host "Backup location: $backupRoot"
Write-Host "The public AUBM package and GitHub repository remain donor-free."
