param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$limits = @{
    "air_base" = 10
    "coastal_fort" = 10
    "flak" = 10
    "infrastructure" = 100
    "land_fort" = 10
    "naval_base" = 10
    "nuclear_reactor" = 10
    "radar_station" = 10
    "rocket_test" = 10
}
$eventRoots = @(
    (Join-Path $root "mod\db\events\india_v3"),
    (Join-Path $root "mod\db\events\aubm_v4")
)
$pattern = [regex]::new(
    '^(?<indent>\s*)command\s*=\s*\{\s*type\s*=\s*construct\s+' +
    'which\s*=\s*(?<kind>[A-Za-z0-9_]+)\s+' +
    'where\s*=\s*(?<province>-?\d+)\s+' +
    'value\s*=\s*(?<amount>\d+)' +
    '(?:\s+trigger\s*=\s*\{.*\})?\s*\}' +
    '(?<comment>\s*(?:#.*)?)$',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)

function Get-Threshold {
    param(
        [string]$Kind,
        [int]$Amount
    )

    $limit = [int]$limits[$Kind]
    if ($Amount -gt $limit) {
        throw "$Kind construction amount $Amount exceeds cap $limit."
    }
    if ($Kind -eq "infrastructure") {
        $threshold = 1.0 - ($Amount / 100.0) + 0.01
        return $threshold.ToString("0.##", [System.Globalization.CultureInfo]::InvariantCulture)
    }
    return [string]($limit - $Amount + 1)
}

$updatedFiles = 0
$updatedCommands = 0
foreach ($eventRoot in $eventRoots) {
    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $lines = [System.IO.File]::ReadAllLines($file.FullName, $encoding)
        $changed = $false
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $match = $pattern.Match($lines[$i])
            if (-not $match.Success) {
                continue
            }

            $kind = $match.Groups["kind"].Value.ToLowerInvariant()
            $province = [int]$match.Groups["province"].Value
            $amount = [int]$match.Groups["amount"].Value
            if ($province -le 0) {
                continue
            }

            $guards = "owned = { province = $province data = IND }"
            if ($limits.ContainsKey($kind)) {
                $threshold = Get-Threshold -Kind $kind -Amount $amount
                $guards += " NOT = { building = { province = $province type = $kind value = $threshold } }"
            }

            $safeLine = (
                $match.Groups["indent"].Value +
                "command = { type = construct which = $kind where = $province value = $amount " +
                "trigger = { $guards } }" +
                $match.Groups["comment"].Value
            )
            if ($safeLine -ne $lines[$i]) {
                $lines[$i] = $safeLine
                $changed = $true
                $updatedCommands++
            }
        }

        if ($changed) {
            [System.IO.File]::WriteAllText(
                $file.FullName,
                (($lines -join "`r`n").TrimEnd() + "`r`n"),
                $encoding
            )
            $updatedFiles++
        }
    }
}

Write-Host "Newly secured $updatedCommands construction commands across $updatedFiles event files."
