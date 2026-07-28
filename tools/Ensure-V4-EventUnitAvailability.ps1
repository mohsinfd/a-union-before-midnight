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

$excludedAttachments = @("", "none")
$changedFiles = 0
$gatedBuilds = 0

foreach ($eventRoot in $eventRoots) {
    if (-not (Test-Path -LiteralPath $eventRoot -PathType Container)) {
        continue
    }

    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $lines = [System.IO.File]::ReadAllLines($file.FullName, $encoding)
        $output = [System.Collections.Generic.List[string]]::new()
        $changed = $false

        foreach ($line in $lines) {
            $match = [regex]::Match(
                $line,
                'type\s*=\s*build_division\s+which\s*=\s*([A-Za-z0-9_]+)(?:\s+value\s*=\s*([A-Za-z0-9_]+))?'
            )
            if (-not $match.Success) {
                $output.Add($line)
                continue
            }

            $indent = [regex]::Match($line, '^\s*').Value
            $types = [System.Collections.Generic.List[string]]::new()
            $types.Add($match.Groups[1].Value)
            $attachment = $match.Groups[2].Value
            if ($excludedAttachments -notcontains $attachment) {
                $types.Add($attachment)
            }

            foreach ($type in $types) {
                $gateMarker = "# AUBM_V4_UNIT_GATE $type"
                $lookBehindStart = [Math]::Max(0, $output.Count - 8)
                $alreadyGated = $false
                for ($i = $lookBehindStart; $i -lt $output.Count; $i++) {
                    if ($output[$i].Contains($gateMarker)) {
                        $alreadyGated = $true
                        break
                    }
                }
                if ($alreadyGated) {
                    continue
                }

                $output.Add(
                    "$indent" + 'command = { type = activate_unit_type which = ' +
                    "$type } $gateMarker"
                )
                $output.Add(
                    "$indent" + 'command = { type = new_model which = ' +
                    "$type value = 0 } $gateMarker"
                )
                $changed = $true
            }

            $output.Add($line)
            $gatedBuilds++
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

Write-Host "Verified event unit availability for $gatedBuilds build commands; updated $changedFiles files."

