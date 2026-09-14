[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$DivisionTypesPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($DivisionTypesPath)) {
    $DivisionTypesPath = Join-Path $RepositoryRoot "mod\db\units\division_types.txt"
}

$spriteKeys = [ordered]@{
    infantry          = "d_41"
    cavalry           = "d_42"
    motorized         = "d_43"
    mechanized        = "d_44"
    light_armor       = "d_45"
    armor             = "d_46"
    paratrooper       = "d_47"
    marine            = "d_48"
    bergsjaeger       = "d_49"
    garrison          = "d_50"
    hq                = "d_51"
    militia           = "d_52"
    multi_role        = "d_53"
    interceptor       = "d_54"
    strategic_bomber  = "d_55"
    tactical_bomber   = "d_56"
    naval_bomber      = "d_57"
    cas               = "d_58"
    transport_plane   = "d_59"
    flying_bomb       = "d_60"
    flying_rocket     = "d_61"
    battleship        = "d_62"
    light_cruiser     = "d_63"
    heavy_cruiser     = "d_64"
    battlecruiser     = "d_65"
    destroyer         = "d_66"
    carrier           = "d_67"
    escort_carrier    = "d_68"
    submarine         = "d_69"
    nuclear_submarine = "d_70"
    transport         = "d_71"
    light_carrier     = "d_72"
    rocket_interceptor = "d_73"
    d_rsv_33          = "d_74"
    d_rsv_34          = "d_75"
    d_rsv_35          = "d_76"
    d_rsv_36          = "d_77"
    d_rsv_37          = "d_78"
    d_rsv_38          = "d_79"
    d_rsv_39          = "d_80"
    d_rsv_40          = "d_81"
}

if (-not (Test-Path -LiteralPath $DivisionTypesPath -PathType Leaf)) {
    throw "Unit registry not found: $DivisionTypesPath"
}

$original = [IO.File]::ReadAllText($DivisionTypesPath)
$newline = if ($original.Contains("`r`n")) { "`r`n" } else { "`n" }
$hadFinalNewline = $original.EndsWith("`n")
$lines = [Collections.Generic.List[string]]::new()
$original -split "`r?`n" | ForEach-Object { [void]$lines.Add($_) }
if ($hadFinalNewline -and $lines.Count -gt 0 -and $lines[$lines.Count - 1] -eq "") {
    $lines.RemoveAt($lines.Count - 1)
}

$seenBlocks = @{}
$seenSpriteLines = @{}
$currentType = $null
$depth = 0
$changed = $false

for ($index = 0; $index -lt $lines.Count; $index++) {
    $line = $lines[$index]

    if ($null -eq $currentType) {
        $blockMatch = [regex]::Match($line, '^\s*([A-Za-z0-9_]+)\s*=\s*\{')
        if ($blockMatch.Success -and $spriteKeys.Contains($blockMatch.Groups[1].Value)) {
            $currentType = $blockMatch.Groups[1].Value
            if ($seenBlocks.ContainsKey($currentType)) {
                throw "Duplicate unit type block '$currentType' in $DivisionTypesPath"
            }
            $seenBlocks[$currentType] = 1
            $seenSpriteLines[$currentType] = 0
            $depth = ([regex]::Matches($line, '\{')).Count - ([regex]::Matches($line, '\}')).Count
        }
        continue
    }

    $spriteMatch = [regex]::Match($line, '^(\s*sprite\s*=\s*)(\S+)(.*)$', 'IgnoreCase')
    if ($spriteMatch.Success) {
        $seenSpriteLines[$currentType]++
        if ($seenSpriteLines[$currentType] -gt 1) {
            throw "Multiple sprite fields in unit type block '$currentType'"
        }
        $replacement = $spriteMatch.Groups[1].Value + $spriteKeys[$currentType] + $spriteMatch.Groups[3].Value
        if ($replacement -cne $line) {
            $lines[$index] = $replacement
            $changed = $true
        }
    }

    $depth += ([regex]::Matches($line, '\{')).Count - ([regex]::Matches($line, '\}')).Count
    if ($depth -eq 0) {
        if ($seenSpriteLines[$currentType] -ne 1) {
            throw "Expected exactly one sprite field in unit type block '$currentType'"
        }
        $currentType = $null
    }
    elseif ($depth -lt 0) {
        throw "Unbalanced braces while reading unit type block '$currentType'"
    }
}

if ($null -ne $currentType) {
    throw "Unclosed unit type block '$currentType'"
}

$missing = @($spriteKeys.Keys | Where-Object { -not $seenBlocks.ContainsKey($_) })
if ($missing.Count -gt 0) {
    throw "Missing required unit type block(s): $($missing -join ', ')"
}

if ($changed) {
    $updated = [string]::Join($newline, $lines)
    if ($hadFinalNewline) {
        $updated += $newline
    }
    [IO.File]::WriteAllText($DivisionTypesPath, $updated, [Text.Encoding]::ASCII)
    Write-Host "Assigned 41 independent India sprite keys in $DivisionTypesPath"
}
else {
    Write-Host "All 41 independent India sprite keys are already assigned."
}

[pscustomobject]@{
    Path = $DivisionTypesPath
    Changed = $changed
    Count = $spriteKeys.Count
    Mapping = $spriteKeys
}
