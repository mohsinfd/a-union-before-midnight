param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$path = Join-Path ([System.IO.Path]::GetFullPath($RepositoryRoot)) "mod\db\misc.txt"
$encoding = [System.Text.Encoding]::GetEncoding(1252)
$text = [System.IO.File]::ReadAllText($path, $encoding)

function Set-ValueAfterComment {
    param(
        [string]$Comment,
        [string]$Value
    )

    $escaped = [regex]::Escape($Comment)
    $pattern = "(?m)(^# $escaped[ \t]*\r?\n)[^\r\n]+"
    $matches = [regex]::Matches($script:text, $pattern)
    if ($matches.Count -ne 1) {
        throw "Expected one misc.txt setting for '$Comment', found $($matches.Count)."
    }
    $script:text = [regex]::Replace(
        $script:text,
        $pattern,
        "`${1}`t$Value",
        1
    )
}

Set-ValueAfterComment `
    "Upgrade cost" `
    "0.5 # AUBM V4.2: paid upgrades use the Darkest Hour baseline cost"
Set-ValueAfterComment `
    "Upgrade time" `
    "0.5 # AUBM V4.2: paid upgrades use the Darkest Hour baseline time"
Set-ValueAfterComment `
    "Reinforce to upgrade modifier. Values from 0.0 (divisions do not get extra upgrade progress on reinforcement) to 1.0 (1:1 ratio, 1% reinforce adds 1% to upgrade progress)" `
    "0.0 # AUBM V4.2: reinforcement does not bypass the upgrade budget"
Set-ValueAfterComment `
    "Added extra upgrade progress to units in supply. Added daily progress to all units in supply that can upgrade is equal to Cur_STR/(Max_STR * THIS). Added value is not affected by any other upgrade modifiers. Set to 0 to disable this functionality." `
    "0 # AUBM V4.2: zero upgrade IC means zero upgrade progress"

Set-ValueAfterComment `
    "Carriers vs. Bases - Str dmg - Increasing this will increase the STR damage inflicted by carriers to enemy units while attacking enemy bases [multiplier]" `
    "1.2 # AUBM V4: base raids disrupt more often than they erase entire wings"
Set-ValueAfterComment `
    "Air vs. Navy - Critical hit chance - Chance for air units to inflict a critical hit (extra STR damage) to ships - checked for each hit inflicted in combat. 0-100 (0 - No critical hits ever, 100 - Every hit is critical)" `
    "5 # AUBM V4: rare decisive hits remain possible"
Set-ValueAfterComment `
    "Air vs. Navy - Str dmg modifier for critical hits inflicted in combats (see above) [multiplier]" `
    "6.0 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Navy - Critical hit chance - Chance for naval units to inflict a critical hit (extra STR damage) to other ships - checked for each hit inflicted in combat. 0-100 (0 - No critical hits ever, 100 - Every hit is critical)" `
    "6 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Navy - Str dmg modifier for critical hits inflicted in combats (see above) [multiplier]" `
    "6.0 # AUBM V4"

Set-ValueAfterComment `
    "Air vs. Air - Org dmg - Increasing this will increase ORG damage air unit takes in battle with other air units [multiplier]" `
    "0.55 # AUBM V4: wings disengage through lost cohesion before destruction"
Set-ValueAfterComment `
    "Air vs. Air - Str dmg - Increasing this will increase STR damage air unit takes in battle with other air units [multiplier]" `
    "0.45 # AUBM V4"
Set-ValueAfterComment `
    "Air vs Navy - Org dmg - Increasing this will increase ORG damage naval unit takes from air units [multiplier]" `
    "1.8 # AUBM V4"
Set-ValueAfterComment `
    "Air vs. Navy - Str dmg - Increasing this will increase STR damage naval unit takes from air units [multiplier]" `
    "0.40 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Air - Org dmg - Increasing this will increase ORG damage air unit takes from naval units [multiplier]" `
    "0.32 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Air - Str dmg - Increasing this will increase STR damage air unit takes from naval units [multiplier]" `
    "0.10 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Navy - Org dmg - Increasing this will increase ORG damage naval unit takes from other naval units [multiplier]" `
    "1.25 # AUBM V4"
Set-ValueAfterComment `
    "Navy vs. Navy - Str dmg - Increasing this will increase STR damage naval unit takes from other naval units [multiplier]" `
    "0.55 # AUBM V4"
Set-ValueAfterComment `
    "Auto-retreat from combat when average ORG for own or controlled units drop below THIS" `
    "12.0 # AUBM V4: recoverable defeat instead of routine annihilation"

$missionReplacements = @{
    '(?ms)(# _MISSION_REBASE_\r?\n)\s*1\s*[^\r\n]*\r?\n\s*1\.0\s*[^\r\n]*\r?\n\s*1\.0\s*[^\r\n]*' =
        "`${1}`t1 `t# enabled by default`r`n`t1.0`t# Starting missions efficiency`r`n`t0.65`t# AUBM V4: faster emergency ferry and fleet withdrawal orders"
    '(?ms)(# _MISSION_SUPPORT_DEFENSE_\r?\n)\s*1\s*[^\r\n]*\r?\n\s*1\.0\s*[^\r\n]*\r?\n\s*0\.5\s*[^\r\n]*' =
        "`${1}`t1 `t# enabled by default`r`n`t1.0`t# Starting missions efficiency`r`n`t0.35`t# AUBM V4: faster reaction by designated reserves"
    '(?ms)(# _MISSION_RESERVES_\r?\n)\s*1\s*[^\r\n]*\r?\n\s*1\.0\s*[^\r\n]*\r?\n\s*0\.5\s*[^\r\n]*' =
        "`${1}`t1 `t# enabled by default`r`n`t1.0`t# Starting missions efficiency`r`n`t0.35`t# AUBM V4: faster movement by operational reserves"
    '(?ms)(# _MISSION_AIR_SCRAMBLE_\r?\n)\s*0\s*[^\r\n]*\r?\n\s*0\.5\s*[^\r\n]*\r?\n\s*0\.0\s*[^\r\n]*\r?\n\s*2\.0\s*[^\r\n]*' =
        "`${1}`t1 `t# AUBM V4: available from the start`r`n`t0.75`t# Starting missions efficiency`r`n`t5.0`t# Radar and observers guide defensive interception`r`n`t0.9`t# Min. air attack required"
    '(?ms)(# _MISSION_NAVAL_SCRAMBLE_\r?\n)\s*0\s*[^\r\n]*\r?\n\s*0\.5\s*[^\r\n]*\r?\n\s*0\.5\s*[^\r\n]*' =
        "`${1}`t1 `t# AUBM V4: available from the start`r`n`t0.6`t# Starting missions efficiency`r`n`t0.4`t# Faster harbour response"
}

foreach ($entry in $missionReplacements.GetEnumerator()) {
    $matches = [regex]::Matches($text, $entry.Key)
    if ($matches.Count -ne 1) {
        throw "Expected one mission block for pattern '$($entry.Key)', found $($matches.Count)."
    }
    $text = [regex]::Replace($text, $entry.Key, $entry.Value, 1)
}

[System.IO.File]::WriteAllText($path, $text, $encoding)
Write-Host "Applied AUBM V4 combat pacing to $path"
