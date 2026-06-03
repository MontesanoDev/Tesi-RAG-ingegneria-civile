#!/usr/bin/env bash
set -euo pipefail

cat <<'BANNER'
 ____      _      ____
|  _ \    / \    / ___|
| |_) |  / _ \  | |  _
|  _ <  / ___ \ | |_| |
|_| \_\/_/   \_\ \____|

RAG per Bandi di Ingegneria Civile
BANNER

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_dir/.." && pwd)"
cd "$project_root"

find_python() {
  local candidates=()
  if [[ -n "${PYTHON:-}" ]]; then
    candidates+=("$PYTHON")
  fi
  candidates+=(python3.12 python3.11 python3.10 python3 python)

  local candidate
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" -c 'import sys; assert sys.version_info >= (3, 10); print(sys.executable)' >/tmp/rag_python_path.txt 2>/dev/null; then
        cat /tmp/rag_python_path.txt
        rm -f /tmp/rag_python_path.txt
        return 0
      fi
    fi
  done

  echo "Python >= 3.10 non trovato. Installa Python e riprova." >&2
  return 1
}

compatible_venv_path() {
  if [[ -n "${RAG_VENV_DIR:-}" ]]; then
    printf '%s\n' "$project_root/$RAG_VENV_DIR"
    return 0
  fi

  if [[ -f "$project_root/.venv/Scripts/python.exe" && ! -f "$project_root/.venv/bin/python" ]]; then
    echo "'.venv' sembra un ambiente Windows. Uso '.venv-unix' per evitare conflitti." >&2
    printf '%s\n' "$project_root/.venv-unix"
    return 0
  fi

  printf '%s\n' "$project_root/.venv"
}

check_env_file() {
  local env_path="$project_root/.env"
  local example_path="$project_root/.env.example"
  local missing=()
  local key

  if [[ ! -f "$env_path" ]]; then
    echo "ATTENZIONE: .env non trovato. Compila un file .env prima di avviare Chainlit."
    echo "Puoi partire da: $example_path"
    return 0
  fi

  for key in LLM_MODEL LLM_API_KEY LLM_API_BASE; do
    if ! grep -Eq "^[[:space:]]*$key[[:space:]]*=[[:space:]]*[^[:space:]#]+" "$env_path"; then
      missing+=("$key")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    echo "ATTENZIONE: completa .env prima di avviare Chainlit. Mancano: ${missing[*]}"
  else
    echo ".env presente: variabili LLM principali compilate."
  fi
}

venv_path="$(compatible_venv_path)"
venv_python="$venv_path/bin/python"

if [[ ! -x "$venv_python" ]]; then
  python_bin="$(find_python)"
  echo "Creo virtualenv Linux/macOS in: $venv_path"
  echo "Python usato: $python_bin"
  "$python_bin" -m venv "$venv_path"
else
  echo "Virtualenv gia' presente: $venv_path"
fi

echo "Installo/aggiorno le dipendenze..."
"$venv_python" -m pip install -r requirements.txt

echo "Controllo conflitti tra pacchetti..."
"$venv_python" -m pip check

echo "Controllo import principali..."
"$venv_python" -c "from llama_index.llms.openai_like import OpenAILike; from llama_index.embeddings.huggingface import HuggingFaceEmbedding; import chainlit, chromadb; print('Import OK')"

check_env_file

echo
echo "Setup completato."
echo "Per avviare: bash scripts/run_chainlit_unix.sh"
echo "Per ingestione dati: bash scripts/ingest_chroma_unix.sh"
