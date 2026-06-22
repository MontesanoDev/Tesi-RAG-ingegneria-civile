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

if [[ ! -d "$project_root/data/bandi" ]]; then
  echo "Cartella data/bandi non trovata." >&2
  exit 1
fi

if ! find "$project_root/data/bandi" -type f -iname '*.pdf' -print -quit | grep -q .; then
  echo "Nessun PDF trovato in data/bandi. Inserisci i PDF da indicizzare e rilancia lo script." >&2
  exit 1
fi

echo "Ambiente usato: $venv_path"
echo "Aggiorno chroma_db dai PDF in data/bandi."
"$venv_path/bin/python" creadb.py
