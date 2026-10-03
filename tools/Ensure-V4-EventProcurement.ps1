param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$eventRoots = @(
    (Join-Path $root "mod\db\events\india_v3"),
    (Join-Path $root "mod\db\events\aubm_v4")
)

# Each command authorizes one current-model formation. Daily IC remains the
# researched model's normal cost, while `where` records meaningful funded
# progress. Larger packages use separate named commands, never hidden serials.
$remainingDays = @{
    infantry = 75
    cavalry = 90
    motorized = 105
    mechanized = 135
    light_armor = 135
    armor = 165
    paratrooper = 120
    marine = 105
    bergsjaeger = 105
    garrison = 60
    hq = 120
    militia = 45
    multi_role = 90
    interceptor = 75
    strategic_bomber = 135
    tactical_bomber = 105
    naval_bomber = 105
    cas = 90
    transport_plane = 120
    battleship = 360
    light_cruiser = 150
    heavy_cruiser = 210
    battlecruiser = 330
    destroyer = 90
    carrier = 330
    escort_carrier = 210
    submarine = 90
    transport = 105
    light_carrier = 270
}

$changedFiles = 0
$normalizedOrders = 0
$collapsedSerials = 0
$verifiedOrders = 0
$approvedShbbOrders = 0

foreach ($eventRoot in $eventRoots) {
    if (-not (Test-Path -LiteralPath $eventRoot -PathType Container)) {
        continue
    }

    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $lines = [System.IO.File]::ReadAllLines($file.FullName, $encoding)
        $changed = $false
        $insideApprovedShbbContract = $false

        for ($index = 0; $index -lt $lines.Count; $index++) {
            $line = $lines[$index]
            if ($line -match 'AUBM_APPROVED_SHBB_HALF_COMPLETE_BEGIN') {
                if ($insideApprovedShbbContract) {
                    throw "Nested approved SHBB marker: $($file.FullName):$($index + 1)"
                }
                $insideApprovedShbbContract = $true
                continue
            }
            if ($line -match 'AUBM_APPROVED_SHBB_HALF_COMPLETE_END') {
                if (-not $insideApprovedShbbContract) {
                    throw "Unmatched approved SHBB end marker: $($file.FullName):$($index + 1)"
                }
                $insideApprovedShbbContract = $false
                continue
            }
            if ($line -notmatch '\btype\s*=\s*build_division\b') {
                continue
            }

            $verifiedOrders++
            if ($line -match '\bcost\s*=') {
                throw "Fixed-cost event production order remains: $($file.FullName):$($index + 1)"
            }
            if ($line -notmatch '\bwhich\s*=\s*([A-Za-z0-9_]+)') {
                throw "Malformed event production order: $($file.FullName):$($index + 1)"
            }

            $unitType = $Matches[1]
            if ($insideApprovedShbbContract) {
                if (
                    $unitType -ne "battleship" -or
                    $line -notmatch '\bwhen\s*=\s*1\b' -or
                    $line -notmatch '\bwhere\s*=\s*420\b'
                ) {
                    throw "Malformed approved half-complete SHBB contract: $($file.FullName):$($index + 1)"
                }
                $approvedShbbOrders++
                continue
            }
            if (-not $remainingDays.ContainsKey($unitType)) {
                throw "No first-item procurement schedule for '$unitType': $($file.FullName):$($index + 1)"
            }

            $days = $remainingDays[$unitType]
            if ($line -match '\bwhen\s*=\s*\d+') {
                if ($line -notmatch '\bwhen\s*=\s*1\b') {
                    $collapsedSerials++
                }
                $line = $line -replace '\bwhen\s*=\s*\d+', "when = 1"
            }
            else {
                $line = $line -replace '\s*}\s*$', " when = 1 }"
            }
            if ($line -match '\bwhere\s*=\s*\d+') {
                $lines[$index] = $line -replace '\bwhere\s*=\s*\d+', "where = $days"
            }
            else {
                $lines[$index] = $line -replace '\s*}\s*$', " where = $days }"
            }
            $normalizedOrders++
            $changed = $true
        }

        if ($changed) {
            [System.IO.File]::WriteAllText(
                $file.FullName,
                (($lines -join "`r`n").TrimEnd() + "`r`n"),
                $encoding
            )
            $changedFiles++
        }

        if ($insideApprovedShbbContract) {
            throw "Unclosed approved SHBB marker: $($file.FullName)"
        }
    }
}

if ($approvedShbbOrders -ne 2) {
    throw "Expected exactly two approved half-complete SHBB contracts; found $approvedShbbOrders."
}

Write-Host (
    "Verified $verifiedOrders event production orders; collapsed $collapsedSerials hidden " +
    "serials and assigned normal-cost funded progress to $normalizedOrders single-unit " +
    "contracts in $changedFiles files; preserved $approvedShbbOrders approved SHBB contracts."
)
