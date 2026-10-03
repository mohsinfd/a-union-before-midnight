param(
    [string]$LiveMod = "C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceEvent = Join-Path $RepoRoot "mod\db\events\aubm_v4\52_delhi_berlin_compact.txt"
$SourceArt = Join-Path $RepoRoot "mod\gfx\events_pics"
$SourceReadme = Join-Path $RepoRoot "docs\DELHI_BERLIN_COMPACT.md"
$BuildRoot = Join-Path $RepoRoot "build\germancompact1"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $BuildRoot "backups\$Stamp"
$ReceiptPath = Join-Path $LiveMod "AUBM_GERMANCOMPACT1_INSTALL_RECEIPT.json"
$EventName = "52_delhi_berlin_compact.txt"
$Registration = 'event = "db\events\aubm_v4\52_delhi_berlin_compact.txt"'
$ArtNames = @(
    "aubm_ger_compact_signing.bmp",
    "aubm_ger_machines_for_ore.bmp",
    "aubm_ger_monsoon_armour.bmp",
    "aubm_ger_three_capitals.bmp",
    "aubm_ger_caucasus_lifeline.bmp",
    "aubm_ger_suez_road.bmp",
    "aubm_ger_independent_command.bmp"
)

function Get-SaveFingerprints([string]$Root) {
    $SaveRoot = Join-Path $Root "scenarios\save games"
    if (-not (Test-Path -LiteralPath $SaveRoot)) { return @() }
    return @(Get-ChildItem -LiteralPath $SaveRoot -File -Filter "*.eug" | Sort-Object FullName | ForEach-Object {
        [ordered]@{ path = $_.FullName; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash }
    })
}

function Copy-Backup([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $Relative = $Path.Substring($LiveMod.Length).TrimStart('\')
    $Target = Join-Path $BackupRoot $Relative
    $Parent = Split-Path -Parent $Target
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Copy-Item -LiteralPath $Path -Destination $Target -Force
}

function Replace-Ascii([string]$Path, [string]$Old, [string]$New) {
    $Latin1 = [Text.Encoding]::GetEncoding(28591)
    $Bytes = [IO.File]::ReadAllBytes($Path)
    $Text = $Latin1.GetString($Bytes)
    if ($Text.Contains($New)) { return }
    if (-not $Text.Contains($Old)) { throw "Expected marker not found in $Path`: $Old" }
    $Text = $Text.Replace($Old, $New)
    [IO.File]::WriteAllBytes($Path, $Latin1.GetBytes($Text))
}

if (-not (Test-Path -LiteralPath $LiveMod -PathType Container)) { throw "Live mod not found: $LiveMod" }
if (-not (Test-Path -LiteralPath $SourceEvent -PathType Leaf)) { throw "Source compact missing: $SourceEvent" }
$Running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match "DarkestHour|hoi" })
if ($Running.Count -gt 0) { throw "Darkest Hour is running. Close it before installing GERMANCOMPACT1." }

$LiveRegistry = Join-Path $LiveMod "db\events.txt"
$LiveEvent = Join-Path $LiveMod "db\events\aubm_v4\$EventName"
$LiveScenario = Join-Path $LiveMod "scenarios\1933.eug"
$LiveBootstrap = Join-Path $LiveMod "db\events\india_v3\00_bootstrap.txt"
$LiveText = Join-Path $LiveMod "config\text.csv"
$LiveReadme = Join-Path $LiveMod "AUBM_GERMANCOMPACT1_README.md"

foreach ($Required in @($LiveRegistry, $LiveScenario, $LiveBootstrap, $LiveText)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "Required live file missing: $Required" }
}

$BeforeSaves = Get-SaveFingerprints $LiveMod
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
foreach ($Path in @($LiveRegistry, $LiveEvent, $LiveScenario, $LiveBootstrap, $LiveText, $LiveReadme, $ReceiptPath)) { Copy-Backup $Path }
foreach ($ArtName in $ArtNames) { Copy-Backup (Join-Path $LiveMod "gfx\events_pics\$ArtName") }

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LiveEvent) | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LiveMod "gfx\events_pics") | Out-Null
Copy-Item -LiteralPath $SourceEvent -Destination $LiveEvent -Force
foreach ($ArtName in $ArtNames) {
    Copy-Item -LiteralPath (Join-Path $SourceArt $ArtName) -Destination (Join-Path $LiveMod "gfx\events_pics\$ArtName") -Force
}
Copy-Item -LiteralPath $SourceReadme -Destination $LiveReadme -Force

$Latin1 = [Text.Encoding]::GetEncoding(28591)
$RegistryBytes = [IO.File]::ReadAllBytes($LiveRegistry)
$RegistryText = $Latin1.GetString($RegistryBytes)
if (-not $RegistryText.Contains($Registration)) {
    $Anchor = 'event = "db\events\aubm_v4\51_bespoke_route_arcs.txt"'
    if ($RegistryText.Contains($Anchor)) {
        $RegistryText = $RegistryText.Replace($Anchor, "$Anchor`r`n$Registration")
    } else {
        $RegistryText = $RegistryText.TrimEnd("`r", "`n") + "`r`n$Registration`r`n"
    }
    [IO.File]::WriteAllBytes($LiveRegistry, $Latin1.GetBytes($RegistryText))
}

Replace-Ascii $LiveScenario "India 1933 - 27-ROSTER1 [NEW GAME PLAYTEST]" "India 1933 - 28-GERCOMPACT1 [NEW GAME PLAYTEST]"
Replace-Ascii $LiveBootstrap "AUBM 27-ROSTER1 - New Campaign" "AUBM 28-GERCOMPACT1 - New Campaign"
Replace-Ascii $LiveText "PLAY 27-ROSTER1" "PLAY 28-GERCOMPACT1"

$InstalledText = [IO.File]::ReadAllText($LiveEvent)
$Ids = @([regex]::Matches($InstalledText, '(?m)^\s*id\s*=\s*(92816\d\d)\s*$') | ForEach-Object { [int]$_.Groups[1].Value })
if ($Ids.Count -lt 45) { throw "Installed compact contains only $($Ids.Count) events" }
if (($Ids | Sort-Object -Unique).Count -ne $Ids.Count) { throw "Duplicate compact event IDs detected after install" }
$LiveRegistryCheck = $Latin1.GetString([IO.File]::ReadAllBytes($LiveRegistry))
if ([regex]::Matches($LiveRegistryCheck, [regex]::Escape($Registration)).Count -ne 1) { throw "Compact registry line is missing or duplicated" }
foreach ($ArtName in $ArtNames) {
    $ArtPath = Join-Path $LiveMod "gfx\events_pics\$ArtName"
    if ((Get-Item -LiteralPath $ArtPath).Length -ne 139254) { throw "Unexpected event-art size: $ArtName" }
}

$AfterSaves = Get-SaveFingerprints $LiveMod
if (($BeforeSaves | ConvertTo-Json -Compress) -ne ($AfterSaves | ConvertTo-Json -Compress)) { throw "Save fingerprints changed during install" }

$Receipt = [ordered]@{
    version = "28-GERCOMPACT1"
    installedAt = (Get-Date).ToString("o")
    liveMod = $LiveMod
    backup = $BackupRoot
    eventCount = $Ids.Count
    eventSha256 = (Get-FileHash -LiteralPath $LiveEvent -Algorithm SHA256).Hash
    art = @($ArtNames | ForEach-Object { [ordered]@{ name = $_; sha256 = (Get-FileHash -LiteralPath (Join-Path $LiveMod "gfx\events_pics\$_") -Algorithm SHA256).Hash } })
    savesUnchanged = $true
    nativePlaytested = $false
}
$Receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding utf8
Write-Host "Installed 28-GERCOMPACT1: $($Ids.Count) events, $($ArtNames.Count) dedicated images."
Write-Host "Backup: $BackupRoot"
Write-Host "Receipt: $ReceiptPath"
