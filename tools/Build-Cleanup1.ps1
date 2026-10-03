param(
    [string]$Target = "C:\Program Files (x86)\Steam\steamapps\common\Darkest Hour A HOI Game\Mods\AUBM Terrain Prototype P1",
    [switch]$ValidateOnly,
    [switch]$WithoutSave
)
$ErrorActionPreference = "Stop"
$cleanupRepo = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $cleanupRepo
try {
    & python (Join-Path $PSScriptRoot "aubm_context_guards.py") --check
    if ($LASTEXITCODE -ne 0) { throw "Context sources are stale." }
    & python (Join-Path $PSScriptRoot "generate_aubm_liberator.py") --check
    if ($LASTEXITCODE -ne 0) { throw "Liberation sources are stale." }
    & python (Join-Path $PSScriptRoot "build_aubm_cleanup.py") --target $Target
    if ($LASTEXITCODE -ne 0) { throw "Cleanup compilation failed." }
    & python (Join-Path $PSScriptRoot "aubm_reserve_portraits.py")
    if ($LASTEXITCODE -ne 0) { throw "Portrait packaging failed." }
    & python (Join-Path $PSScriptRoot "validate_aubm_cleanup.py")
    if ($LASTEXITCODE -ne 0) { throw "Cleanup validation failed; installation skipped." }
    if (-not $ValidateOnly) {
        $cleanupArgs = @((Join-Path $PSScriptRoot "install_aubm_cleanup.py"), "--target", $Target)
        if ($WithoutSave) { $cleanupArgs += "--without-save" }
        & python @cleanupArgs
        if ($LASTEXITCODE -ne 0) { throw "Cleanup installation failed; inspect its verified backup." }
    }
} finally { Pop-Location }
