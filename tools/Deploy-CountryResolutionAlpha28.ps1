param(
    [string]$Target = "C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$targetRoot = (Resolve-Path -LiteralPath $Target).Path
$expectedTarget = "C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1"
if ($targetRoot -ne $expectedTarget) {
    throw "Unexpected deployment target: $targetRoot"
}
if (Get-Process | Where-Object { $_.ProcessName -match '^Darkest.?Hour$' }) {
    throw "Darkest Hour is running; deployment stopped."
}

$saveRoot = Join-Path $targetRoot "scenarios\save games"
$saveBefore = @{}
if (Test-Path -LiteralPath $saveRoot) {
    Get-ChildItem -LiteralPath $saveRoot -File -Recurse | ForEach-Object {
        $saveBefore[$_.FullName] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $repositoryRoot "build\alpha28-country-resolution-backup-$stamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$changed = @(
    "db\events.txt",
    "db\events\aubm_v4\32_national_consolidation.txt",
    "db\events\aubm_v4\35_japan_partnership.txt",
    "db\events\aubm_v4\37_german_campaigns.txt",
    "db\events\aubm_v4\41_wartime_state.txt",
    "db\events\aubm_v4\44_wartime_economy.txt",
    "db\events\aubm_v4\52_delhi_berlin_compact.txt",
    "db\events\aubm_v4\53_country_resolutions.txt",
    "db\events\aubm_v4\53_world_ai_balance1.txt",
    "gfx\load_1024.bmp",
    "gfx\interface\frontend\bg_start.bmp",
    "scenarios\1933.eug",
    "Readme.txt"
)
$retired = @(
    "db\events\aubm_v4\42_wartime_theatres.txt",
    "db\events\aubm_v4\43_wartime_settlements.txt",
    "db\events\aubm_v4\45_enemy_campaigns.txt",
    "db\events\aubm_v4\46_regional_campaigns.txt",
    "db\events\aubm_v4\47_global_campaign_matrix.txt",
    "db\events\aubm_v4\48_route_wartime_consequences.txt",
    "db\events\aubm_v4\49_bespoke_armistices.txt",
    "db\events\aubm_v4\50_southeast_asia_operations.txt",
    "db\events\aubm_v4\51_bespoke_route_arcs.txt"
)

function Resolve-SafeTarget([string]$RelativePath) {
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $targetRoot $RelativePath))
    $prefix = $targetRoot + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe deployment path: $candidate"
    }
    return $candidate
}

foreach ($relative in @($changed + $retired)) {
    $livePath = Resolve-SafeTarget $relative
    if (Test-Path -LiteralPath $livePath -PathType Leaf) {
        $backupPath = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
        Copy-Item -LiteralPath $livePath -Destination $backupPath -Force
    }
}

foreach ($relative in $changed) {
    $sourcePath = Join-Path $repositoryRoot ("mod\" + $relative)
    $livePath = Resolve-SafeTarget $relative
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw "Missing deployment source: $sourcePath"
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $livePath) -Force | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $livePath -Force
    if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $livePath -Algorithm SHA256).Hash) {
        throw "Hash mismatch after deployment: $relative"
    }
}

foreach ($relative in $retired) {
    $livePath = Resolve-SafeTarget $relative
    if (Test-Path -LiteralPath $livePath -PathType Leaf) {
        Remove-Item -LiteralPath $livePath -Force
    }
}

$saveAfter = @{}
if (Test-Path -LiteralPath $saveRoot) {
    Get-ChildItem -LiteralPath $saveRoot -File -Recurse | ForEach-Object {
        $saveAfter[$_.FullName] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
}
if ($saveBefore.Count -ne $saveAfter.Count) {
    throw "Save file count changed during deployment."
}
foreach ($path in $saveBefore.Keys) {
    if (-not $saveAfter.ContainsKey($path) -or $saveBefore[$path] -ne $saveAfter[$path]) {
        throw "Save changed during deployment: $path"
    }
}

Write-Host "DEPLOYED_FILES=$($changed.Count)"
Write-Host "PURGED_FILES=$($retired.Count)"
Write-Host "SAVE_FILES_UNCHANGED=$($saveAfter.Count)"
Write-Host "BACKUP=$backupRoot"
