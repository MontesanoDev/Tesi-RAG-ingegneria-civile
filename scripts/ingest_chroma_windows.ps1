$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host @"
 ____      _      ____
|  _ \    / \    / ___|
| |_) |  / _ \  | |  _
|  _ <  / ___ \ | |_| |
|_| \_\/_/   \_\ \____|

RAG per Bandi di Ingegneria Civile
"@
}

function Fail {
    param([string]$Message)
    Write-Host "ERRORE: $Message" -ForegroundColor Red
    exit 1
}

function Get-ProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-CompatibleVenvPath {
    param([string]$ProjectRoot)

    if ($env:RAG_VENV_DIR) {
        return (Join-Path $ProjectRoot $env:RAG_VENV_DIR)
    }

    $preferred = Join-Path $ProjectRoot ".venv"
    $fallback = Join-Path $ProjectRoot ".venv-windows"

    if (Test-Path (Join-Path $preferred "Scripts\python.exe")) {
        return $preferred
    }
    if (Test-Path (Join-Path $fallback "Scripts\python.exe")) {
        return $fallback
    }

    return $preferred
}

Show-Banner

$projectRoot = Get-ProjectRoot
Set-Location $projectRoot

$venvPath = Get-CompatibleVenvPath -ProjectRoot $projectRoot
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Fail "Virtualenv Windows non pronto. Esegui prima: .\scripts\setup_windows.ps1"
}

$dataDir = Join-Path $projectRoot "dati_azienda"
if (-not (Test-Path $dataDir)) {
    Fail "Cartella dati_azienda non trovata."
}

$files = Get-ChildItem -Path $dataDir -File -Recurse
if ($files.Count -eq 0) {
    Fail "Nessun documento trovato in dati_azienda. Inserisci i file da indicizzare e rilancia lo script."
}

$env:VIRTUAL_ENV = $venvPath
$env:PATH = "$(Join-Path $venvPath 'Scripts');$env:PATH"

Write-Host "Ambiente attivo: $venvPath"
Write-Host "Rigenero chroma_db da dati_azienda. Il vecchio database locale verra' sostituito."
& $venvPython creadb.py
