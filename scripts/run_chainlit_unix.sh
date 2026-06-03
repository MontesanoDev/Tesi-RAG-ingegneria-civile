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

compatible_venv_path() {
  if [[ -n "${RAG_VENV_DIR:-}" ]]; then
    printf '%s\n' "$project_root/$RAG_VENV_DIR"
    return 0
  fi

  if [[ -x "$project_root/.venv/bin/python" ]]; then
    printf '%s\n' "$project_root/.venv"
    return 0
  fi

  if [[ -x "$project_root/.venv-unix/bin/python" ]]; then
    printf '%s\n' "$project_root/.venv-unix"
    return 0
  fi

  printf '%s\n' "$project_root/.venv"
}

assert_env_ready() {
  local env_path="$project_root/.env"
  local missing=()
  local key

  if [[ ! -f "$env_path" ]]; then
    echo ".env non trovato. Crea .env partendo da .env.example e compila LLM_MODEL, LLM_API_KEY, LLM_API_BASE prima di avviare Chainlit." >&2
    exit 1
  fi

  for key in LLM_MODEL LLM_API_KEY LLM_API_BASE; do
    if ! grep -Eq "^[[:space:]]*$key[[:space:]]*=[[:space:]]*[^[:space:]#]+" "$env_path"; then
      missing+=("$key")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    echo "Completa .env prima di avviare Chainlit. Mancano: ${missing[*]}" >&2
    exit 1
  fi
}

venv_path="$(compatible_venv_path)"

if [[ ! -x "$venv_path/bin/python" || ! -x "$venv_path/bin/chainlit" ]]; then
  echo "Virtualenv Linux/macOS non pronto. Esegui prima: bash scripts/setup_unix.sh" >&2
  exit 1
fi

assert_env_ready

# shellcheck disable=SC1091
source "$venv_path/bin/activate"

host="${HOST:-127.0.0.1}"
port="${PORT:-8000}"

echo "Ambiente attivo: $venv_path"
echo "Avvio Chainlit su http://$host:$port"
chainlit run app.py --host "$host" --port "$port"
