# This file is a player-operated launcher. Build and validation never execute it.
$ErrorActionPreference = 'Stop'
try {
    $gameRoot = 'C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game'
    $modFolderName = 'Japan Rising JX1 Alpha2'
    $modRoot = Join-Path (Join-Path $gameRoot 'Mods') $modFolderName
    $manifestPath = Join-Path $modRoot 'JAPAN_RISING_BUILD.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $acceptedStates = @('installed-offline-validated', 'offline-validated-awaiting-user-playtest')
    if ($manifest.mod_name -ne $modFolderName -or $manifest.state -notin $acceptedStates) {
        throw 'The installed Japan Rising build has not passed its offline checks.'
    }
    if ($manifest.validation_receipt) {
        $receiptPath = Join-Path $modRoot $manifest.validation_receipt
        if (-not (Test-Path -LiteralPath $receiptPath)) { throw 'The Japan Rising installation record is missing.' }
        $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        if ($receipt.version -ne $manifest.version -or $receipt.state -ne $manifest.state -or $receipt.target -ne $modRoot) {
            throw 'The Japan Rising installation record does not match this build. Reinstall the latest update.'
        }
    }
    $exePath = Join-Path $gameRoot 'Darkest Hour.exe'
    $existing = Get-Process -Name 'Darkest Hour' -ErrorAction SilentlyContinue
    if ($existing) { throw 'Darkest Hour is already open. Close it before starting Japan Rising.' }
    $settingsPath = Join-Path $gameRoot 'settings.cfg'
    $settings = [IO.File]::ReadAllLines($settingsPath, [Text.Encoding]::GetEncoding(28591))
    if ($settings.Count -lt 15 -or $settings[14] -notmatch '#.*[Ss]elected mod') {
        throw 'The game settings format has changed. Select Japan Rising in the standard Darkest Hour launcher.'
    }
    $backupPath = Join-Path $PSScriptRoot 'settings-before-japan-rising.cfg'
    if (-not (Test-Path -LiteralPath $backupPath)) { Copy-Item -LiteralPath $settingsPath -Destination $backupPath }
    $settings[7] = '0 # Start-up movie: skipped by Japan Rising launcher'
    $settings[14] = $modFolderName + ' # Selected mod (must be a folder into MODDIR)'
    [IO.File]::WriteAllLines($settingsPath, $settings, [Text.Encoding]::GetEncoding(28591))
    # The engine reads its selected mod from settings.cfg. No ambiguous quoted
    # mod command-line argument, private runtime, or working-directory switch.
    Start-Process -FilePath $exePath -WorkingDirectory $gameRoot
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Japan Rising could not start', 'OK', 'Warning') | Out-Null
    exit 1
}
