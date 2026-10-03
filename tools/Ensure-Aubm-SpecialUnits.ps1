param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$BaselineMod
)

$ErrorActionPreference = "Stop"
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$overlayRoot = Join-Path $root "mod"

if (-not $BaselineMod) {
    $configPath = Join-Path $root "tools\v4_config.json"
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Cannot resolve the Darkest Hour Full baseline: $configPath is missing."
    }
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $BaselineMod = [string]$config.baseline_mod
}

$baselineRoot = [System.IO.Path]::GetFullPath($BaselineMod)
if (-not (Test-Path -LiteralPath $baselineRoot -PathType Container)) {
    throw "Darkest Hour Full baseline was not found: $baselineRoot"
}
if (-not (Test-Path -LiteralPath $overlayRoot -PathType Container)) {
    throw "AUBM overlay was not found: $overlayRoot"
}

$modelGenerator = Join-Path $root "tools\generate_aubm_special_unit_models.py"
if (-not (Test-Path -LiteralPath $modelGenerator -PathType Leaf)) {
    throw "Special-unit model generator is missing: $modelGenerator"
}
$python = Get-Command python -ErrorAction Stop
& $python.Source $modelGenerator
if ($LASTEXITCODE -ne 0) {
    throw "Special-unit model generation failed with exit code $LASTEXITCODE."
}

function Write-Cp1252Text {
    param([string]$Path, [string]$Text)

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText(
        $Path,
        ($Text.TrimEnd() + "`r`n"),
        $encoding
    )
}

function Ensure-OverlayFile {
    param([string]$RelativePath)

    $target = Join-Path $overlayRoot $RelativePath
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        return $target
    }

    $source = Join-Path $baselineRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required baseline file is missing: $source"
    }
    $parent = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $target
    return $target
}

$unitTypes = [ordered]@{
    d_rsv_33 = @'
d_rsv_33 = {
	#ID			33
	type		= bergsjaeger
	name		= AUBM_NAME_GURKHA_RIFLES
	short_name	= AUBM_SNAME_GURKHA_RIFLES
	desc		= AUBM_LDESC_GURKHA_RIFLES
	short_desc	= AUBM_SDESC_GURKHA_RIFLES
	eyr			= 1
	sprite		= bergsjaeger
	transmute	= infantry
	gfx_prio	= 3
	value		= 1.6
	list_prio	= 40
}
'@
    d_rsv_34 = @'
d_rsv_34 = {
	#ID			34
	type		= bergsjaeger
	name		= AUBM_NAME_FRONTIER_FORCE
	short_name	= AUBM_SNAME_FRONTIER_FORCE
	desc		= AUBM_LDESC_FRONTIER_FORCE
	short_desc	= AUBM_SDESC_FRONTIER_FORCE
	eyr			= 1
	sprite		= bergsjaeger
	transmute	= infantry
	gfx_prio	= 3
	value		= 1.4
	list_prio	= 40
}
'@
    d_rsv_35 = @'
d_rsv_35 = {
	#ID			35
	type		= bergsjaeger
	name		= AUBM_NAME_CHINDIT_COLUMNS
	short_name	= AUBM_SNAME_CHINDIT_COLUMNS
	desc		= AUBM_LDESC_CHINDIT_COLUMNS
	short_desc	= AUBM_SDESC_CHINDIT_COLUMNS
	eyr			= 1
	sprite		= bergsjaeger
	transmute	= infantry
	gfx_prio	= 4
	value		= 1.5
	list_prio	= 40
}
'@
    d_rsv_36 = @'
d_rsv_36 = {
	#ID			36
	type		= paratrooper
	name		= AUBM_NAME_INDIAN_AIRBORNE
	short_name	= AUBM_SNAME_INDIAN_AIRBORNE
	desc		= AUBM_LDESC_INDIAN_AIRBORNE
	short_desc	= AUBM_SDESC_INDIAN_AIRBORNE
	eyr			= 1
	sprite		= paratrooper
	transmute	= infantry
	gfx_prio	= 5
	value		= 1.7
	list_prio	= 40
}
'@
    d_rsv_37 = @'
d_rsv_37 = {
	#ID			37
	type		= marine
	name		= AUBM_NAME_COROMANDEL_MARINES
	short_name	= AUBM_SNAME_COROMANDEL_MARINES
	desc		= AUBM_LDESC_COROMANDEL_MARINES
	short_desc	= AUBM_SDESC_COROMANDEL_MARINES
	eyr			= 1
	sprite		= marine
	transmute	= infantry
	gfx_prio	= 4
	value		= 1.6
	list_prio	= 40
}
'@
    d_rsv_38 = @'
d_rsv_38 = {
	#ID			38
	type		= armor
	name		= AUBM_NAME_GUARDS_ARMOUR
	short_name	= AUBM_SNAME_GUARDS_ARMOUR
	desc		= AUBM_LDESC_GUARDS_ARMOUR
	short_desc	= AUBM_SDESC_GUARDS_ARMOUR
	eyr			= 6
	sprite		= panzer
	transmute	= light_armor
	gfx_prio	= 10
	armor		= yes
	value		= 3.1
	list_prio	= 110
}
'@
    d_rsv_39 = @'
d_rsv_39 = {
	#ID			39
	type		= motorized
	name		= AUBM_NAME_GUARDS_MOTORISED
	short_name	= AUBM_SNAME_GUARDS_MOTORISED
	desc		= AUBM_LDESC_GUARDS_MOTORISED
	short_desc	= AUBM_SDESC_GUARDS_MOTORISED
	eyr			= 3
	sprite		= motorized
	transmute	= infantry
	gfx_prio	= 7
	value		= 1.5
	list_prio	= 80
}
'@
    d_rsv_40 = @'
d_rsv_40 = {
	#ID			40
	type		= infantry
	name		= AUBM_NAME_INDIAN_PIONEERS
	short_name	= AUBM_SNAME_INDIAN_PIONEERS
	desc		= AUBM_LDESC_INDIAN_PIONEERS
	short_desc	= AUBM_SDESC_INDIAN_PIONEERS
	eyr			= 1
	sprite		= infantry
	transmute	= infantry
	gfx_prio	= 3
	infantry	= yes
	value		= 1.3
	list_prio	= 10
}
'@
}

$divisionTypesPath = Ensure-OverlayFile "db\units\division_types.txt"
$divisionTypes = [System.IO.File]::ReadAllText($divisionTypesPath, $encoding)
$topLevelBefore = @(
    [regex]::Matches($divisionTypes, '(?m)^[A-Za-z0-9_]+\s*=\s*\{') |
        ForEach-Object { $_.Value }
)

foreach ($entry in $unitTypes.GetEnumerator()) {
    $pattern = "(?ms)^$([regex]::Escape($entry.Key))\s*=\s*\{.*?^\}"
    $matches = [regex]::Matches($divisionTypes, $pattern)
    if ($matches.Count -ne 1) {
        throw "Expected exactly one $($entry.Key) block in division_types.txt; found $($matches.Count)."
    }
    $divisionTypes = [regex]::Replace(
        $divisionTypes,
        $pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $entry.Value.TrimEnd() },
        1
    )
}

$topLevelAfter = @(
    [regex]::Matches($divisionTypes, '(?m)^[A-Za-z0-9_]+\s*=\s*\{') |
        ForEach-Object { $_.Value }
)
if ($topLevelBefore.Count -ne $topLevelAfter.Count) {
    throw "Reserved-slot patch changed the number of division types."
}
Write-Cp1252Text -Path $divisionTypesPath -Text $divisionTypes

$modifierSources = [ordered]@{
    rsv_33 = "MTN"
    rsv_34 = "MTN"
    rsv_35 = "MTN"
    rsv_36 = "PARA"
    rsv_37 = "MAR"
    rsv_38 = "ARM"
    rsv_39 = "MOT"
    rsv_40 = "INF"
}

$modifiersPath = Ensure-OverlayFile "db\units\modifiers.csv"
$modifierLines = [System.IO.File]::ReadAllLines($modifiersPath, $encoding)
if ($modifierLines.Count -lt 2) {
    throw "Malformed modifiers.csv: $modifiersPath"
}
$header = [regex]::Split($modifierLines[0], ';')
$columnIndex = @{}
for ($index = 0; $index -lt $header.Count; $index++) {
    $columnIndex[$header[$index]] = $index
}
foreach ($entry in $modifierSources.GetEnumerator()) {
    if (-not $columnIndex.ContainsKey($entry.Key) -or -not $columnIndex.ContainsKey($entry.Value)) {
        throw "modifiers.csv lacks $($entry.Key) or source column $($entry.Value)."
    }
}

for ($lineIndex = 1; $lineIndex -lt $modifierLines.Count; $lineIndex++) {
    if ([string]::IsNullOrWhiteSpace($modifierLines[$lineIndex])) {
        continue
    }
    $fields = [regex]::Split($modifierLines[$lineIndex], ';')
    if ($fields.Count -ne $header.Count) {
        throw "modifiers.csv column mismatch on line $($lineIndex + 1)."
    }
    foreach ($entry in $modifierSources.GetEnumerator()) {
        $fields[$columnIndex[$entry.Key]] = $fields[$columnIndex[$entry.Value]]
    }
    $modifierLines[$lineIndex] = $fields -join ';'
}
[System.IO.File]::WriteAllText(
    $modifiersPath,
    (($modifierLines -join "`r`n").TrimEnd() + "`r`n"),
    $encoding
)

$counterPath = Ensure-OverlayFile "gfx\map\hoi_counter_strip.bmp"
$bytes = [System.IO.File]::ReadAllBytes($counterPath)
if ($bytes.Length -lt 54 -or $bytes[0] -ne 0x42 -or $bytes[1] -ne 0x4D) {
    throw "Counter strip is not a Windows BMP: $counterPath"
}
$pixelOffset = [BitConverter]::ToInt32($bytes, 10)
$width = [BitConverter]::ToInt32($bytes, 18)
$height = [Math]::Abs([BitConverter]::ToInt32($bytes, 22))
$bitsPerPixel = [BitConverter]::ToUInt16($bytes, 28)
$compression = [BitConverter]::ToInt32($bytes, 30)
if ($bitsPerPixel -ne 8 -or $compression -ne 0) {
    throw "Counter strip must be an uncompressed 8-bit indexed BMP."
}

$tileWidth = 32
$requiredWidth = 41 * $tileWidth
if ($width -lt $requiredWidth) {
    throw "Counter strip width $width cannot hold reserved unit ID 40."
}
$stride = [int]([Math]::Ceiling(($width * $bitsPerPixel) / 32.0) * 4)
if ($pixelOffset + ($stride * $height) -gt $bytes.Length) {
    throw "Counter strip pixel data is truncated."
}

# Destination IDs remain unique engine slots. These source NATO symbols are
# safe fallbacks until each d_rsv sprite family receives bespoke counter art.
$counterSources = [ordered]@{
    33 = 8  # mountain
    34 = 8  # mountain
    35 = 8  # mountain
    36 = 6  # airborne
    37 = 7  # marine
    38 = 5  # armour
    39 = 2  # motorised
    40 = 0  # infantry
}
foreach ($entry in $counterSources.GetEnumerator()) {
    for ($row = 0; $row -lt $height; $row++) {
        $rowOffset = $pixelOffset + ($row * $stride)
        [Array]::Copy(
            $bytes,
            $rowOffset + ([int]$entry.Value * $tileWidth),
            $bytes,
            $rowOffset + ([int]$entry.Key * $tileWidth),
            $tileWidth
        )
    }
}
[System.IO.File]::WriteAllBytes($counterPath, $bytes)

$localizationSourcePaths = @(
    (Join-Path $overlayRoot "config\aubm_special_units.csv"),
    (Join-Path $overlayRoot "config\aubm_special_unit_models.csv")
)
$localizationRows = [Collections.Generic.List[string]]::new()
$managedLocalizationKeys = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($localizationSourcePath in $localizationSourcePaths) {
    if (-not (Test-Path -LiteralPath $localizationSourcePath -PathType Leaf)) {
        throw "Special-unit localization source is missing: $localizationSourcePath"
    }
    foreach ($line in [System.IO.File]::ReadAllLines($localizationSourcePath, $encoding)) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            continue
        }
        $fields = [regex]::Split($line, ';')
        if ($fields.Count -ne 12 -or $fields[11] -ne "X") {
            throw "Malformed special-unit localization row: $line"
        }
        if (-not $managedLocalizationKeys.Add($fields[0])) {
            throw "Duplicate special-unit localization key: $($fields[0])"
        }
        $localizationRows.Add($line)
    }
}

# Darkest Hour resolves division-type and model keys through unit_names.csv.
# Keep the dedicated file as source of truth, then publish into that table.
$unitNamesPath = Ensure-OverlayFile "config\unit_names.csv"
$localizationBegin = "# AUBM SPECIAL UNIT LOCALIZATION BEGIN;;;;;;;;;;;X"
$localizationEnd = "# AUBM SPECIAL UNIT LOCALIZATION END;;;;;;;;;;;X"
$extraLines = [Collections.Generic.List[string]]::new()
$insideManagedBlock = $false
foreach ($line in [System.IO.File]::ReadAllLines($unitNamesPath, $encoding)) {
    if ($line -eq $localizationBegin) {
        $insideManagedBlock = $true
        continue
    }
    if ($line -eq $localizationEnd) {
        $insideManagedBlock = $false
        continue
    }
    if ($insideManagedBlock -or $line.StartsWith("#EOF")) {
        continue
    }
    $key = ([regex]::Split($line, ';'))[0]
    if ($managedLocalizationKeys.Contains($key)) {
        continue
    }
    $extraLines.Add($line)
}
while ($extraLines.Count -gt 0 -and [string]::IsNullOrWhiteSpace($extraLines[$extraLines.Count - 1])) {
    $extraLines.RemoveAt($extraLines.Count - 1)
}
$extraLines.Add($localizationBegin)
foreach ($line in $localizationRows) {
    $extraLines.Add($line)
}
$extraLines.Add($localizationEnd)
$extraLines.Add("#EOF;;;;;;;;;;;X")
Write-Cp1252Text -Path $unitNamesPath -Text ($extraLines -join "`r`n")

$requiredFiles = @(
    "config\aubm_special_units.csv",
    "config\aubm_special_unit_models.csv",
    "config\unit_names.csv",
    "db\events\aubm_v4\40_special_units_and_capital_ships.txt",
    "db\tech\infantry_tech.txt",
    "db\tech\armor_tech.txt"
)
$requiredFiles += 33..40 | ForEach-Object { "db\units\divisions\d_rsv_$_.txt" }
foreach ($relativePath in $requiredFiles) {
    $path = Join-Path $overlayRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Special-unit source file is missing: $path"
    }
}

Write-Host "AUBM special units installed into reserved IDs 33-40."
Write-Host "  Division types: $divisionTypesPath"
Write-Host "  Terrain modifiers: $modifiersPath"
Write-Host "  Counter fallbacks: $counterPath"
Write-Host "  Loaded localization: $unitNamesPath"
Write-Host "  Model panels: omitted; engine missing-art placeholder applies to reserved models 33-40"
