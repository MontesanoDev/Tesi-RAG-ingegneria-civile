param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000
)

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

function Assert-EnvReady {
    param([string]$ProjectRoot)

    $envPath = Join-Path $ProjectRoot ".env"
    $requiredKeys = @("LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE")

    if (-not (Test-Path $envPath)) {
        Fail ".env non trovato. Crea .env partendo da .env.example e compila LLM_MODEL, LLM_API_KEY, LLM_API_BASE prima di avviare Chainlit."
    }

    $values = @{}
    foreach ($line in Get-Content $envPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") {
            continue
        }
        $parts = $line -split "=", 2
        $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }

    $missing = @()
    foreach ($key in $requiredKeys) {
        if (-not $values.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($values[$key])) {
            $missing += $key
        }
    }

    if ($missing.Count -gt 0) {
        Fail "Completa .env prima di avviare Chainlit. Mancano: $($missing -join ', ')"
    }
}

Show-Banner

$projectRoot = Get-ProjectRoot
Set-Location $projectRoot

$venvPath = Get-CompatibleVenvPath -ProjectRoot $projectRoot
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$chainlit = Join-Path $venvPath "Scripts\chainlit.exe"

if (-not (Test-Path $venvPython) -or -not (Test-Path $chainlit)) {
    Fail "Virtualenv Windows non pronto. Esegui prima: .\scripts\setup_windows.ps1"
}

Assert-EnvReady -ProjectRoot $projectRoot

$env:VIRTUAL_ENV = $venvPath
$env:PATH = "$(Join-Path $venvPath 'Scripts');$env:PATH"

Write-Host "Ambiente attivo: $venvPath"
Write-Host "Avvio Chainlit su http://${HostName}:$Port"
& $chainlit run app.py --host $HostName --port $Port
