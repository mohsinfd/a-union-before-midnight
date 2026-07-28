param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
$overlay = Join-Path $root "mod"
$installer = Join-Path $root "installer"
if (-not (Test-Path -LiteralPath $overlay -PathType Container)) {
    throw "Overlay folder is missing: $overlay"
}

$records = @(
    Get-ChildItem -LiteralPath $overlay -Recurse -File |
        Where-Object {
            $_.FullName -notmatch '(?i)[\\/](save games|logs?)[\\/]'
        } |
        ForEach-Object {
            $relative = $_.FullName.Substring($overlay.Length + 1).Replace("\", "/")
            [pscustomobject]@{
                Relative = $relative
                Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        } |
        Sort-Object Relative
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

Write-Host "Generated installer manifests for $($records.Count) overlay files."

