param(
    [string]$GameRoot,
    [string]$TargetName = "A Union Before Midnight V4.2",
    [string]$DonorName = "Blood and Iron v1.1",
    [switch]$Preview
)

$ErrorActionPreference = "Stop"

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
        throw "Unsafe personal-visual path: $RelativePath"
    }
    return $resolvedPath
}

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

$donorRoot = [System.IO.Path]::GetFullPath((Join-Path $modsRoot $DonorName))
if (-not (Test-Path -LiteralPath $donorRoot -PathType Container)) {
    throw "The personal donor installation was not found: $donorRoot"
}

# These are deliberately copied only from the player's own locally installed
# Blood and Iron instance.  They are never added to the repository, public
# installer manifest or release archive.
$assets = @(
    "map\Map_1\colorscales.csv",
    "map\Map_1\lightmap1.tbl",
    "map\Map_1\lightmap2.tbl",
    "gfx\map\Snow.bmp",
    "gfx\map\airfield.bmp",
    "gfx\map\beach.bmp",
    "gfx\map\harbour.bmp",
    "gfx\map\rain.bmp",
    "gfx\map\storm.bmp"
)

$sources = @()
foreach ($relativePath in $assets) {
    $source = Resolve-SafeChildPath -Root $donorRoot -RelativePath $relativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "The personal donor visual is missing: $source"
    }
    $sources += [pscustomobject]@{ RelativePath = $relativePath; Source = $source }
}

if ($Preview) {
    Write-Host "Personal terrain-reference overlay would copy $($sources.Count) local files:"
    $sources | ForEach-Object { Write-Host "  $($_.RelativePath)" }
    exit 0
}

$stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$backupRoot = Join-Path $targetRoot "AUBM_PERSONAL_TERRAIN_BACKUP\$stamp"
$records = @()
foreach ($item in $sources) {
    $target = Resolve-SafeChildPath -Root $targetRoot -RelativePath $item.RelativePath
    $targetDirectory = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }

    $replacedExisting = Test-Path -LiteralPath $target -PathType Leaf
    if ($replacedExisting) {
        $backup = Resolve-SafeChildPath -Root $backupRoot -RelativePath $item.RelativePath
        $backupDirectory = Split-Path -Parent $backup
        if (-not (Test-Path -LiteralPath $backupDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $target -Destination $backup -Force
    }

    Copy-Item -LiteralPath $item.Source -Destination $target -Force
    $sourceHash = (Get-FileHash -LiteralPath $item.Source -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($targetHash -ne $sourceHash) {
        throw "Hash verification failed for personal visual: $($item.RelativePath)"
    }

    $records += [pscustomobject]@{
        path = $item.RelativePath.Replace("\", "/")
        sha256 = $targetHash.ToLowerInvariant()
        replacedExisting = $replacedExisting
    }
}

$statePath = Join-Path $targetRoot "AUBM_PERSONAL_TERRAIN_VISUALS.json"
@{
    mode = "personal-blood-and-iron-reference-overlay"
    installed_at = (Get-Date).ToString("o")
    donor_root = $donorRoot
    backup_root = $backupRoot
    files = $records
    note = "Local-only personal reference overlay. Never redistribute these donor-derived files."
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8

Write-Host "Personal terrain-reference overlay installed and verified."
Write-Host "Backup location: $backupRoot"
Write-Host "The public AUBM package and GitHub repository remain donor-free."
