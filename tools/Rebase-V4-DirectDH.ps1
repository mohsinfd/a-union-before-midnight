param(
    [string]$GameRoot,
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$IncludePersonalSprites
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

function Exclude-IndiaFromGenericMobilization {
    $relativePath = "db\events\Mobilization.txt"
    Copy-StockFile $relativePath
    $path = Join-Path $script:OverlayRoot $relativePath
    $text = Get-Content -LiteralPath $path -Raw
    $updated = [regex]::Replace(
        $text,
        '(?<![A-Z0-9])IND(?![A-Z0-9])',
        ''
    )
    if ($updated -eq $text) {
        throw "India was not present in the generic mobilization TAG lists."
    }
    [System.IO.File]::WriteAllText(
        $path,
        $updated,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

function Exclude-IndiaFromGenericElections {
    $relativePath = "db\events\Election_day.txt"
    Copy-StockFile $relativePath
    $path = Join-Path $script:OverlayRoot $relativePath
    $text = Get-Content -LiteralPath $path -Raw
    $updated = [regex]::Replace(
        $text,
        '(?<![A-Z0-9])IND(?![A-Z0-9])',
        ''
    )
    if ($updated -eq $text) {
        throw "India was not present in the generic election TAG lists."
    }
    [System.IO.File]::WriteAllText(
        $path,
        $updated,
        [System.Text.Encoding]::GetEncoding(1252)
    )
}

function Add-SovereignIndiaToJapanAI {
    $relativePaths = @(
        "ai\jap_1933.ai",
        "ai\jap_1936.ai",
        "ai\jap_1939.ai",
        "ai\jap_1940.ai",
        "ai\switch\jap_backoff.ai",
        "ai\switch\jap_backoff2.ai",
        "ai\switch\jap_backoff2_siam.ai",
        "ai\switch\jap_backoff_remove.ai",
        "ai\switch\JAP_Backoff_Remove_Siam.ai",
        "ai\switch\jap_chc.ai",
        "ai\switch\jap_china.ai",
        "ai\switch\jap_naval_nei.ai",
        "ai\switch\JAP_Naval_PHI.ai"
    )

    foreach ($relativePath in $relativePaths) {
        Copy-StockFile $relativePath
        $path = Join-Path $script:OverlayRoot $relativePath
        $lines = @(Get-Content -LiteralPath $path)
        $updated = New-Object System.Collections.Generic.List[string]
        $replacements = 0
        foreach ($line in $lines) {
            $updated.Add($line)
            if ($line -match '^(\s*)U02\s*=\s*([^#\r\n]+)(.*)$') {
                $updated.Add("$($Matches[1])IND = $($Matches[2].Trim())$($Matches[3])")
                $replacements++
            }
        }
        if ($replacements -eq 0) {
            throw "Japan AI file has no British Raj U02 policy to mirror for India: $relativePath"
        }
        Write-Text -Path $path -Lines $updated
    }
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
        "12_campaign_systems.txt",
        "15_operational_command.txt",
        "18_manpower_reserves.txt",
        "20_procurement.txt",
        "22_crisis_interventions.txt",
        "25_global_war.txt",
        "26_grand_strategy.txt",
        "27_dynamic_strategy.txt",
        "28_foreign_responses.txt",
        "29_world_pressure.txt",
        "30_war_settlements.txt",
        "31_campaign_continuity.txt",
        "32_national_consolidation.txt",
        "35_japan_partnership.txt",
        "36_allied_campaigns.txt",
        "37_german_campaigns.txt",
        "38_soviet_campaigns.txt",
        "39_non_aligned_campaigns.txt",
        "40_special_units_and_capital_ships.txt",
        "41_wartime_state.txt",
        "42_wartime_theatres.txt",
        "43_wartime_settlements.txt",
        "44_wartime_economy.txt",
        "45_enemy_campaigns.txt",
        "46_regional_campaigns.txt",
		"47_global_campaign_matrix.txt",
		"48_route_wartime_consequences.txt",
		"49_bespoke_armistices.txt",
		"50_southeast_asia_operations.txt"
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

function Enable-NavalConversions {
    $routes = [ordered]@{
        "db\units\divisions\battleship.txt" = @(
            "upgrade = { type = carrier upgrade_time_factor = 0.90 upgrade_cost_factor = 0.70 }"
        )
        "db\units\divisions\battlecruiser.txt" = @(
            "upgrade = { type = carrier upgrade_time_factor = 0.80 upgrade_cost_factor = 0.75 }"
        )
        "db\units\divisions\heavy_cruiser.txt" = @(
            "upgrade = { type = light_carrier upgrade_time_factor = 0.32 upgrade_cost_factor = 0.60 }",
            "upgrade = { type = escort_carrier upgrade_time_factor = 0.45 upgrade_cost_factor = 0.35 }"
        )
        "db\units\divisions\light_cruiser.txt" = @(
            "upgrade = { type = light_carrier upgrade_time_factor = 0.30 upgrade_cost_factor = 0.65 }",
            "upgrade = { type = escort_carrier upgrade_time_factor = 0.42 upgrade_cost_factor = 0.35 }"
        )
        "db\units\divisions\transport.txt" = @(
            "upgrade = { type = light_carrier upgrade_time_factor = 0.30 upgrade_cost_factor = 1.00 }",
            "upgrade = { type = escort_carrier upgrade_time_factor = 0.40 upgrade_cost_factor = 0.60 }"
        )
    }

    $encoding = [System.Text.Encoding]::GetEncoding(1252)
    foreach ($entry in $routes.GetEnumerator()) {
        Copy-StockFile $entry.Key
        $path = Join-Path $script:OverlayRoot $entry.Key
        $text = [System.IO.File]::ReadAllText($path, $encoding)
        if ([regex]::IsMatch($text, '(?m)^upgrade\s*=')) {
            throw "Darkest Hour Full unexpectedly defines naval conversions in $($entry.Key)."
        }
        $firstLineEnd = $text.IndexOf("`n")
        if ($firstLineEnd -lt 0) {
            throw "Malformed naval unit definition: $($entry.Key)"
        }
        $block = @(
            @("# AUBM V4.2: refit an existing hull through the normal upgrade budget.") +
            @($entry.Value)
        ) -join "`r`n"
        $text = $text.Insert($firstLineEnd + 1, "`r`n$block`r`n")
        [System.IO.File]::WriteAllText($path, $text, $encoding)
    }
}

function Enable-LandConversionUsability {
    $encoding = [System.Text.Encoding]::GetEncoding(1252)
    $routes = [ordered]@{
        "db\units\divisions\cavalry.txt" = @{
            Pattern = '(?m)^upgrade\s*=\s*\{\s*type\s*=\s*motorized\b[^}\r\n]*\}'
            Replacement = 'upgrade = { type = motorized upgrade_time_factor = 0.45 upgrade_cost_factor = 0.45 }'
        }
        "db\units\divisions\militia.txt" = @{
            Pattern = '(?m)^upgrade\s*=\s*\{\s*type\s*=\s*infantry\b[^}\r\n]*\}'
            Replacement = 'upgrade = { type = infantry upgrade_time_factor = 0.45 upgrade_cost_factor = 0.70 }'
        }
        "db\units\divisions\garrison.txt" = @{
            Pattern = '(?m)^upgrade\s*=\s*\{\s*type\s*=\s*infantry\b[^}\r\n]*\}'
            Replacement = 'upgrade = { type = infantry upgrade_time_factor = 0.50 upgrade_cost_factor = 0.70 }'
        }
    }

    foreach ($entry in $routes.GetEnumerator()) {
        Copy-StockFile $entry.Key
        $path = Join-Path $script:OverlayRoot $entry.Key
        $text = [System.IO.File]::ReadAllText($path, $encoding)
        $updated = [regex]::Replace($text, $entry.Value.Pattern, $entry.Value.Replacement)
        if ($updated -eq $text) {
            throw "Expected conversion route was not found in $($entry.Key)."
        }
        [System.IO.File]::WriteAllText($path, $updated, $encoding)
    }
}

$GameRoot = Resolve-GameRoot $GameRoot
$script:StockRoot = Join-Path $GameRoot "Mods\Darkest Hour Full"
$repositoryFullPath = [System.IO.Path]::GetFullPath($RepositoryRoot)
$script:OverlayRoot = Join-Path $repositoryFullPath "mod"
$python = Get-Command python -ErrorAction Stop

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
& (Join-Path $repositoryFullPath "tools\Set-V4-IndiaFormationNames.ps1") -RepositoryRoot $repositoryFullPath
Replace-TaggedRowsWithOverlayRows -RelativePath "db\country.csv" -Tag "IND"

Add-IndiaPersonalityDefinitions
Disable-GenericPurgeForIndia
Exclude-IndiaFromGenericMobilization
Exclude-IndiaFromGenericElections
Add-SovereignIndiaToJapanAI
Build-EventsIndex
Build-Scenario
Build-UnitedKingdomScenario
Enable-LandConversionUsability
Enable-NavalConversions
Copy-StockFile "db\misc.txt"

& (Join-Path $repositoryFullPath "tools\Set-V4-CombatRules.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Set-V4-IndiaOOB.ps1") -RepositoryRoot $repositoryFullPath
Copy-StockFile "db\units\division_types.txt"
& (Join-Path $repositoryFullPath "tools\Ensure-Aubm-SpecialUnits.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-EventUnitAvailability.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-EventProcurement.ps1") -RepositoryRoot $repositoryFullPath
& $python.Source (Join-Path $repositoryFullPath "tools\normalize_v4_procurement_gates.py")
if ($LASTEXITCODE -ne 0) {
    throw "Procurement-gate normalization failed with exit code $LASTEXITCODE."
}
& $python.Source (Join-Path $repositoryFullPath "tools\ensure_decision_visibility.py") --root $repositoryFullPath
if ($LASTEXITCODE -ne 0) {
    throw "Decision-visibility normalization failed with exit code $LASTEXITCODE."
}
& (Join-Path $repositoryFullPath "tools\Ensure-V4-ConstructionSafety.ps1") -RepositoryRoot $repositoryFullPath
& (Join-Path $repositoryFullPath "tools\Ensure-V4-EventPictures.ps1") -RepositoryRoot $repositoryFullPath -GameRoot $GameRoot
if ($IncludePersonalSprites) {
    & (Join-Path $repositoryFullPath "tools\Build-Aubm-IndiaSprites.ps1") `
        -RepositoryRoot $repositoryFullPath `
        -GameRoot $GameRoot `
        -BloodAndIronPath (Join-Path $GameRoot "Mods\Blood and Iron v1.1")

    & $python.Source (Join-Path $repositoryFullPath "tools\validate_aubm_sprites.py") `
        --root $repositoryFullPath `
        --game-root $GameRoot `
        --skip-idempotence
    if ($LASTEXITCODE -ne 0) {
        throw "India sprite validation failed with exit code $LASTEXITCODE."
    }
}

Write-Host "V4 overlay rebased onto Darkest Hour Full:"
Write-Host "  $script:OverlayRoot"
