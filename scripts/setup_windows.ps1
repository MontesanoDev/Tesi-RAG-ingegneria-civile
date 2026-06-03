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

    if ((Test-Path (Join-Path $preferred "bin\python")) -and -not (Test-Path (Join-Path $preferred "Scripts\python.exe"))) {
        Write-Warning "'.venv' sembra un ambiente Linux/macOS. Uso '.venv-windows' per evitare conflitti."
        return $fallback
    }

    return $preferred
}

function Find-Python {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "py"; Args = @("-3.10") },
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Exe -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }

        if (($candidate.Exe -like "python*") -and ($command.Source -like "*\WindowsApps\*")) {
            continue
        }

        $output = & $candidate.Exe @($candidate.Args) -c "import sys; assert sys.version_info >= (3, 10); print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $output) {
            return [pscustomobject]@{
                Exe = $candidate.Exe
                Args = $candidate.Args
                Path = @($output)[0]
            }
        }
    }

    Fail "Python >= 3.10 non trovato. Installa Python da python.org e riprova."
}

function Test-EnvFile {
    param([string]$ProjectRoot)

    $envPath = Join-Path $ProjectRoot ".env"
    $examplePath = Join-Path $ProjectRoot ".env.example"
    $requiredKeys = @("LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE")

    if (-not (Test-Path $envPath)) {
        Write-Warning ".env non trovato. Compila un file .env prima di avviare Chainlit."
        Write-Host "Puoi partire da: $examplePath"
        return
    }

    $values = @{}
    foreach ($line in Get-Content $envPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") {
            continue
        }
        $parts = $line -split "=", 2
        $key = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }

    $missing = @()
    foreach ($key in $requiredKeys) {
        if (-not $values.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($values[$key])) {
            $missing += $key
        }
    }

    if ($missing.Count -gt 0) {
        Write-Warning "Completa .env prima di avviare Chainlit. Mancano: $($missing -join ', ')"
    } else {
        Write-Host ".env presente: variabili LLM principali compilate."
    }
}

Show-Banner

$projectRoot = Get-ProjectRoot
Set-Location $projectRoot

$venvPath = Get-CompatibleVenvPath -ProjectRoot $projectRoot
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $python = Find-Python
    Write-Host "Creo virtualenv Windows in: $venvPath"
    Write-Host "Python usato: $($python.Path)"
    & $python.Exe @($python.Args) -m venv $venvPath
} else {
    Write-Host "Virtualenv gia' presente: $venvPath"
}

Write-Host "Installo/aggiorno le dipendenze..."
& $venvPython -m pip install -r requirements.txt

Write-Host "Controllo conflitti tra pacchetti..."
& $venvPython -m pip check

Write-Host "Controllo import principali..."
& $venvPython -c "from llama_index.llms.openai_like import OpenAILike; from llama_index.embeddings.huggingface import HuggingFaceEmbedding; import chainlit, chromadb; print('Import OK')"

Test-EnvFile -ProjectRoot $projectRoot

Write-Host ""
Write-Host "Setup completato."
Write-Host "Per avviare: .\scripts\run_chainlit_windows.ps1"
Write-Host "Per ingestione dati: .\scripts\ingest_chroma_windows.ps1"
