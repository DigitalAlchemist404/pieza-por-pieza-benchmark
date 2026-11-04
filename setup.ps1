# Pieza por Pieza: prepara solo el entorno Python; no instala llama.cpp ni modelos.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'Pieza por Pieza | Windows | PowerShell'
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $python = 'py'; $pyArgs = @('-3') }
else {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { throw 'Instala Python 3.10+ y vuelve a ejecutar este script.' }
    $python = 'python'; $pyArgs = @()
}
& $python @pyArgs -c "import sys; assert sys.version_info >= (3,10), 'Se requiere Python 3.10+'; print(sys.version)"
if ($LASTEXITCODE -ne 0) { throw 'Version de Python no compatible.' }
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    & $python @pyArgs -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-eval.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
Write-Host 'Entorno preparado. Ejecuta .\.venv\Scripts\python.exe scripts\configure.py'
