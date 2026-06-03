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

venv_path="$(compatible_venv_path)"

if [[ ! -x "$venv_path/bin/python" ]]; then
  echo "Virtualenv Linux/macOS non pronto. Esegui prima: bash scripts/setup_unix.sh" >&2
  exit 1
fi

if [[ ! -d "$project_root/dati_azienda" ]]; then
  echo "Cartella dati_azienda non trovata." >&2
  exit 1
fi

if ! find "$project_root/dati_azienda" -type f -print -quit | grep -q .; then
  echo "Nessun documento trovato in dati_azienda. Inserisci i file da indicizzare e rilancia lo script." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "$venv_path/bin/activate"

echo "Ambiente attivo: $venv_path"
echo "Rigenero chroma_db da dati_azienda. Il vecchio database locale verra' sostituito."
python creadb.py
