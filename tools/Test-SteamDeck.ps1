param(
    [switch]$FullPayload
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$deckRoot = Join-Path $repositoryRoot "platform\steam-deck"
$wsl = Get-Command wsl.exe -ErrorAction Stop

function Convert-ToWslPath {
    param([string]$WindowsPath)

    $result = & $wsl.Source -e wslpath -a $WindowsPath
    if ($LASTEXITCODE -ne 0) {
        throw "wslpath failed for $WindowsPath"
    }
    return ($result | Select-Object -First 1).Trim()
}

$shellScripts = @(Get-ChildItem -LiteralPath $deckRoot -Filter "*.sh" -File)
foreach ($script in $shellScripts) {
    $linuxPath = Convert-ToWslPath -WindowsPath $script.FullName
    & $wsl.Source -e bash -n $linuxPath
    if ($LASTEXITCODE -ne 0) {
        throw "Bash syntax validation failed: $($script.Name)"
    }
}
Write-Host "Steam Deck shell syntax passed for $($shellScripts.Count) scripts."

$controllerPath = Join-Path $deckRoot "controller\aubm-steam-deck.vdf"
$controller = Get-Content -LiteralPath $controllerPath -Raw
$openingBraces = ($controller.ToCharArray() | Where-Object { $_ -eq '{' }).Count
$closingBraces = ($controller.ToCharArray() | Where-Object { $_ -eq '}' }).Count
if ($openingBraces -ne $closingBraces) {
    throw "Steam Input VDF has unbalanced braces: $openingBraces opening, $closingBraces closing."
}
foreach ($required in @(
    'controller_type" "controller_neptune',
    'key_press SPACE',
    'key_press KEYPAD_DASH',
    'key_press KEYPAD_PLUS',
    'key_press F3',
    'key_press LEFT_SHIFT',
    'key_press LEFT_CONTROL',
    'key_press ENTER, Confirm',
    '"mode" "mouse_region"',
    'mouse_button LEFT, Select Action',
    '"position_x" "58"',
    '"position_y" "72"',
    '"sensitivity_horiz_scale" "0"',
    '"mode" "touch_menu"',
    '"touch_menu_button_0"',
    '"touch_menu_button_9"',
    'controller_action SHOW_KEYBOARD',
    'mouse_button LEFT',
    'mouse_button RIGHT'
)) {
    if (-not $controller.Contains($required)) {
        throw "Steam Input VDF is missing required binding: $required"
    }
}
Write-Host "Steam Input layout structure and required controls passed."

$controllerInstaller = Get-Content -LiteralPath (Join-Path $deckRoot "install-aubm-controller.sh") -Raw
if (-not $controllerInstaller.Contains('--replace')) {
    throw "Steam Input installer does not support managed replacement of an existing layout."
}
$deckInstaller = Get-Content -LiteralPath (Join-Path $deckRoot "install-aubm-deck.sh") -Raw
if (-not $deckInstaller.Contains('aubm-steam-deck.vdf" \') -or
    -not $deckInstaller.Contains('--replace')) {
    throw "Steam Deck installer does not activate the managed replacement controller profile."
}

$fixtureTest = Convert-ToWslPath -WindowsPath (Join-Path $deckRoot "test-aubm-deck.sh")
& $wsl.Source -e bash $fixtureTest
if ($LASTEXITCODE -ne 0) {
    throw "Steam Deck end-to-end fixture failed."
}

if ($FullPayload) {
    $packageScript = Convert-ToWslPath -WindowsPath (Join-Path $deckRoot "package-aubm-deck.sh")
    & $wsl.Source -e bash $packageScript --verify-only
    if ($LASTEXITCODE -ne 0) {
        throw "Steam Deck full payload validation failed."
    }
}

Write-Host "Steam Deck validation passed."
