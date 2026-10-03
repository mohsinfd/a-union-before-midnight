param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$encoding = [System.Text.Encoding]::GetEncoding(1252)

function Get-Ordinal {
    param([int]$Number)

    $lastTwo = $Number % 100
    if ($lastTwo -ge 11 -and $lastTwo -le 13) {
        return "${Number}th"
    }

    switch ($Number % 10) {
        1 { return "${Number}st" }
        2 { return "${Number}nd" }
        3 { return "${Number}rd" }
        default { return "${Number}th" }
    }
}

function Set-IndiaRows {
    param(
        [string]$RelativePath,
        [string[]]$IndiaRows
    )

    $path = Join-Path $RepositoryRoot "mod\$RelativePath"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Formation-name file not found: $path"
    }

    $otherRows = @(
        [System.IO.File]::ReadAllLines($path, $encoding) |
            Where-Object { $_ -notlike "IND;*" }
    )
    [System.IO.File]::WriteAllLines($path, @($otherRows + $IndiaRows), $encoding)
}

$armyRows = 1..200 | ForEach-Object {
    "IND;$(Get-Ordinal $_) Indian Corps"
}
$navyRows = 1..100 | ForEach-Object {
    "IND;$(Get-Ordinal $_) Indian Naval Group"
}
$airRows = 1..100 | ForEach-Object {
    "IND;No. $_ Indian Air Group"
}

Set-IndiaRows -RelativePath "db\armynames.csv" -IndiaRows $armyRows
Set-IndiaRows -RelativePath "db\navynames.csv" -IndiaRows $navyRows
Set-IndiaRows -RelativePath "db\airnames.csv" -IndiaRows $airRows

Write-Host "Applied composition-neutral Indian corps, naval-group and air-group names."
