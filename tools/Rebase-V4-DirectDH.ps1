param(
    [string]$GameRoot,
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
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

function Write-Text {
    param([string]$Path, [string[]]$Lines)

    [System.IO.File]::WriteAllLines(
        $Path,
        $Lines,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

function Copy-StockFile {
    param([string]$RelativePath)

    $source = Join-Path $script:StockRoot $RelativePath
    $target = Join-Path $script:OverlayRoot $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required Darkest Hour Full file is missing: $source"
    }
    $targetDirectory = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $target -Force
}

function Replace-TaggedRowsWithOverlayRows {
    param(
        [string]$RelativePath,
        [string]$Tag
    )

    $overlayPath = Join-Path $script:OverlayRoot $RelativePath
    $preservedRows = @(
        Get-Content -LiteralPath $overlayPath |
            Where-Object { $_ -like "$Tag;*" }
    )
    if ($preservedRows.Count -eq 0) {
        throw "No $Tag rows found to preserve in $RelativePath"
    }

    Copy-StockFile $RelativePath
    $stockRows = @(
        Get-Content -LiteralPath $overlayPath |
            Where-Object { $_ -notlike "$Tag;*" }
    )

    if ($RelativePath -eq "db\country.csv") {
        $endIndex = [Array]::IndexOf($stockRows, "END;DarkGreen;ENG;ENG;;;;X")
        if ($endIndex -lt 0) {
            throw "Could not locate the country.csv END row."
        }
        $merged = @($stockRows[0..($endIndex - 1)] + $preservedRows + $stockRows[$endIndex..($stockRows.Count - 1)])
    } else {
        $merged = @($stockRows + $preservedRows)
    }
    Write-Text -Path $overlayPath -Lines $merged
}

function Add-IndiaPersonalityDefinitions {
    $relativePath = "db\ministers\minister_personalities.txt"
    $overlayPath = Join-Path $script:OverlayRoot $relativePath
    $current = Get-Content -LiteralPath $overlayPath
    $marker = "####### India Mod V3: historical and alternate-history personalities #########"
    $markerIndex = [Array]::IndexOf($current, $marker)
    if ($markerIndex -lt 0) {
        throw "India minister personality block was not found."
    }
    $indiaBlock = @($current[$markerIndex..($current.Count - 1)])

    Copy-StockFile $relativePath
    $stock = @(Get-Content -LiteralPath $overlayPath)
    Write-Text -Path $overlayPath -Lines @($stock + "" + $indiaBlock)
}

function Disable-GenericPurgeForIndia {
    $relativePath = "db\events\generic_decisions.txt"
    Copy-StockFile $relativePath
    $path = Join-Path $script:OverlayRoot $relativePath
    $text = Get-Content -LiteralPath $path -Raw
    $start = $text.IndexOf("#### Purge the Army")
    $end = $text.IndexOf("####", $start + 5)
    if ($start -lt 0 -or $end -lt 0) {
        throw "Could not isolate the generic Purge the Army event."
    }
    $prefix = $text.Substring(0, $start)
    $block = $text.Substring($start, $end - $start)
    $suffix = $text.Substring($end)

    $block = $block.Replace(
        "NOT = { country = SOV }",
        "NOT = { country = SOV }`r`n`t`tNOT = { country = IND }"
    )
    $block = $block.Replace(
        "decision_trigger = { `r`n`t`tNOT = { government = democratic }",
        "decision_trigger = { `r`n`t`tNOT = { country = IND }`r`n`t`tNOT = { government = democratic }"
    )
    [System.IO.File]::WriteAllText(
        $path,
        $prefix + $block + $suffix,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

function Build-EventsIndex {
    Copy-StockFile "db\events.txt"
    $path = Join-Path $script:OverlayRoot "db\events.txt"
    $lines = @(Get-Content -LiteralPath $path)
    $lines += ""
    $lines += "# A Union Before Midnight: India"
    foreach ($name in @(
        "00_bootstrap.txt",
        "10_politics.txt",
        "12_society.txt",
        "20_development.txt",
        "21_fallbacks.txt",
        "22_resources.txt",
        "30_military.txt",
        "31_air_force.txt",
        "32_navy.txt",
        "33_command_research.txt",
        "34_elite_forces.txt",
        "40_diplomacy.txt",
        "46_world_reactions.txt",
        "41_allied.txt",
        "42_axis.txt",
        "43_soviet.txt",
        "44_non_aligned.txt",
        "45_japan.txt",
        "47_revisionist_aftermath.txt",
        "50_wartime.txt",
        "51_theatres.txt",
        "52_home_front.txt",
        "60_postwar.txt",
        "61_cold_war.txt",
        "62_victory.txt"
    )) {
        $lines += "event = `"db\events\india_v3\$name`""
    }
    $lines += ""
    $lines += "# A Union Before Midnight V4: direct-DH systems"
    foreach ($name in @(
        "00_world_bootstrap.txt",
        "05_union_integration.txt",
        "10_world_reactions.txt",
        "15_operational_command.txt",
        "20_procurement.txt",
        "30_war_settlements.txt"
    )) {
        $lines += "event = `"db\events\aubm_v4\$name`""
    }
    Write-Text -Path $path -Lines $lines
}

function Build-Scenario {
    Copy-StockFile "scenarios\1933.eug"
    $path = Join-Path $script:OverlayRoot "scenarios\1933.eug"
    $text = Get-Content -LiteralPath $path -Raw
    $header = @'
header =
{ name       = "A Union Before Midnight: India 1933"
  startdate  = { year = 1933 }
  selectable = { IND }
  IND        = { picture = "scenarios\data\propaganda_IND_V3.bmp" }
}
globaldata =
'@
    $text = [regex]::Replace(
        $text,
        '(?s)header\s*=\s*\{.*?\r?\n\}\r?\nglobaldata\s*=\s*',
        $header + "`r`n",
        1
    )
    $text = $text.Replace(
        "startdate = { year = 1933 month = march day = 3 }",
        "startdate = { year = 1933 month = january day = 0 }"
    )
    $text = [regex]::Replace(
        $text,
        'participant\s*=\s*\{\s*ENG FRA BEL AST NZL CAN SAF NEP EGY U60\s*\}',
        'participant = { ENG FRA BEL AST NZL CAN SAF EGY U60 }',
        1
    )
    [System.IO.File]::WriteAllText(
        $path,
        $text,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

function Build-UnitedKingdomScenario {
    Copy-StockFile "scenarios\1933\united kingdom.inc"
    $path = Join-Path $script:OverlayRoot "scenarios\1933\united kingdom.inc"
    $text = Get-Content -LiteralPath $path -Raw

    $text = [regex]::Replace(
        $text,
        '(?s)\s*landunit\s*=\s*\{\s*name\s*=\s*"Ceylon Command".*?\n\s*\}\s*(?=landunit\s*=)',
        "`r`n   ",
        1
    )
    $text = $text.Replace(
        'name = "East Indies Station"',
        'name = "Singapore Station"'
    )
    $stationStart = $text.IndexOf('name = "Singapore Station"')
    if ($stationStart -lt 0) {
        throw "Could not locate the Royal Navy East Indies Station."
    }
    $stationEnd = $text.IndexOf("navalunit", $stationStart)
    if ($stationEnd -lt 0) {
        $stationEnd = $text.Length
    }
    $stationBlock = $text.Substring($stationStart, $stationEnd - $stationStart)
    $stationBlock = [regex]::Replace($stationBlock, 'location\s*=\s*\d+', 'location = 1435', 1)
    $stationBlock = [regex]::Replace($stationBlock, 'base\s*=\s*\d+', 'base = 1435', 1)
    $text = $text.Substring(0, $stationStart) + $stationBlock + $text.Substring($stationEnd)

    foreach ($province in 1509, 1510, 1511) {
        $text = [regex]::Replace($text, "(?<!\d)$province(?!\d)", "")
    }
    $text = $text.Replace("location =  ", "location = 1435")
    $text = $text.Replace("base =  ", "base = 1435")

    [System.IO.File]::WriteAllText(
        $path,
        $text,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

$GameRoot = Resolve-GameRoot $GameRoot
$script:StockRoot = Join-Path $GameRoot "Mods\Darkest Hour Full"
$repositoryFullPath = [System.IO.Path]::GetFullPath($RepositoryRoot)
$script:OverlayRoot = Join-Path $repositoryFullPath "mod"

if (-not (Test-Path -LiteralPath $script:StockRoot -PathType Container)) {
    throw "Darkest Hour Full was not found at: $script:StockRoot"
}
if (-not (Test-Path -LiteralPath $script:OverlayRoot -PathType Container)) {
    throw "Mod overlay was not found at: $script:OverlayRoot"
}

foreach ($nameFile in @(
    "db\airnames.csv",
    "db\armynames.csv",
    "db\navynames.csv",
    "db\unitnames.csv"
)) {
    Replace-TaggedRowsWithOverlayRows -RelativePath $nameFile -Tag "IND"
}
Replace-TaggedRowsWithOverlayRows -RelativePath "db\country.csv" -Tag "IND"

Add-IndiaPersonalityDefinitions
Disable-GenericPurgeForIndia
Build-EventsIndex
Build-Scenario
Build-UnitedKingdomScenario
Copy-StockFile "db\misc.txt"

& (Join-Path $repositoryFullPath "tools\Set-V4-CombatRules.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Set-V4-IndiaOOB.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-EventUnitAvailability.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-ConstructionSafety.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-EventPictures.ps1") -RepositoryRoot $repositoryFullPath -GameRoot $GameRoot

Write-Host "V4 overlay rebased onto Darkest Hour Full:"
Write-Host "  $script:OverlayRoot"
