param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$IncludePersonalSprites
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$overlay = Join-Path $root "mod"
$installer = Join-Path $root "installer"
if (-not (Test-Path -LiteralPath $overlay -PathType Container)) {
    throw "Overlay folder is missing: $overlay"
}

function Read-OverlayPatterns {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Overlay exclusion list is missing: $Path"
    }
    return @(
        Get-Content -LiteralPath $Path |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -and -not $_.StartsWith("#") }
    )
}

function Test-OverlayPattern {
    param(
        [string]$RelativePath,
        [string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        if ($RelativePath -like $pattern) {
            return $true
        }
    }
    return $false
}

$nonRedistributablePatterns = Read-OverlayPatterns (
    Join-Path $installer "nonredistributable-overlay-patterns.txt"
)
$personalSpritePatterns = Read-OverlayPatterns (
    Join-Path $installer "personal-sprite-overlay-patterns.txt"
)

$relativePaths = @(
    Get-ChildItem -LiteralPath $overlay -Recurse -File |
        Where-Object {
            $_.FullName -notmatch '(?i)[\\/](save games|logs?)[\\/]'
        } |
        ForEach-Object {
            $relative = $_.FullName.Substring($overlay.Length + 1).Replace("\", "/")
            $isNonRedistributable = Test-OverlayPattern $relative $nonRedistributablePatterns
            $isPersonalSprite = Test-OverlayPattern $relative $personalSpritePatterns
            if (-not $isNonRedistributable -and ($IncludePersonalSprites -or -not $isPersonalSprite)) {
                $relative
            }
        }
)
[Array]::Sort($relativePaths, [System.StringComparer]::OrdinalIgnoreCase)

$records = @(
    $relativePaths | ForEach-Object {
        $relative = $_
        $source = Join-Path $overlay $relative.Replace("/", "\")
        [pscustomobject]@{
            Relative = $relative
            Hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
)

$manifest = $records | ForEach-Object { $_.Relative }
$hashManifest = $records | ForEach-Object { "$($_.Hash) *$($_.Relative)" }
[System.IO.File]::WriteAllLines(
    (Join-Path $installer "manifest.txt"),
    $manifest,
    [System.Text.Encoding]::ASCII
)
[System.IO.File]::WriteAllLines(
    (Join-Path $installer "manifest-sha256.txt"),
    $hashManifest,
    [System.Text.Encoding]::ASCII
)

$mode = if ($IncludePersonalSprites) { "personal" } else { "public" }
Write-Host "Generated $mode installer manifests for $($records.Count) overlay files."
