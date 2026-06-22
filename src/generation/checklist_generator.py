from pathlib import Path
from typing import Any

from src.generation.company_profile import DEFAULT_COMPANY_PROFILE, load_company_profile
from src.retrieval.rag_engine import RagEngine

CHECKLIST_QUERY_TEMPLATE = """
Analizza il bando caricato e genera una checklist operativa per preparare una candidatura.

Profilo aziendale disponibile:
{company_profile}

Produci solo Markdown con questa struttura:

# Checklist candidatura

## 1. Requisiti principali
- [ ] Requisito ...
  - Fonte: ...

## 2. Documenti e allegati richiesti
- [ ] Documento/allegato ...
  - Fonte: ...

## 3. Scadenze
- [ ] Scadenza ...
  - Fonte: ...

## 4. Vincoli e criteri di ammissibilita'
- [ ] Vincolo ...
  - Fonte: ...

## 5. Informazioni aziendali necessarie
- [ ] Informazione richiesta ...
  - Stato: disponibile / da verificare
  - Fonte: ...

## 6. Informazioni mancanti o da verificare
- [ ] Informazione non trovata o non deducibile dai documenti caricati.

## 7. Note per revisione umana
- Punti incerti.
- Parti da controllare manualmente.
- Eventuali ambiguita' del bando.

Regole:
- Usa solo informazioni supportate dai documenti recuperati.
- Usa il profilo aziendale solo per indicare se un'informazione sembra disponibile o da verificare.
- Per ogni punto specifico indica una fonte con pagina/sezione se disponibile.
- Se una categoria non e' supportata dal contesto, scrivi "informazione non trovata nei documenti caricati" o "da verificare".
- Non generare la candidatura completa: genera solo una checklist revisionabile.
"""


def generate_checklist(
    rag_engine: RagEngine | None = None,
    company_profile_path: str | Path = DEFAULT_COMPANY_PROFILE,
) -> dict[str, Any]:
    engine = rag_engine or RagEngine(similarity_top_k=12, streaming=False)
    company_profile = load_company_profile(company_profile_path)
    profile_context = (
        company_profile
        if company_profile
        else "Nessun profilo aziendale caricato. Le informazioni aziendali sono da verificare."
    )
    result = engine.query(
        CHECKLIST_QUERY_TEMPLATE.format(company_profile=profile_context)
    )
    return {
        "markdown": result["answer"],
        "sources": result["sources"],
        "company_profile_loaded": company_profile is not None,
    }


def save_checklist(markdown: str, output_dir: str | Path = "outputs/checklist") -> Path:
    if not markdown or not markdown.strip():
        raise ValueError("Checklist vuota: niente da salvare.")

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("checklist_*.md"))
    next_id = len(existing) + 1
    path = directory / f"checklist_{next_id:03d}.md"
    path.write_text(markdown, encoding="utf-8")
    return path
