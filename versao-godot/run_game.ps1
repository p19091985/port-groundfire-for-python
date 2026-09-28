Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Groundfire Godot edition — launcher standalone Windows (ST03).
$editionDir = $PSScriptRoot
if ($env:GROUNDFIRE_USERDATA_DIR) { $userdataDir = $env:GROUNDFIRE_USERDATA_DIR } else { $userdataDir = Join-Path $editionDir "userdata" }
try { New-Item -ItemType Directory -Force -Path $userdataDir | Out-Null } catch {
    Write-Error "Erro: pasta userdata nao e gravavel: $userdataDir"
    exit 1
}
$probe = Join-Path $userdataDir ".writetest"
try { Set-Content -Path $probe -Value "ok" -Encoding Ascii } catch {
    Write-Error "Erro: pasta userdata nao e gravavel: $userdataDir"
    exit 1
}
Remove-Item $probe -Force -ErrorAction SilentlyContinue

$candidate = $null
foreach ($rel in @("runtime\windows\Groundfire.exe", "runtime\windows\Godot.exe", "runtime\linux\Groundfire.x86_64")) {
    $full = Join-Path $editionDir $rel
    if (Test-Path $full) { $candidate = $full; break }
}
if (-not $candidate -and $env:GODOT_BIN -and (Test-Path $env:GODOT_BIN)) { $candidate = $env:GODOT_BIN }
if (-not $candidate) {
    foreach ($name in @("godot", "godot4", "Godot")) {
        if (Get-Command $name -ErrorAction SilentlyContinue) { $candidate = $name; break }
    }
}
if (-not $candidate) {
    Write-Error "Godot nao encontrado. Coloque o binario em versao-godot/runtime/windows/ ou defina GODOT_BIN."
    exit 1
}
& $candidate --path (Join-Path $editionDir "godot") @args
exit $LASTEXITCODE
