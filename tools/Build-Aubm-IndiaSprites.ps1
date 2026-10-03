[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot = "C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game",
    [string]$BloodAndIronPath,
    [switch]$SkipRegistryPatch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BloodAndIronPath)) {
    $BloodAndIronPath = Join-Path $GameRoot "Mods\Blood and Iron v1.1"
}
$repositoryRootPath = [IO.Path]::GetFullPath($RepositoryRoot)
$modRoot = Join-Path $repositoryRootPath "mod"
$spriteRoot = Join-Path $modRoot "gfx\map\units"
$bitmapRoot = Join-Path $spriteRoot "bmp"
$paletteRoot = Join-Path $modRoot "gfx\palette"
$manifestPath = Join-Path $spriteRoot "AUBM-IND-GENERATED-MANIFEST.json"
$registryPatcher = Join-Path $PSScriptRoot "Ensure-Aubm-UniqueSpriteKeys.ps1"

$donors = [ordered]@{
    "Blood and Iron v1.1" = [IO.Path]::GetFullPath($BloodAndIronPath)
    "Darkest Hour core" = [IO.Path]::GetFullPath($GameRoot)
}

$mappings = @(
    [ordered]@{ UnitType = "infantry";          SpriteKey = "d_41"; Role = "Indian line infantry";       SourceMod = "Blood and Iron v1.1"; SourceType = "INFANTRY";          Countries = @("ENG", "AST", "U02", "MIN"); Levels = @(8, 9, 10, 1) }
    [ordered]@{ UnitType = "cavalry";           SpriteKey = "d_42"; Role = "Indian cavalry";             SourceMod = "Blood and Iron v1.1"; SourceType = "CAVALRY";           Countries = @("AST", "ENG", "U02", "MIN"); Levels = @(8, 9, 10, 1) }
    [ordered]@{ UnitType = "motorized";         SpriteKey = "d_43"; Role = "Indian motorised infantry";  SourceMod = "Blood and Iron v1.1"; SourceType = "MOTORIZED";         Countries = @("ENG", "AST", "USA", "MIN"); Levels = @(1) }
    [ordered]@{ UnitType = "mechanized";        SpriteKey = "d_44"; Role = "Indian mechanised infantry"; SourceMod = "Blood and Iron v1.1"; SourceType = "MECHANIZED";        Countries = @("ENG", "AST", "USA", "MIN"); Levels = @(1) }
    [ordered]@{ UnitType = "light_armor";       SpriteKey = "d_45"; Role = "Indian light armour";        SourceMod = "Blood and Iron v1.1"; SourceType = "L_PANZER";         Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(4, 1) }
    [ordered]@{ UnitType = "armor";             SpriteKey = "d_46"; Role = "Indian armour";              SourceMod = "Blood and Iron v1.1"; SourceType = "PANZER";           Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(5, 6, 7, 1) }
    [ordered]@{ UnitType = "paratrooper";       SpriteKey = "d_47"; Role = "Indian paratroops";          SourceMod = "Blood and Iron v1.1"; SourceType = "PARATROOPER";      Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(1) }
    [ordered]@{ UnitType = "marine";            SpriteKey = "d_48"; Role = "Indian marines";             SourceMod = "Blood and Iron v1.1"; SourceType = "MARINE";           Countries = @("ENG", "AST", "USA", "U02"); Levels = @(2, 3, 4, 1) }
    [ordered]@{ UnitType = "bergsjaeger";       SpriteKey = "d_49"; Role = "Indian mountain troops";     SourceMod = "Blood and Iron v1.1"; SourceType = "BERGSJAEGER";      Countries = @("ENG", "AST", "U02", "MIN"); Levels = @(8, 9, 10, 1) }
    [ordered]@{ UnitType = "garrison";          SpriteKey = "d_50"; Role = "Indian garrison";            SourceMod = "Blood and Iron v1.1"; SourceType = "INFANTRY";         Countries = @("U02", "AST", "ENG", "MIN"); Levels = @(1, 8, 9, 10) }
    [ordered]@{ UnitType = "hq";                SpriteKey = "d_51"; Role = "Indian headquarters";        SourceMod = "Blood and Iron v1.1"; SourceType = "HQ";               Countries = @("ENG", "AST", "U02", "MIN"); Levels = @(3, 4, 5, 1) }
    [ordered]@{ UnitType = "militia";           SpriteKey = "d_52"; Role = "Indian militia";             SourceMod = "Blood and Iron v1.1"; SourceType = "MILITIA";          Countries = @("AST", "ENG", "U02", "MIN"); Levels = @(5, 6, 7, 1) }
    [ordered]@{ UnitType = "multi_role";        SpriteKey = "d_53"; Role = "Indian multirole fighter";   SourceMod = "Blood and Iron v1.1"; SourceType = "FIGHTER";          Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(6, 7, 8, 1) }
    [ordered]@{ UnitType = "interceptor";       SpriteKey = "d_54"; Role = "Indian interceptor";         SourceMod = "Blood and Iron v1.1"; SourceType = "INTERCEPTOR";      Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(6, 7, 8, 1) }
    [ordered]@{ UnitType = "strategic_bomber";  SpriteKey = "d_55"; Role = "Indian strategic bomber";    SourceMod = "Blood and Iron v1.1"; SourceType = "BOMBER";           Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(6, 7, 8, 1) }
    [ordered]@{ UnitType = "tactical_bomber";   SpriteKey = "d_56"; Role = "Indian tactical bomber";     SourceMod = "Blood and Iron v1.1"; SourceType = "TACTICAL";         Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(7, 8, 9, 1) }
    [ordered]@{ UnitType = "naval_bomber";      SpriteKey = "d_57"; Role = "Indian naval bomber";        SourceMod = "Blood and Iron v1.1"; SourceType = "NAVAL";            Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(3, 4, 5, 1) }
    [ordered]@{ UnitType = "cas";               SpriteKey = "d_58"; Role = "Indian close-support wing";  SourceMod = "Blood and Iron v1.1"; SourceType = "CAS";              Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(2, 3, 4, 1) }
    [ordered]@{ UnitType = "transport_plane";   SpriteKey = "d_59"; Role = "Indian air transport";       SourceMod = "Blood and Iron v1.1"; SourceType = "TRANSPORTPLANE";   Countries = @("ENG", "AST", "USA", "FRA"); Levels = @(1) }
    [ordered]@{ UnitType = "flying_bomb";       SpriteKey = "d_60"; Role = "Indian flying bomb";         SourceMod = "Blood and Iron v1.1"; SourceType = "FLYING_BOMB";      Countries = @("ENG", "USA", "GER", "AST"); Levels = @(1) }
    [ordered]@{ UnitType = "flying_rocket";     SpriteKey = "d_61"; Role = "Indian ballistic rocket";    SourceMod = "Blood and Iron v1.1"; SourceType = "ROCKET";           Countries = @("ENG", "USA", "GER", "AST"); Levels = @(1) }
    [ordered]@{ UnitType = "battleship";        SpriteKey = "d_62"; Role = "Indian battleship";          SourceMod = "Blood and Iron v1.1"; SourceType = "BATTLESHIP";       Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "light_cruiser";     SpriteKey = "d_63"; Role = "Indian light cruiser";       SourceMod = "Blood and Iron v1.1"; SourceType = "LIGHT_CRUISER";    Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "heavy_cruiser";     SpriteKey = "d_64"; Role = "Indian heavy cruiser";       SourceMod = "Blood and Iron v1.1"; SourceType = "HEAVY_CRUISER";    Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "battlecruiser";     SpriteKey = "d_65"; Role = "Indian battlecruiser";       SourceMod = "Blood and Iron v1.1"; SourceType = "BATTLECRUISER";    Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "destroyer";         SpriteKey = "d_66"; Role = "Indian destroyer";           SourceMod = "Blood and Iron v1.1"; SourceType = "DESTROYER";        Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "carrier";           SpriteKey = "d_67"; Role = "Indian fleet carrier";       SourceMod = "Blood and Iron v1.1"; SourceType = "CARRIER";          Countries = @("ENG", "USA", "JAP", "AST"); Levels = @(1) }
    [ordered]@{ UnitType = "escort_carrier";    SpriteKey = "d_68"; Role = "Indian escort carrier";      SourceMod = "Blood and Iron v1.1"; SourceType = "ESCORT_CARRIER";   Countries = @("ENG", "USA", "JAP", "AST"); Levels = @(1) }
    [ordered]@{ UnitType = "submarine";         SpriteKey = "d_69"; Role = "Indian submarine";           SourceMod = "Blood and Iron v1.1"; SourceType = "SUBMARINE";        Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "nuclear_submarine"; SpriteKey = "d_70"; Role = "Indian nuclear submarine";   SourceMod = "Darkest Hour core";  SourceType = "NUCLEAR_SUBMARINE"; Countries = @("MIN"); Levels = @(1) }
    [ordered]@{ UnitType = "transport";         SpriteKey = "d_71"; Role = "Indian naval transport";     SourceMod = "Blood and Iron v1.1"; SourceType = "TRANSPORT";        Countries = @("ENG", "AST", "USA", "JAP"); Levels = @(1) }
    [ordered]@{ UnitType = "light_carrier";     SpriteKey = "d_72"; Role = "Indian light carrier";       SourceMod = "Blood and Iron v1.1"; SourceType = "CARRIER";          Countries = @("JAP", "AST", "USA", "ENG"); Levels = @(1) }
    [ordered]@{ UnitType = "rocket_interceptor"; SpriteKey = "d_73"; Role = "Indian rocket interceptor"; SourceMod = "Blood and Iron v1.1"; SourceType = "ROCKET_INTERCEPTOR"; Countries = @("ENG", "USA", "GER", "AST"); Levels = @(1) }
    [ordered]@{ UnitType = "d_rsv_33"; SpriteKey = "d_74"; Role = "Gurkha Rifles";        SourceMod = "Blood and Iron v1.1"; SourceType = "d_05";          Countries = @("ENG"); Levels = @(1) }
    [ordered]@{ UnitType = "d_rsv_34"; SpriteKey = "d_75"; Role = "Frontier Force";       SourceMod = "Blood and Iron v1.1"; SourceType = "BERGSJAEGER"; Countries = @("AST", "ENG", "U02"); Levels = @(9, 10, 8, 1) }
    [ordered]@{ UnitType = "d_rsv_35"; SpriteKey = "d_76"; Role = "Chindit Columns";      SourceMod = "Blood and Iron v1.1"; SourceType = "INFANTRY";    Countries = @("AST", "ENG", "U02"); Levels = @(10, 9, 8, 1) }
    [ordered]@{ UnitType = "d_rsv_36"; SpriteKey = "d_77"; Role = "Indian Airborne";      SourceMod = "Blood and Iron v1.1"; SourceType = "PARATROOPER"; Countries = @("AST", "USA", "ENG"); Levels = @(1) }
    [ordered]@{ UnitType = "d_rsv_37"; SpriteKey = "d_78"; Role = "Coromandel Marines";   SourceMod = "Blood and Iron v1.1"; SourceType = "MARINE";      Countries = @("AST", "USA", "ENG"); Levels = @(3, 4, 2, 1) }
    [ordered]@{ UnitType = "d_rsv_38"; SpriteKey = "d_79"; Role = "Guards Armour";        SourceMod = "Blood and Iron v1.1"; SourceType = "PANZER";      Countries = @("AST", "USA", "ENG"); Levels = @(6, 7, 5, 1) }
    [ordered]@{ UnitType = "d_rsv_39"; SpriteKey = "d_80"; Role = "Guards Motorised";     SourceMod = "Blood and Iron v1.1"; SourceType = "MOTORIZED";   Countries = @("AST", "USA", "ENG"); Levels = @(1) }
    [ordered]@{ UnitType = "d_rsv_40"; SpriteKey = "d_81"; Role = "Indian Pioneers";      SourceMod = "Blood and Iron v1.1"; SourceType = "HQ";          Countries = @("AST", "U02", "ENG"); Levels = @(4, 5, 3, 1) }
)

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Resolve-BmpAsset {
    param(
        [Parameter(Mandatory)][string]$Directory,
        [Parameter(Mandatory)][string]$Name
    )
    $direct = Join-Path $Directory $Name
    if (Test-Path -LiteralPath $direct -PathType Leaf) {
        return [IO.Path]::GetFullPath($direct)
    }
    if ([string]::IsNullOrWhiteSpace([IO.Path]::GetExtension($Name))) {
        $withExtension = "$direct.bmp"
        if (Test-Path -LiteralPath $withExtension -PathType Leaf) {
            return [IO.Path]::GetFullPath($withExtension)
        }
    }
    return $null
}

function Copy-IfChanged {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )
    if ((Test-Path -LiteralPath $Destination -PathType Leaf) -and
        ((Get-Sha256 -Path $Source) -eq (Get-Sha256 -Path $Destination))) {
        return $false
    }
    $destinationDirectory = Split-Path -Parent $Destination
    [IO.Directory]::CreateDirectory($destinationDirectory) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    return $true
}

function Write-AsciiIfChanged {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )
    if ((Test-Path -LiteralPath $Path -PathType Leaf) -and
        ([IO.File]::ReadAllText($Path) -ceq $Content)) {
        return $false
    }
    [IO.Directory]::CreateDirectory((Split-Path -Parent $Path)) | Out-Null
    [IO.File]::WriteAllText($Path, $Content, [Text.Encoding]::ASCII)
    return $true
}

function Get-RelativePathCompat {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$Path
    )
    $rootFull = [IO.Path]::GetFullPath($Root).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $pathFull = [IO.Path]::GetFullPath($Path)
    $prefix = $rootFull + [IO.Path]::DirectorySeparatorChar
    if (-not $pathFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the expected root: $pathFull (root: $rootFull)"
    }
    return $pathFull.Substring($prefix.Length).Replace('\', '/')
}

function Get-RelativeModPath {
    param([Parameter(Mandatory)][string]$Path)
    return Get-RelativePathCompat -Root $modRoot -Path $Path
}

function Get-SpriteDescriptor {
    param(
        [Parameter(Mandatory)][IO.FileInfo]$File,
        [Parameter(Mandatory)][string]$DonorName,
        [Parameter(Mandatory)][string]$DonorRoot
    )
    $nameMatch = [regex]::Match(
        $File.Name,
        '^T-(?<Type>.+?) A-(?<Action>STAND|WALK|FIRE) C-(?<Country>[^ ]+)(?: L-(?<Level>\d+))?(?: D-(?<Direction>E|NE|N|NW|W|SW|S|SE))?\.spr$',
        [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
    if (-not $nameMatch.Success) {
        return $null
    }

    $text = [IO.File]::ReadAllText($File.FullName)
    $bitmapMatch = [regex]::Match($text, '(?im)^\s*Bitmap\s*=\s*"([^"]+)"')
    $paletteMatch = [regex]::Match($text, '(?im)^\s*Palette\s*=\s*"([^"]+)"')
    $framesMatch = [regex]::Match($text, '(?im)^\s*Frames\s*=\s*(\d+)')
    $speedMatch = [regex]::Match($text, '(?im)^\s*Speed\s*=\s*([0-9.]+)')
    $originMatch = [regex]::Match($text, '(?im)^\s*Origin\s*=\s*\{\s*x\s*=\s*(-?\d+)\s+y\s*=\s*(-?\d+)\s*\}')
    if (-not ($bitmapMatch.Success -and $paletteMatch.Success -and $framesMatch.Success -and
              $speedMatch.Success -and $originMatch.Success)) {
        return $null
    }

    $bitmapPath = Resolve-BmpAsset -Directory (Join-Path $DonorRoot "gfx\map\units\bmp") -Name $bitmapMatch.Groups[1].Value
    $palettePath = Resolve-BmpAsset -Directory (Join-Path $DonorRoot "gfx\palette") -Name $paletteMatch.Groups[1].Value
    if ($null -eq $bitmapPath -or $null -eq $palettePath) {
        return $null
    }

    return [pscustomobject]@{
        DonorName = $DonorName
        DonorRoot = $DonorRoot
        SourcePath = $File.FullName
        Type = $nameMatch.Groups['Type'].Value.ToUpperInvariant()
        Action = $nameMatch.Groups['Action'].Value.ToUpperInvariant()
        Country = $nameMatch.Groups['Country'].Value.ToUpperInvariant()
        Level = if ($nameMatch.Groups['Level'].Success) { [int]$nameMatch.Groups['Level'].Value } else { 0 }
        Direction = $nameMatch.Groups['Direction'].Value.ToUpperInvariant()
        BitmapPath = $bitmapPath
        PalettePath = $palettePath
        Frames = [int]$framesMatch.Groups[1].Value
        Speed = $speedMatch.Groups[1].Value
        OriginX = [int]$originMatch.Groups[1].Value
        OriginY = [int]$originMatch.Groups[2].Value
    }
}

function Get-Rank {
    param([object[]]$Values, [object]$Value)
    for ($index = 0; $index -lt $Values.Count; $index++) {
        if ([string]$Values[$index] -ceq [string]$Value) {
            return $index
        }
    }
    return 1000
}

function Get-FamilyCandidate {
    param(
        [Parameter(Mandatory)]$Mapping,
        [Parameter(Mandatory)][Collections.IDictionary]$FamilyIndex,
        [Collections.Generic.HashSet[string]]$UsedSignatures
    )
    $prefix = "$($Mapping.SourceMod)|$($Mapping.SourceType.ToUpperInvariant())|"
    $candidates = [Collections.Generic.List[object]]::new()
    foreach ($entry in $FamilyIndex.GetEnumerator()) {
        if (-not $entry.Key.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        $records = @($entry.Value)
        $stand = @($records | Where-Object Action -eq "STAND")
        $walk = @($records | Where-Object Action -eq "WALK")
        $fire = @($records | Where-Object Action -eq "FIRE")
        $walkDirections = @($walk | Where-Object { $_.Direction } | Select-Object -ExpandProperty Direction -Unique)
        if ($stand.Count -ne 1 -or $walkDirections.Count -ne 8 -or $fire.Count -lt 1) {
            continue
        }
        if (@($walk | Where-Object Frames -le 1).Count -gt 0 -or
            @($fire | Where-Object Frames -le 1).Count -gt 0) {
            continue
        }

        $standBitmapHash = Get-Sha256 -Path $stand[0].BitmapPath
        $standPaletteHash = Get-Sha256 -Path $stand[0].PalettePath
        $signature = "$standBitmapHash`:$standPaletteHash"
        if ($UsedSignatures.Contains($signature)) {
            continue
        }

        $countryRank = Get-Rank -Values @($Mapping.Countries) -Value $stand[0].Country
        $levelRank = Get-Rank -Values @($Mapping.Levels) -Value $stand[0].Level
        $minWalkFrames = ($walk | Measure-Object Frames -Minimum).Minimum
        $minFireFrames = ($fire | Measure-Object Frames -Minimum).Minimum
        $score = 100000 - ($countryRank * 1000) - ($levelRank * 100) +
                 ([int]$minWalkFrames * 2) + [int]$minFireFrames + [int]$stand[0].Frames
        $candidates.Add([pscustomobject]@{
            Key = $entry.Key
            Records = $records
            Stand = $stand[0]
            Signature = $signature
            Score = $score
            MinWalkFrames = [int]$minWalkFrames
            MinFireFrames = [int]$minFireFrames
        })
    }

    $selected = $candidates | Sort-Object @{ Expression = "Score"; Descending = $true }, Key | Select-Object -First 1
    if ($null -eq $selected) {
        throw "No complete unused donor family for $($Mapping.UnitType) ($($Mapping.SourceMod) / $($Mapping.SourceType))"
    }
    [void]$UsedSignatures.Add($selected.Signature)
    return $selected
}

foreach ($donor in $donors.GetEnumerator()) {
    if (-not (Test-Path -LiteralPath $donor.Value -PathType Container)) {
        throw "Required donor mod is missing: $($donor.Value)"
    }
}
if (-not (Test-Path -LiteralPath $modRoot -PathType Container)) {
    throw "AUBM mod root is missing: $modRoot"
}

if (-not $SkipRegistryPatch) {
    if (-not (Test-Path -LiteralPath $registryPatcher -PathType Leaf)) {
        throw "Sprite-key patcher is missing: $registryPatcher"
    }
    & $registryPatcher -RepositoryRoot $repositoryRootPath | Out-Host
}

[IO.Directory]::CreateDirectory($spriteRoot) | Out-Null
[IO.Directory]::CreateDirectory($bitmapRoot) | Out-Null
[IO.Directory]::CreateDirectory($paletteRoot) | Out-Null

$oldGeneratedFiles = @()
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    try {
        $oldManifest = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
        $oldGeneratedFiles = @(
            $oldManifest.files | ForEach-Object {
                if ($_ -is [string]) { $_ } else { $_.path }
            }
        )
    }
    catch {
        throw "Existing generated manifest is invalid; refusing unsafe cleanup: $manifestPath"
    }
}

$neededTypes = @{}
foreach ($mapping in $mappings) {
    $neededTypes["$($mapping.SourceMod)|$($mapping.SourceType.ToUpperInvariant())"] = $true
}

$familyIndex = @{}
$indexedDescriptors = 0
foreach ($donor in $donors.GetEnumerator()) {
    $sourceSpriteRoot = Join-Path $donor.Value "gfx\map\units"
    if (-not (Test-Path -LiteralPath $sourceSpriteRoot -PathType Container)) {
        throw "Donor sprite directory is missing: $sourceSpriteRoot"
    }
    foreach ($file in Get-ChildItem -LiteralPath $sourceSpriteRoot -Filter "*.spr" -File) {
        $nameMatch = [regex]::Match($file.Name, '^T-(?<Type>.+?) A-(?:STAND|WALK|FIRE) C-', 'IgnoreCase')
        if (-not $nameMatch.Success) {
            continue
        }
        $neededKey = "$($donor.Key)|$($nameMatch.Groups['Type'].Value.ToUpperInvariant())"
        if (-not $neededTypes.ContainsKey($neededKey)) {
            continue
        }
        $record = Get-SpriteDescriptor -File $file -DonorName $donor.Key -DonorRoot $donor.Value
        if ($null -eq $record) {
            continue
        }
        $familyKey = "$($record.DonorName)|$($record.Type)|$($record.Country)|$($record.Level)"
        if (-not $familyIndex.ContainsKey($familyKey)) {
            $familyIndex[$familyKey] = [Collections.Generic.List[object]]::new()
        }
        $familyIndex[$familyKey].Add($record)
        $indexedDescriptors++
    }
}

$usedSignatures = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$generatedFiles = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$fileProvenance = @{}
$manifestFamilies = [Collections.Generic.List[object]]::new()
$descriptorCount = 0
$bitmapCount = 0
$paletteCount = 0
$writeCount = 0

foreach ($mapping in $mappings) {
    $family = Get-FamilyCandidate -Mapping $mapping -FamilyIndex $familyIndex -UsedSignatures $usedSignatures
    $sourceRecords = @($family.Records | Sort-Object @{ Expression = { switch ($_.Action) { "STAND" { 0 } "WALK" { 1 } default { 2 } } } }, Direction, SourcePath)
    $assetNames = @{}
    $actionCounts = [ordered]@{ STAND = 0; WALK = 0; FIRE = 0 }

    foreach ($source in $sourceRecords) {
        $bitmapSourceKey = "BMP|$($source.BitmapPath)"
        if (-not $assetNames.ContainsKey($bitmapSourceKey)) {
            $sourceHash = Get-Sha256 -Path $source.BitmapPath
            $bitmapName = "AUBM-IND-$($mapping.SpriteKey.ToUpperInvariant())-BMP-$($sourceHash.Substring(0, 16)).bmp"
            $bitmapDestination = Join-Path $bitmapRoot $bitmapName
            if (Copy-IfChanged -Source $source.BitmapPath -Destination $bitmapDestination) {
                $writeCount++
            }
            $assetNames[$bitmapSourceKey] = $bitmapName
            $bitmapRelativePath = Get-RelativeModPath -Path $bitmapDestination
            [void]$generatedFiles.Add($bitmapRelativePath)
            $fileProvenance[$bitmapRelativePath] = [ordered]@{
                kind = "bitmap"
                source_mod = $source.DonorName
                source_path = Get-RelativePathCompat -Root $source.DonorRoot -Path $source.BitmapPath
                source_sha256 = Get-Sha256 -Path $source.BitmapPath
            }
            $bitmapCount++
        }
        $bitmapName = $assetNames[$bitmapSourceKey]

        $paletteSourceKey = "PAL|$($source.PalettePath)"
        if (-not $assetNames.ContainsKey($paletteSourceKey)) {
            $sourceHash = Get-Sha256 -Path $source.PalettePath
            $paletteName = "AUBM-IND-$($mapping.SpriteKey.ToUpperInvariant())-PAL-$($sourceHash.Substring(0, 16)).bmp"
            $paletteDestination = Join-Path $paletteRoot $paletteName
            if (Copy-IfChanged -Source $source.PalettePath -Destination $paletteDestination) {
                $writeCount++
            }
            $assetNames[$paletteSourceKey] = $paletteName
            $paletteRelativePath = Get-RelativeModPath -Path $paletteDestination
            [void]$generatedFiles.Add($paletteRelativePath)
            $fileProvenance[$paletteRelativePath] = [ordered]@{
                kind = "palette"
                source_mod = $source.DonorName
                source_path = Get-RelativePathCompat -Root $source.DonorRoot -Path $source.PalettePath
                source_sha256 = Get-Sha256 -Path $source.PalettePath
            }
            $paletteCount++
        }
        $paletteName = $assetNames[$paletteSourceKey]

        $directionToken = if ([string]::IsNullOrWhiteSpace($source.Direction)) { "" } else { " D-$($source.Direction)" }
        $descriptorName = "T-$($mapping.SpriteKey) A-$($source.Action) C-IND L-1$directionToken.spr"
        $descriptorPath = Join-Path $spriteRoot $descriptorName
        $descriptorContent = @"
Sprite = {
`tBitmap = "$bitmapName"
`tOrigin = { x = $($source.OriginX) y = $($source.OriginY) }
`tFrames = $($source.Frames)
`tSpeed = $($source.Speed)
`tPalette = "$paletteName"
}
"@ -replace "`n", "`r`n"
        if (Write-AsciiIfChanged -Path $descriptorPath -Content $descriptorContent) {
            $writeCount++
        }
        $descriptorRelativePath = Get-RelativeModPath -Path $descriptorPath
        [void]$generatedFiles.Add($descriptorRelativePath)
        $fileProvenance[$descriptorRelativePath] = [ordered]@{
            kind = "descriptor"
            source_mod = $source.DonorName
            source_path = Get-RelativePathCompat -Root $source.DonorRoot -Path $source.SourcePath
            source_sha256 = Get-Sha256 -Path $source.SourcePath
        }
        $actionCounts[$source.Action]++
        $descriptorCount++
    }

    $manifestFamilies.Add([ordered]@{
        unit_type = $mapping.UnitType
        sprite_key = $mapping.SpriteKey
        role = $mapping.Role
        source_mod = $family.Stand.DonorName
        source_type = $family.Stand.Type
        source_country = $family.Stand.Country
        source_level = $family.Stand.Level
        stand_signature = $family.Signature
        descriptors = $sourceRecords.Count
        stand_descriptors = $actionCounts.STAND
        walk_descriptors = $actionCounts.WALK
        fire_descriptors = $actionCounts.FIRE
        minimum_walk_frames = $family.MinWalkFrames
        minimum_fire_frames = $family.MinFireFrames
    })
}

$allowedRoots = @(
    ([IO.Path]::GetFullPath($spriteRoot).TrimEnd('\') + '\'),
    ([IO.Path]::GetFullPath($paletteRoot).TrimEnd('\') + '\')
)
$staleCount = 0
foreach ($relativePath in $oldGeneratedFiles) {
    if ($generatedFiles.Contains([string]$relativePath)) {
        continue
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $modRoot ([string]$relativePath).Replace('/', '\')))
    $isAllowed = $false
    foreach ($allowedRoot in $allowedRoots) {
        if ($candidate.StartsWith($allowedRoot, [StringComparison]::OrdinalIgnoreCase)) {
            $isAllowed = $true
            break
        }
    }
    if (-not $isAllowed) {
        throw "Manifest cleanup path escapes generated sprite roots: $relativePath"
    }
    $leafName = Split-Path -Leaf $candidate
    $isNamespacedAsset = $leafName.StartsWith("AUBM-IND-", [StringComparison]::OrdinalIgnoreCase)
    $isNamespacedDescriptor = $leafName -match '^T-(?:d_(?:4[1-9]|[56][0-9]|7[0-9]|8[01])|d_rsv_(?:3[3-9]|40)) A-(?:STAND|WALK|FIRE) C-IND L-1(?: D-(?:E|NE|N|NW|W|SW|S|SE))?\.spr$'
    if (-not ($isNamespacedAsset -or $isNamespacedDescriptor)) {
        throw "Manifest cleanup path is outside the AUBM-IND filename namespace: $relativePath"
    }
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        Remove-Item -LiteralPath $candidate -Force
        $staleCount++
    }
}

$sortedFiles = @($generatedFiles | Sort-Object)
$manifestFiles = [Collections.Generic.List[object]]::new()
foreach ($relativePath in $sortedFiles) {
    $fullPath = Join-Path $modRoot $relativePath.Replace('/', '\')
    $fileEntry = [ordered]@{
        path = $relativePath
        sha256 = Get-Sha256 -Path $fullPath
        bytes = (Get-Item -LiteralPath $fullPath).Length
    }
    foreach ($provenanceField in $fileProvenance[$relativePath].GetEnumerator()) {
        $fileEntry[$provenanceField.Key] = $provenanceField.Value
    }
    $manifestFiles.Add($fileEntry)
}

$manifest = [ordered]@{
    schema = 1
    namespace = "AUBM-IND"
    country = "IND"
    registry = "db/units/division_types.txt"
    unit_count = $mappings.Count
    descriptor_count = $descriptorCount
    bitmap_reference_count = $bitmapCount
    palette_reference_count = $paletteCount
    donors = @($donors.Keys)
    families = @($manifestFamilies)
    files = @($manifestFiles)
}
$manifestJson = ($manifest | ConvertTo-Json -Depth 8) + "`r`n"
if (Write-AsciiIfChanged -Path $manifestPath -Content $manifestJson) {
    $writeCount++
}

Write-Host "Built A Union Before Midnight India sprite package:"
Write-Host "  unit sprite keys: $($mappings.Count)"
Write-Host "  donor descriptors indexed: $indexedDescriptors"
Write-Host "  generated descriptors: $descriptorCount"
Write-Host "  unique generated files: $($generatedFiles.Count)"
Write-Host "  bitmap references copied: $bitmapCount"
Write-Host "  palette references copied: $paletteCount"
Write-Host "  stale manifest-owned files removed: $staleCount"
Write-Host "  files written or refreshed: $writeCount"
Write-Host "  manifest: $manifestPath"

[pscustomobject]@{
    UnitCount = $mappings.Count
    DescriptorCount = $descriptorCount
    GeneratedFileCount = $generatedFiles.Count
    StaleFilesRemoved = $staleCount
    FilesWritten = $writeCount
    Manifest = $manifestPath
}
