[CmdletBinding()]
param(
    [string]$RepositoryRoot,
    [string]$GameRoot,
    [string]$TargetName = "A Union Before Midnight V4.2",
    [switch]$Preview,
    [switch]$ValidateOnly,
    [switch]$Rollback
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $PSScriptRoot
}

# This helper deliberately uses only the player's Darkest Hour core map, the
# AUBM province table and the original AUBM motif source. It never invokes the
# legacy MapUtility executables and it never reads a donor mod.
$managedRelativePaths = @(
    "map\Map_1\colorscales.csv",
    "map\Map_1\lightmap1.tbl",
    "map\Map_1\lightmap2.tbl",
    "map\Map_1\lightmap3.tbl",
    "map\Map_1\lightmap4.tbl"
)
$lightmapNames = @(
    "lightmap1.tbl",
    "lightmap2.tbl",
    "lightmap3.tbl",
    "lightmap4.tbl"
)
# Known local Blood and Iron / DEC reference payloads from the audited test
# installation.  Seeing one of these hashes in generated output means the
# donor-removal promise has failed, regardless of the path used to produce it.
$forbiddenDonorHashes = @(
    "5678ef053cdc78b1f53d2477209411847c23478cb42987baa91a57e0b55cccec",
    "abf9a0397248b151eaf7fa198b084895f3a139fef10d3f061970bea5b870f8f4",
    "6b72e5b2855e9ced79c1290e892769dee43b62c26c2b4a42ad8e9a04e3e14df2"
)

function Resolve-GameRoot {
    param([string]$Requested)

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        return [System.IO.Path]::GetFullPath($Requested)
    }

    $candidates = New-Object System.Collections.Generic.List[string]
    if (${env:ProgramFiles(x86)}) {
        $candidates.Add((Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Darkest Hour A HOI Game"))
    }
    if ($env:ProgramFiles) {
        $candidates.Add((Join-Path $env:ProgramFiles "Steam\steamapps\common\Darkest Hour A HOI Game"))
        $candidates.Add((Join-Path $env:ProgramFiles "Darkest Hour A HOI Game"))
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $candidate "Darkest Hour.exe") -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    throw "Darkest Hour was not found. Pass -GameRoot explicitly."
}

function Resolve-SafeChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [string]$Purpose = "path"
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Unsafe $Purpose (rooted relative path): $RelativePath"
    }
    $resolvedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )
    $resolvedPath = [System.IO.Path]::GetFullPath((Join-Path $resolvedRoot $RelativePath))
    $prefix = $resolvedRoot + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolvedPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe $Purpose outside its allowed root: $RelativePath"
    }

    # FullPath blocks lexical traversal. This directory-chain check also
    # prevents an existing junction/symlink inside an approved root from
    # redirecting a later copy or removal somewhere else.
    $current = $resolvedRoot
    if (Test-Path -LiteralPath $current) {
        $rootItem = Get-Item -LiteralPath $current -Force
        if (($rootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Unsafe $Purpose through a reparse-point root: $current"
        }
    }
    $suffix = $resolvedPath.Substring($prefix.Length)
    $segments = @(
        [regex]::Split($suffix, '[\\/]') |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )
    for ($index = 0; $index -lt ($segments.Count - 1); $index++) {
        $current = Join-Path $current $segments[$index]
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Unsafe $Purpose through a reparse-point directory: $current"
            }
        }
    }
    return $resolvedPath
}

function Assert-OrdinaryFileOrAbsent {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Expected a file or an absent path, but found another item: $Path"
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to manage a symbolic link or other reparse point: $Path"
    }
    if (($item.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0) {
        throw "Refusing to replace or remove a read-only managed file: $Path"
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )

    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    Assert-OrdinaryFileOrAbsent -Path $Path
    $temporary = Join-Path $directory (".{0}.aubm-{1}.tmp" -f ([System.IO.Path]::GetFileName($Path)), [guid]::NewGuid().ToString("N"))
    try {
        $json = $Value | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText(
            $temporary,
            $json + [Environment]::NewLine,
            [System.Text.UTF8Encoding]::new($false)
        )
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            # Windows PowerShell's .NET Framework rejects a null backup-name
            # argument even though newer runtimes accept it.  Keep the atomic
            # Replace primitive, but provide a same-directory one-use backup.
            $replaceBackup = Join-Path $directory (".{0}.aubm-replaced-{1}.bak" -f ([System.IO.Path]::GetFileName($Path)), [guid]::NewGuid().ToString("N"))
            try {
                [System.IO.File]::Replace($temporary, $Path, $replaceBackup, $true)
            } finally {
                if (Test-Path -LiteralPath $replaceBackup -PathType Leaf) {
                    Remove-Item -LiteralPath $replaceBackup -Force
                }
            }
        } else {
            [System.IO.File]::Move($temporary, $Path)
        }
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Copy-FileAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$ExpectedHash
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Atomic-copy source is missing: $Source"
    }
    Assert-OrdinaryFileOrAbsent -Path $Destination
    $directory = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $temporary = Join-Path $directory (".{0}.aubm-{1}.tmp" -f ([System.IO.Path]::GetFileName($Destination)), [guid]::NewGuid().ToString("N"))
    try {
        Copy-Item -LiteralPath $Source -Destination $temporary
        $temporaryHash = Get-Sha256 -Path $temporary
        if ($temporaryHash -ne $ExpectedHash) {
            throw "Atomic-copy staging hash mismatch for $Destination"
        }
        if (Test-Path -LiteralPath $Destination -PathType Leaf) {
            $replaceBackup = Join-Path $directory (".{0}.aubm-replaced-{1}.bak" -f ([System.IO.Path]::GetFileName($Destination)), [guid]::NewGuid().ToString("N"))
            try {
                [System.IO.File]::Replace($temporary, $Destination, $replaceBackup, $true)
            } finally {
                if (Test-Path -LiteralPath $replaceBackup -PathType Leaf) {
                    Remove-Item -LiteralPath $replaceBackup -Force
                }
            }
        } else {
            [System.IO.File]::Move($temporary, $Destination)
        }
        if ((Get-Sha256 -Path $Destination) -ne $ExpectedHash) {
            throw "Atomic-copy destination hash mismatch for $Destination"
        }
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}

function Assert-GameNotRunning {
    $running = @(
        Get-Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ProcessName -like "Darkest Hour*" -or
                $_.ProcessName -eq "DarkestHour"
            }
    )
    if ($running.Count -gt 0) {
        throw "Close Darkest Hour and its launcher before changing or rolling back the terrain layer."
    }
}

function Get-InstalledSnapshot {
    param(
        [Parameter(Mandatory = $true)][string]$TargetRoot,
        [Parameter(Mandatory = $true)][string]$BackupRoot
    )

    $records = New-Object System.Collections.Generic.List[object]
    foreach ($relativePath in $managedRelativePaths) {
        $target = Resolve-SafeChildPath -Root $TargetRoot -RelativePath $relativePath -Purpose "managed terrain path"
        Assert-OrdinaryFileOrAbsent -Path $target
        $exists = Test-Path -LiteralPath $target -PathType Leaf
        $record = [ordered]@{
            path = $relativePath.Replace("\", "/")
            existed = $exists
            sha256 = $null
            length = $null
            backup_path = $null
        }
        if ($exists) {
            $backupRelative = Join-Path "snapshot" $relativePath
            $backup = Resolve-SafeChildPath -Root $BackupRoot -RelativePath $backupRelative -Purpose "terrain backup path"
            $backupDirectory = Split-Path -Parent $backup
            if (-not (Test-Path -LiteralPath $backupDirectory -PathType Container)) {
                New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
            }
            Copy-Item -LiteralPath $target -Destination $backup
            $hash = Get-Sha256 -Path $target
            if ((Get-Sha256 -Path $backup) -ne $hash) {
                throw "Backup hash verification failed for $relativePath"
            }
            $record.sha256 = $hash
            $record.length = (Get-Item -LiteralPath $target).Length
            $record.backup_path = $backupRelative.Replace("\", "/")
        }
        $records.Add([pscustomobject]$record)
    }
    return $records.ToArray()
}

function Assert-SnapshotContract {
    param(
        [Parameter(Mandatory = $true)]$Records,
        [Parameter(Mandatory = $true)][string]$BackupRoot
    )

    $expected = @($managedRelativePaths | ForEach-Object { $_.Replace("\", "/") })
    $actual = @($Records | ForEach-Object { [string]$_.path })
    if ($actual.Count -ne $expected.Count) {
        throw "Terrain snapshot must describe exactly $($expected.Count) managed paths."
    }
    foreach ($path in $expected) {
        if (@($actual | Where-Object { $_ -ceq $path }).Count -ne 1) {
            throw "Terrain snapshot is missing or duplicates its exact path contract: $path"
        }
        $record = @($Records | Where-Object { ([string]$_.path) -ceq $path })[0]
        if ($record.existed -isnot [bool]) {
            throw "Terrain snapshot has a non-Boolean presence marker for $path"
        }
        if ([bool]$record.existed) {
            if (([string]$record.sha256) -notmatch '^[0-9a-f]{64}$' -or [long]$record.length -le 0) {
                throw "Terrain snapshot has invalid file metadata for $path"
            }
            $expectedBackupRelative = (Join-Path "snapshot" $path.Replace("/", "\")).Replace("\", "/")
            if (([string]$record.backup_path) -cne $expectedBackupRelative) {
                throw "Terrain snapshot has an unexpected backup path for $path"
            }
            $backup = Resolve-SafeChildPath -Root $BackupRoot -RelativePath $expectedBackupRelative.Replace("/", "\") -Purpose "terrain rollback source"
            if (-not (Test-Path -LiteralPath $backup -PathType Leaf)) {
                throw "Terrain rollback source is missing: $backup"
            }
            Assert-OrdinaryFileOrAbsent -Path $backup
            if ((Get-Sha256 -Path $backup) -ne ([string]$record.sha256).ToLowerInvariant()) {
                throw "Terrain rollback source failed its recorded hash: $path"
            }
            if ((Get-Item -LiteralPath $backup).Length -ne [long]$record.length) {
                throw "Terrain rollback source failed its recorded length: $path"
            }
        } elseif ($null -ne $record.sha256 -or $null -ne $record.length -or $null -ne $record.backup_path) {
            throw "An absent terrain path contains unexpected backup metadata: $path"
        }
    }
}

function Restore-InstalledSnapshot {
    param(
        [Parameter(Mandatory = $true)][string]$TargetRoot,
        [Parameter(Mandatory = $true)][string]$BackupRoot,
        [Parameter(Mandatory = $true)]$Records
    )

    Assert-SnapshotContract -Records $Records -BackupRoot $BackupRoot
    foreach ($record in $Records) {
        $relativePath = ([string]$record.path).Replace("/", "\")
        $target = Resolve-SafeChildPath -Root $TargetRoot -RelativePath $relativePath -Purpose "terrain rollback target"
        Assert-OrdinaryFileOrAbsent -Path $target
        if ([bool]$record.existed) {
            $backup = Resolve-SafeChildPath -Root $BackupRoot -RelativePath ([string]$record.backup_path).Replace("/", "\") -Purpose "terrain rollback source"
            Copy-FileAtomic -Source $backup -Destination $target -ExpectedHash ([string]$record.sha256).ToLowerInvariant()
        } elseif (Test-Path -LiteralPath $target -PathType Leaf) {
            Remove-Item -LiteralPath $target -Force
        }
    }

    foreach ($record in $Records) {
        $target = Resolve-SafeChildPath -Root $TargetRoot -RelativePath ([string]$record.path).Replace("/", "\") -Purpose "restored terrain path"
        if ([bool]$record.existed) {
            if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
                throw "Rollback did not restore $($record.path)"
            }
            if ((Get-Sha256 -Path $target) -ne ([string]$record.sha256).ToLowerInvariant()) {
                throw "Rollback verification failed for $($record.path)"
            }
        } elseif (Test-Path -LiteralPath $target) {
            throw "Rollback did not restore the absent state for $($record.path)"
        }
    }
}

function Invoke-PythonChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Host "[$Label]"
    & $PythonPath $ScriptPath @Arguments
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode."
    }
}

$modeCount = @(@($Preview, $ValidateOnly, $Rollback) | Where-Object { [bool]$_ }).Count
if ($modeCount -gt 1) {
    throw "Use only one of -Preview, -ValidateOnly or -Rollback."
}

$repositoryRoot = [System.IO.Path]::GetFullPath($RepositoryRoot)
$gameRoot = Resolve-GameRoot -Requested $GameRoot
if (-not (Test-Path -LiteralPath (Join-Path $gameRoot "Darkest Hour.exe") -PathType Leaf)) {
    throw "The selected GameRoot is not a Darkest Hour installation: $gameRoot"
}

$modsRoot = Join-Path $gameRoot "Mods"
if (-not (Test-Path -LiteralPath $modsRoot -PathType Container)) {
    throw "The Darkest Hour Mods folder is missing: $modsRoot"
}
if ([string]::IsNullOrWhiteSpace($TargetName) -or
    [System.IO.Path]::GetFileName($TargetName) -cne $TargetName -or
    $TargetName -in @(".", "..")) {
    throw "TargetName must be one ordinary folder name."
}
$targetRoot = [System.IO.Path]::GetFullPath((Join-Path $modsRoot $TargetName))
$expectedParent = [System.IO.Path]::GetFullPath($modsRoot).TrimEnd("\")
$actualParent = [System.IO.Path]::GetDirectoryName($targetRoot).TrimEnd("\")
if (-not $actualParent.Equals($expectedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "TargetName must resolve directly below the Darkest Hour Mods folder."
}
$markerPath = Join-Path $targetRoot "A_UNION_BEFORE_MIDNIGHT_INSTALL.json"
if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
    throw "The managed A Union Before Midnight installation was not found: $targetRoot"
}

$statePath = Join-Path $targetRoot "AUBM_ORIGINAL_TERRAIN_VISUALS.json"
if ($Rollback) {
    Assert-GameNotRunning
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) {
        throw "No original-terrain installation state was found to roll back: $statePath"
    }
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.mode -ne "aubm-original-all-terrain-local-compiler") {
        throw "The terrain state file has an unexpected mode and will not be used for rollback."
    }
    if (-not ([string]$state.target_root).Equals($targetRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The terrain state belongs to a different target installation."
    }
    $backupRoot = [System.IO.Path]::GetFullPath([string]$state.backup_root)
    $expectedBackupParent = [System.IO.Path]::GetFullPath((Join-Path $targetRoot "AUBM_ORIGINAL_TERRAIN_BACKUP"))
    $backupPrefix = $expectedBackupParent.TrimEnd("\") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $backupRoot.StartsWith($backupPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "The terrain state points outside the allowed backup root."
    }
    if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) {
        throw "The terrain backup folder is missing: $backupRoot"
    }
    Restore-InstalledSnapshot -TargetRoot $targetRoot -BackupRoot $backupRoot -Records @($state.before)
    $state.status = "rolled-back"
    $state | Add-Member -NotePropertyName rolled_back_at -NotePropertyValue (Get-Date).ToString("o") -Force
    Write-JsonAtomic -Path $statePath -Value $state
    Write-Host "Original AUBM terrain layer rolled back and verified."
    Write-Host "The five managed map paths now match their exact pre-install file/absence states."
    exit 0
}

$coreMapRoot = Join-Path $gameRoot "map\Map_1"
$compilerPath = Join-Path $repositoryRoot "tools\aubm_lightmap.py"
$provinceCsvPath = Join-Path $repositoryRoot "mod\map\Map_1\Province.csv"
$motifPath = Join-Path $repositoryRoot "assets\v4_terrain\aubm_terrain_motifs.json"
foreach ($required in @($compilerPath, $provinceCsvPath, $motifPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required AUBM original-terrain source is missing: $required"
    }
}
$coreColorscalesPath = Join-Path $coreMapRoot "colorscales.csv"
foreach ($required in @($coreColorscalesPath) + @($lightmapNames | ForEach-Object { Join-Path $coreMapRoot $_ })) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required player-owned Darkest Hour core-map source is missing: $required"
    }
}

if ($Preview) {
    Write-Host "Original AUBM all-terrain layer is ready to compile from:"
    Write-Host "  Darkest Hour core map: $coreMapRoot"
    Write-Host "  AUBM province table:    $provinceCsvPath"
    Write-Host "  Original motif source:  $motifPath"
    Write-Host "The install would back up exactly five map paths, atomically replace lightmap1-4,"
    Write-Host "and remove only the mod-local colorscales.csv so Darkest Hour's core scale is used."
    Write-Host "Save games, scenarios, events, models and sprites are outside the managed path list."
    exit 0
}

$python = Get-Command python -ErrorAction Stop
$stagingBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$stagingRoot = Resolve-SafeChildPath -Root $stagingBase -RelativePath ("AUBM-original-terrain-{0}" -f [guid]::NewGuid().ToString("N")) -Purpose "temporary build folder"
$compiledRoot = Join-Path $stagingRoot "compiled"
$buildManifestPath = Join-Path $stagingRoot "AUBM_ORIGINAL_TERRAIN_MANIFEST.json"
$mutationStarted = $false
$backupRoot = $null
$before = $null
$transaction = $null

try {
    New-Item -ItemType Directory -Path $compiledRoot -Force | Out-Null

    Invoke-PythonChecked `
        -Label "Original motif validation" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @("motifs", "--motifs", $motifPath)
    Invoke-PythonChecked `
        -Label "Core lightmap byte-identical codec roundtrip" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @("roundtrip", "--source-dir", $coreMapRoot)
    Invoke-PythonChecked `
        -Label "Four-zoom original terrain compilation" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @(
            "build",
            "--source-dir", $coreMapRoot,
            "--province-csv", $provinceCsvPath,
            "--motifs", $motifPath,
            "--output-dir", $compiledRoot,
            "--manifest", $buildManifestPath
        )
    Invoke-PythonChecked `
        -Label "Compiled lightmap structural validation" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @("validate", "--source-dir", $compiledRoot)
    Invoke-PythonChecked `
        -Label "Compiled ownership and protected-pixel comparison" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @(
            "compare",
            "--source-dir", $coreMapRoot,
            "--candidate-dir", $compiledRoot,
            "--province-csv", $provinceCsvPath,
            "--motifs", $motifPath
        )

    if (-not (Test-Path -LiteralPath $buildManifestPath -PathType Leaf)) {
        throw "The terrain compiler did not produce its provenance manifest."
    }
    $null = Get-Content -LiteralPath $buildManifestPath -Raw | ConvertFrom-Json

    $coreRecords = New-Object System.Collections.Generic.List[object]
    $generatedRecords = New-Object System.Collections.Generic.List[object]
    foreach ($name in $lightmapNames) {
        $core = Join-Path $coreMapRoot $name
        $generated = Join-Path $compiledRoot $name
        if (-not (Test-Path -LiteralPath $generated -PathType Leaf)) {
            throw "The terrain compiler did not produce $name"
        }
        $coreHash = Get-Sha256 -Path $core
        $generatedHash = Get-Sha256 -Path $generated
        if ($generatedHash -eq $coreHash) {
            throw "The compiled $name is byte-identical to the core input; all four zooms must carry the original AUBM layer."
        }
        if ($generatedHash -in $forbiddenDonorHashes) {
            throw "The compiled $name matches a forbidden Blood and Iron/DEC reference hash."
        }
        $coreRecords.Add([pscustomobject][ordered]@{
            path = $core
            sha256 = $coreHash
            length = (Get-Item -LiteralPath $core).Length
        })
        $generatedRecords.Add([pscustomobject][ordered]@{
            path = ("map/Map_1/{0}" -f $name)
            sha256 = $generatedHash
            length = (Get-Item -LiteralPath $generated).Length
        })
    }

    # Prove the compiler treated the player's core files as immutable inputs.
    foreach ($record in $coreRecords) {
        if ((Get-Sha256 -Path $record.path) -ne $record.sha256) {
            throw "The compiler modified a Darkest Hour core input: $($record.path)"
        }
    }

    if ($ValidateOnly) {
        Write-Host "Original AUBM terrain sources compiled and structurally validated at all four zooms."
        Write-Host "No installed game file was changed."
        exit 0
    }

    Assert-GameNotRunning
    $stamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $backupRoot = Resolve-SafeChildPath -Root $targetRoot -RelativePath ("AUBM_ORIGINAL_TERRAIN_BACKUP\$stamp") -Purpose "terrain backup folder"
    if (Test-Path -LiteralPath $backupRoot) {
        throw "The unique terrain backup folder already exists: $backupRoot"
    }
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    $before = @(Get-InstalledSnapshot -TargetRoot $targetRoot -BackupRoot $backupRoot)
    Assert-SnapshotContract -Records $before -BackupRoot $backupRoot

    $manifestBackupPath = Join-Path $backupRoot "AUBM_ORIGINAL_TERRAIN_BUILD_MANIFEST.json"
    Copy-Item -LiteralPath $buildManifestPath -Destination $manifestBackupPath
    $manifestHash = Get-Sha256 -Path $manifestBackupPath

    $versionPath = Join-Path $repositoryRoot "VERSION"
    $version = if (Test-Path -LiteralPath $versionPath -PathType Leaf) {
        (Get-Content -LiteralPath $versionPath -Raw).Trim()
    } else {
        $null
    }
    $transaction = [ordered]@{
        mode = "aubm-original-all-terrain-local-compiler"
        status = "prepared"
        aubm_version = $version
        prepared_at = (Get-Date).ToString("o")
        target_root = $targetRoot
        backup_root = $backupRoot
        before = $before
        installed = $generatedRecords.ToArray()
        provenance = [ordered]@{
            compiler = [ordered]@{
                path = $compilerPath
                sha256 = Get-Sha256 -Path $compilerPath
            }
            motifs = [ordered]@{
                path = $motifPath
                sha256 = Get-Sha256 -Path $motifPath
            }
            province_csv = [ordered]@{
                path = $provinceCsvPath
                sha256 = Get-Sha256 -Path $provinceCsvPath
            }
            dark_hour_core = [ordered]@{
                root = $coreMapRoot
                colorscales_sha256 = Get-Sha256 -Path $coreColorscalesPath
                lightmaps = $coreRecords.ToArray()
            }
            build_manifest = [ordered]@{
                path = $manifestBackupPath
                sha256 = $manifestHash
            }
            donor_pixels_used = $false
            legacy_maputility_executed = $false
        }
        colorscales = [ordered]@{
            path = "map/Map_1/colorscales.csv"
            installed_state = "absent"
            fallback = $coreColorscalesPath
        }
        note = "Only the five listed map paths are managed. Save games and sprite assets are never touched."
    }
    $transactionPath = Join-Path $backupRoot "AUBM_ORIGINAL_TERRAIN_TRANSACTION.json"
    Write-JsonAtomic -Path $transactionPath -Value $transaction

    $mutationStarted = $true
    foreach ($record in $generatedRecords) {
        $name = [System.IO.Path]::GetFileName([string]$record.path)
        $source = Join-Path $compiledRoot $name
        $target = Resolve-SafeChildPath -Root $targetRoot -RelativePath ([string]$record.path).Replace("/", "\") -Purpose "compiled terrain target"
        Copy-FileAtomic -Source $source -Destination $target -ExpectedHash ([string]$record.sha256)
    }

    $targetColorscales = Resolve-SafeChildPath -Root $targetRoot -RelativePath "map\Map_1\colorscales.csv" -Purpose "mod-local colorscale"
    Assert-OrdinaryFileOrAbsent -Path $targetColorscales
    if (Test-Path -LiteralPath $targetColorscales -PathType Leaf) {
        Remove-Item -LiteralPath $targetColorscales -Force
    }
    if (Test-Path -LiteralPath $targetColorscales) {
        throw "The mod-local colorscales.csv was not removed."
    }

    # Re-parse the exact installed binaries, not just their staging copies.
    $installedMapRoot = Join-Path $targetRoot "map\Map_1"
    Invoke-PythonChecked `
        -Label "Installed lightmap structural validation" `
        -PythonPath $python.Source `
        -ScriptPath $compilerPath `
        -Arguments @("validate", "--source-dir", $installedMapRoot)
    # The staging files already passed the exhaustive semantic comparison.
    # Exact installed SHA-256 equality extends that proof without repeating a
    # second hundreds-of-millions-of-pixels comparison pass.
    foreach ($record in $generatedRecords) {
        $target = Resolve-SafeChildPath -Root $targetRoot -RelativePath ([string]$record.path).Replace("/", "\") -Purpose "installed terrain verification path"
        if ((Get-Sha256 -Path $target) -ne ([string]$record.sha256)) {
            throw "Installed terrain hash verification failed for $($record.path)"
        }
    }

    $transaction.status = "installed"
    $transaction.installed_at = (Get-Date).ToString("o")
    Write-JsonAtomic -Path $transactionPath -Value $transaction
    Write-JsonAtomic -Path $statePath -Value $transaction
    Write-Host "Original AUBM all-terrain layer installed and verified at all four zooms."
    Write-Host "Exact pre-install file/absence states are backed up at: $backupRoot"
    Write-Host "Run this tool with -Rollback to restore that snapshot."
} catch {
    $failure = $_
    if ($mutationStarted -and $null -ne $before -and $null -ne $backupRoot) {
        try {
            Restore-InstalledSnapshot -TargetRoot $targetRoot -BackupRoot $backupRoot -Records $before
            if ($null -ne $transaction) {
                $transaction.status = "installation-failed-rolled-back"
                $transaction.failure = $failure.Exception.Message
                $transaction.rolled_back_at = (Get-Date).ToString("o")
                Write-JsonAtomic -Path (Join-Path $backupRoot "AUBM_ORIGINAL_TERRAIN_TRANSACTION.json") -Value $transaction
            }
        } catch {
            throw "Terrain installation failed ('$($failure.Exception.Message)') and automatic rollback also failed ('$($_.Exception.Message)'). The verified snapshot remains at $backupRoot."
        }
        throw "Terrain installation failed and its five managed paths were rolled back: $($failure.Exception.Message)"
    }
    throw
} finally {
    $resolvedStaging = [System.IO.Path]::GetFullPath($stagingRoot)
    $stagingPrefix = $stagingBase.TrimEnd("\") + [System.IO.Path]::DirectorySeparatorChar
    if ($resolvedStaging.StartsWith($stagingPrefix, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $resolvedStaging -PathType Container)) {
        Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
    }
}
