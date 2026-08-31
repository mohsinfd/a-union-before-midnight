param(
    [string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$GameRoot
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($RepositoryRoot)
if (-not $GameRoot) {
    $GameRoot = Join-Path ${env:ProgramFiles(x86)} "Steam\steamapps\common\Darkest Hour A HOI Game"
}
$game = [System.IO.Path]::GetFullPath($GameRoot)
$stockPictures = Join-Path $game "Mods\Darkest Hour Full\gfx\events_pics"
$pictureRoot = Join-Path $root "mod\gfx\events_pics"
$encoding = [System.Text.Encoding]::GetEncoding(1252)

$fallbacks = @{
    "armed" = Join-Path $pictureRoot "india_v3_armed_forces.bmp"
    "industry" = Join-Path $pictureRoot "india_v3_industry.bmp"
    "politics" = Join-Path $pictureRoot "india_v3_independence.bmp"
    "decision" = Join-Path $stockPictures "decision_wargames.bmp"
}
foreach ($path in $fallbacks.Values) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required event-picture fallback is missing: $path"
    }
}

function Select-Fallback {
    param([string]$Name)

    if ($Name -match '(?i)(industry|plan|steel|factory|science|rocket|atomic)') {
        return $fallbacks["industry"]
    }
    if ($Name -match '(?i)(army|air|nav|fleet|elite|gurkha|imphal|yokosuka|mission|war_aim|airborne|frontier|marine|penetration)') {
        return $fallbacks["armed"]
    }
    return $fallbacks["politics"]
}

$eventRoots = @(
    (Join-Path $root "mod\db\events\india_v3"),
    (Join-Path $root "mod\db\events\aubm_v4")
)
$created = [System.Collections.Generic.List[string]]::new()
$rewritten = 0

foreach ($eventRoot in $eventRoots) {
    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $text = [System.IO.File]::ReadAllText($file.FullName, $encoding)
        $original = $text

        $decisionMatches = [regex]::Matches(
            $text,
            '(?m)^(\s*decision_picture\s*=\s*")([^"]+)(")'
        )
        foreach ($match in $decisionMatches) {
            $name = $match.Groups[2].Value
            $modPicture = Join-Path $pictureRoot "$name.bmp"
            $stockPicture = Join-Path $stockPictures "$name.bmp"
            if ((Test-Path -LiteralPath $modPicture) -or (Test-Path -LiteralPath $stockPicture)) {
                continue
            }
            $text = $text.Replace($match.Value, $match.Groups[1].Value + "decision_wargames" + $match.Groups[3].Value)
        }

        $pictureMatches = [regex]::Matches(
            $text,
            '(?m)^\s*picture\s*=\s*"([^"]+)"'
        )
        foreach ($match in $pictureMatches) {
            $name = $match.Groups[1].Value
            $modPicture = Join-Path $pictureRoot "$name.bmp"
            $stockPicture = Join-Path $stockPictures "$name.bmp"
            if ((Test-Path -LiteralPath $modPicture) -or (Test-Path -LiteralPath $stockPicture)) {
                continue
            }

            $fallback = Select-Fallback $name
            Copy-Item -LiteralPath $fallback -Destination $modPicture -Force
            $created.Add("$name <- $([System.IO.Path]::GetFileNameWithoutExtension($fallback))")
        }

        if ($text -ne $original) {
            [System.IO.File]::WriteAllText($file.FullName, $text, $encoding)
            $rewritten++
        }
    }
}

$fallbackHashes = @{}
foreach ($key in "armed", "industry", "politics") {
    $fallbackHashes[$key] = (Get-FileHash -LiteralPath $fallbacks[$key] -Algorithm SHA256).Hash
}
$backlog = [System.Collections.Generic.List[string]]::new()
foreach ($eventRoot in $eventRoots) {
    foreach ($file in Get-ChildItem -LiteralPath $eventRoot -Filter "*.txt" -File) {
        $text = [System.IO.File]::ReadAllText($file.FullName, $encoding)
        foreach ($match in [regex]::Matches($text, '(?m)^\s*picture\s*=\s*"([^"]+)"')) {
            $name = $match.Groups[1].Value
            if ($name -in @("india_v3_armed_forces", "india_v3_industry", "india_v3_independence")) {
                continue
            }
            $localPicture = Join-Path $pictureRoot "$name.bmp"
            if (-not (Test-Path -LiteralPath $localPicture -PathType Leaf)) {
                continue
            }
            $hash = (Get-FileHash -LiteralPath $localPicture -Algorithm SHA256).Hash
            foreach ($key in $fallbackHashes.Keys) {
                if ($hash -eq $fallbackHashes[$key]) {
                    $sourceName = [System.IO.Path]::GetFileNameWithoutExtension($fallbacks[$key])
                    $backlog.Add("$name <- $sourceName")
                    break
                }
            }
        }
    }
}

$manifest = Join-Path $root "docs\V4_EVENT_ART_BACKLOG.md"
if ($backlog.Count -gt 0) {
    $lines = @(
        "# V4 Event Art Backlog",
        "",
        "These event-picture names currently use independently generated AUBM fallback art.",
        "They are valid and donor-free, but remain candidates for unique original work.",
        ""
    )
    $lines += @($backlog | Sort-Object -Unique | ForEach-Object { "- " + $_ })
    [System.IO.File]::WriteAllText(
        $manifest,
        (($lines -join "`r`n").TrimEnd() + "`r`n"),
        [System.Text.Encoding]::UTF8
    )
} elseif (Test-Path -LiteralPath $manifest -PathType Leaf) {
    Remove-Item -LiteralPath $manifest -Force
}

Write-Host "Resolved missing event pictures: $($created.Count) new fallback assets, $($backlog.Count) backlog references, $rewritten decision references updated."
