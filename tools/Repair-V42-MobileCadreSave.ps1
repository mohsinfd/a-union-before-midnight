param(
    [Parameter(Mandatory = $true)]
    [string]$SavePath,
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$source = [System.IO.Path]::GetFullPath($SavePath)
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Save file not found: $source"
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $directory = Split-Path -Parent $source
    $name = [System.IO.Path]::GetFileNameWithoutExtension($source)
    $OutputPath = Join-Path $directory ($name + "_AUBM_v42_alpha3_repaired.eug")
}
$destination = [System.IO.Path]::GetFullPath($OutputPath)
if (Test-Path -LiteralPath $destination) {
    throw "Refusing to overwrite existing repaired save: $destination"
}
$sourceConfig = $source + ".cfg"
$destinationConfig = $destination + ".cfg"
if (-not (Test-Path -LiteralPath $sourceConfig -PathType Leaf)) {
    throw "Companion save configuration not found: $sourceConfig"
}
if (Test-Path -LiteralPath $destinationConfig) {
    throw "Refusing to overwrite existing repaired save configuration: $destinationConfig"
}

function Find-BlockEnd {
    param([string]$Text, [int]$Start)
    $depth = 0
    $opened = $false
    for ($index = $Start; $index -lt $Text.Length; $index++) {
        $character = $Text[$index]
        if ($character -eq '{') {
            $depth++
            $opened = $true
        }
        elseif ($character -eq '}') {
            $depth--
            if ($opened -and $depth -eq 0) {
                return $index + 1
            }
        }
    }
    throw "Unterminated save block beginning at character $Start."
}

$text = [System.IO.File]::ReadAllText($source, $encoding)
if ($text -notmatch '\bsaved\s*=\s*IND\b') {
    throw "Save is not an India player save."
}
if ($text -notmatch '(?m)^\s*ind_v3_mobile_army\s*=\s*1\s*$') {
    throw "Save did not choose the 1934 mobile-army rearmament path."
}
if ($text -match '(?m)^\s*aubm_v42_mobile_cadre_repair\s*=') {
    throw "Save already contains the mobile-cadre repair marker."
}

$countryMatch = [regex]::Match($text, '(?m)^country\s*=\s*\{\s*\r?\n\s*tag\s*=\s*IND\s*$')
if (-not $countryMatch.Success) {
    throw "Could not locate the India country block."
}
$countryStart = $countryMatch.Index
$countryEnd = Find-BlockEnd -Text $text -Start $countryStart
$country = $text.Substring($countryStart, $countryEnd - $countryStart)

$developmentMatches = [regex]::Matches($country, '(?m)^\s*division_development\s*=\s*\{')
$targets = [System.Collections.Generic.List[object]]::new()
foreach ($match in $developmentMatches) {
    $end = Find-BlockEnd -Text $country -Start $match.Index
    $block = $country.Substring($match.Index, $end - $match.Index)
    $isCavalry = $block -match '(?m)^\s*type\s*=\s*cavalry\s*$' -and
        $block -match '(?m)^\s*extra\s*=\s*armored_car\s*$'
    $isInfantry = $block -match '(?m)^\s*type\s*=\s*infantry\s*$' -and
        $block -match '(?m)^\s*extra\s*=\s*tank_destroyer\s*$'
    if (-not ($isCavalry -or $isInfantry)) {
        continue
    }
    if ($block -match '(?m)^\s*name\s*=') {
        continue
    }
    $manpowerMatch = [regex]::Match($block, '(?m)^\s*manpower\s*=\s*([0-9.]+)\s*$')
    $sizeMatch = [regex]::Match($block, '(?m)^\s*size\s*=\s*(\d+)\s*$')
    if (-not $manpowerMatch.Success -or -not $sizeMatch.Success) {
        throw "Candidate rearmament queue entry has no manpower or serial size."
    }
    $targets.Add([pscustomobject]@{
        Start = $match.Index
        End = $end
        Type = $(if ($isCavalry) { "cavalry" } else { "infantry" })
        Refund = [decimal]::Parse($manpowerMatch.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture) *
            [int]$sizeMatch.Groups[1].Value
    })
}

if (($targets | Where-Object Type -eq 'cavalry').Count -ne 1 -or
    ($targets | Where-Object Type -eq 'infantry').Count -ne 1) {
    throw "Expected exactly one cavalry and one infantry rearmament queue line; found $($targets.Count) candidates."
}

$refund = ($targets | Measure-Object -Property Refund -Sum).Sum
foreach ($target in ($targets | Sort-Object Start -Descending)) {
    $country = $country.Remove($target.Start, $target.End - $target.Start)
}

$manpowerMatch = [regex]::Match($country, '(?m)^\tmanpower\s*=\s*([0-9.]+)\s*$')
if (-not $manpowerMatch.Success) {
    throw "Could not locate India's top-level manpower pool."
}
$currentManpower = [decimal]::Parse($manpowerMatch.Groups[1].Value, [Globalization.CultureInfo]::InvariantCulture)
$newManpower = $currentManpower + $refund
$replacement = "`tmanpower = " + $newManpower.ToString('0.0000', [Globalization.CultureInfo]::InvariantCulture) + " "
$country = $country.Remove($manpowerMatch.Index, $manpowerMatch.Length).Insert($manpowerMatch.Index, $replacement)

$text = $text.Remove($countryStart, $countryEnd - $countryStart).Insert($countryStart, $country)
$flagMatch = [regex]::Match($text, '(?m)^(\s*)ind_v3_mobile_army\s*=\s*1\s*$')
if (-not $flagMatch.Success) {
    throw "Could not place the repair marker beside the mobile-army flag."
}
$marker = $flagMatch.Value + "`r`n" + $flagMatch.Groups[1].Value + "aubm_v42_mobile_cadre_repair = 1"
$text = $text.Remove($flagMatch.Index, $flagMatch.Length).Insert($flagMatch.Index, $marker)

$destinationOption = "scenarios\save games\" + [System.IO.Path]::GetFileName($destinationConfig)
$optionMatch = [regex]::Match($text, '(?m)^\s*optionfile\s*=\s*"[^"]+"\s*$')
if (-not $optionMatch.Success) {
    throw "Could not update the companion save-configuration reference."
}
$optionIndent = [regex]::Match($optionMatch.Value, '^\s*').Value
$optionLine = $optionIndent + 'optionfile = "' + $destinationOption + '" '
$text = $text.Remove($optionMatch.Index, $optionMatch.Length).Insert($optionMatch.Index, $optionLine)

[System.IO.File]::WriteAllText($destination, $text, $encoding)
[System.IO.File]::Copy($sourceConfig, $destinationConfig)
Write-Host "Created repaired save: $destination"
Write-Host "Removed 2 obsolete production lines and refunded $refund manpower; the four 40% cadres will assemble after load."
