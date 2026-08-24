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

$changedFiles = 0
$removedGates = 0
$verifiedBuilds = 0
$verifiedDeployments = 0

foreach ($eventRoot in $eventRoots) {
    if (-not (Test-Path -LiteralPath $eventRoot -PathType Container)) {
        continue
    }

    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $lines = [System.IO.File]::ReadAllLines($file.FullName, $encoding)
        $output = [System.Collections.Generic.List[string]]::new()
        $changed = $false

        foreach ($line in $lines) {
            if ($line -match '#\s*AUBM_V4_UNIT_GATE\s+[A-Za-z0-9_]+') {
                # Technology, not an event, owns the current equipment model.
                # Generated activation gates previously exposed model zero for
                # unresearched types and could downgrade later procurement.
                $changed = $true
                $removedGates++
                continue
            }
            if ($line -match '\btype\s*=\s*build_division\b') {
                $verifiedBuilds++
            }
            if ($line -match '\btype\s*=\s*add_division\b') {
                $verifiedDeployments++
                if ($line -notmatch '\bvalue\s*=\s*d_(?:\d+|rsv_\d+)\b') {
                    if ($line -notmatch '\bwhen\s*=\s*-1\b') {
                        if ($line -notmatch '\bwhen\s*=\s*-\d+\b') {
                            throw "Direct standard-unit grant has no latest-model selector: $($file.FullName): $line"
                        }
                        # In DH, 'when' selects the model. -1 is the established
                        # latest-model selector; unit damage belongs in 'where'.
                        $line = $line -replace '\bwhen\s*=\s*-\d+\b', 'when = -1'
                        $changed = $true
                    }
                }
            }
            $output.Add($line)
        }

        if ($changed) {
            [System.IO.File]::WriteAllText(
                $file.FullName,
                (($output -join "`r`n").TrimEnd() + "`r`n"),
                $encoding
            )
            $changedFiles++
        }
    }
}

Write-Host (
    "Verified $verifiedBuilds research-owned production orders and " +
    "$verifiedDeployments latest-model direct deployments; " +
    "removed $removedGates generated availability gates from $changedFiles files."
)
