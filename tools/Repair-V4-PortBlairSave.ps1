param(
    [Parameter(Mandatory = $true)]
    [string]$SavePath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$source = Get-Item -LiteralPath $SavePath
$sourceStamp = $source.LastWriteTimeUtc
$sourceLength = $source.Length
$text = [System.IO.File]::ReadAllText($source.FullName, $encoding)

function Get-BracedBlock {
    param(
        [string]$Content,
        [int]$Start
    )

    $open = $Content.IndexOf('{', $Start)
    if ($open -lt 0) {
        throw "Opening brace not found at offset $Start."
    }

    $depth = 0
    for ($index = $open; $index -lt $Content.Length; $index++) {
        switch ($Content[$index]) {
            '{' { $depth++ }
            '}' {
                $depth--
                if ($depth -eq 0) {
                    return [pscustomobject]@{
                        Start = $Start
                        End = $index + 1
                        Text = $Content.Substring($Start, $index + 1 - $Start)
                    }
                }
            }
        }
    }

    throw "Unclosed block at offset $Start."
}

$countryMatch = [regex]::Match($text, '(?m)^country = \{[ \t]*\r?\n[ \t]*tag = IND[ \t]*\r?$')
if (-not $countryMatch.Success) {
    throw "The save does not contain an India country block."
}
$country = Get-BracedBlock -Content $text -Start $countryMatch.Index

$provinceMatch = [regex]::Match($text, '(?m)^province = \{[ \t]*\r?\n[ \t]*id = 1421[ \t]*\r?$')
if (-not $provinceMatch.Success) {
    throw "Port Blair province 1421 was not found."
}
$province = Get-BracedBlock -Content $text -Start $provinceMatch.Index

$currentLevels = @{}
foreach ($type in @('air_base', 'naval_base')) {
    $levelMatch = [regex]::Match($province.Text, "(?m)^\s*$type = \{ size = (\d+)")
    if (-not $levelMatch.Success) {
        throw "Port Blair has no $type level in this save."
    }
    $currentLevels[$type] = [int]$levelMatch.Groups[1].Value
}

$developmentPattern = [regex]'(?m)^\s*province_development = \{'
$matches = $developmentPattern.Matches($country.Text)
$replacements = @()

foreach ($match in $matches) {
    $absoluteStart = $country.Start + $match.Index
    $block = Get-BracedBlock -Content $text -Start $absoluteStart
    if ($block.Text -notmatch '(?m)^\s*location = 1421\s*$') {
        continue
    }

    $typeMatch = [regex]::Match($block.Text, '(?m)^\s*type = (air_base|naval_base)\s*$')
    if (-not $typeMatch.Success) {
        continue
    }

    $type = $typeMatch.Groups[1].Value
    $sizeMatch = [regex]::Match($block.Text, '(?m)^\s*size = (\d+)\s*$')
    $doneMatch = [regex]::Match($block.Text, '(?m)^\s*done = (\d+)\s*$')
    if (-not $sizeMatch.Success) {
        throw "The Port Blair $type queue has no serial size."
    }

    $size = [int]$sizeMatch.Groups[1].Value
    $done = if ($doneMatch.Success) { [int]$doneMatch.Groups[1].Value } else { 0 }
    $remainingCapacity = [Math]::Max(0, 10 - $currentLevels[$type])
    $safeSize = $done + $remainingCapacity

    if ($safeSize -ge $size) {
        continue
    }
    if ($safeSize -le $done) {
        throw "The $type queue must be removed after the game is closed; no safe serial remains."
    }

    $relativeSizeStart = $sizeMatch.Groups[1].Index
    $absoluteSizeStart = $block.Start + $relativeSizeStart
    $replacements += [pscustomobject]@{
        Start = $absoluteSizeStart
        Length = $sizeMatch.Groups[1].Length
        Value = [string]$safeSize
        Type = $type
        Before = $size
        After = $safeSize
        Current = $currentLevels[$type]
        Done = $done
    }
}

if ($replacements.Count -ne 2) {
    throw "Expected two unsafe Port Blair base queues; found $($replacements.Count)."
}

foreach ($replacement in $replacements | Sort-Object Start -Descending) {
    $text = $text.Remove($replacement.Start, $replacement.Length).Insert($replacement.Start, $replacement.Value)
}

$outputName = [System.IO.Path]::GetFileName($OutputPath)
$text = [regex]::Replace(
    $text,
    'optionfile = "scenarios\\save games\\autosave\.eug\.cfg"',
    "optionfile = `"scenarios\save games\$outputName.cfg`"",
    1
)

$sourceAfter = Get-Item -LiteralPath $SavePath
if ($sourceAfter.LastWriteTimeUtc -ne $sourceStamp -or $sourceAfter.Length -ne $sourceLength) {
    throw "The live autosave changed during repair. Run the tool again on the newest save."
}

$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}
[System.IO.File]::WriteAllText($OutputPath, $text, $encoding)

$configPath = "$SavePath.cfg"
if (Test-Path -LiteralPath $configPath) {
    Copy-Item -LiteralPath $configPath -Destination "$OutputPath.cfg" -Force
}

Write-Host "Created repaired save: $OutputPath"
foreach ($replacement in $replacements | Sort-Object Type) {
    Write-Host ("  Port Blair {0}: level {1}, completed {2}, serial {3} -> {4}" -f `
        $replacement.Type, $replacement.Current, $replacement.Done, $replacement.Before, $replacement.After)
}
