from pathlib import Path

DEFAULT_COMPANY_PROFILE = Path("data/aziende/mapi_ingegneria.yaml")


def load_company_profile(path: str | Path = DEFAULT_COMPANY_PROFILE) -> str | None:
    profile_path = Path(path)
    if not profile_path.exists():
        return None

    content = profile_path.read_text(encoding="utf-8").strip()
    return content or None
