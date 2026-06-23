COMMAND_ALIASES = {
    "index": "/index",
    "/index": "/index",
    "checklist": "/checklist",
    "/checklist": "/checklist",
    "facts": "/facts",
    "/facts": "/facts",
    "summary": "/summary",
    "/summary": "/summary",
    "riassunto": "/summary",
    "/riassunto": "/summary",
    "save": "/save",
    "/save": "/save",
    "checkpoint": "/save",
    "/checkpoint": "/save",
    "profile": "/azienda",
    "/profile": "/azienda",
    "azienda": "/azienda",
    "/azienda": "/azienda",
    "status": "/status",
    "/status": "/status",
    "bando": "/bando",
    "/bando": "/bando",
    "help": "/help",
    "/help": "/help",
}


def normalize_command(content: str, command: str | None = None) -> str | None:
    candidates = [command or "", content or ""]
    for candidate in candidates:
        stripped = candidate.strip()
        if not stripped:
            continue
        normalized = stripped.lower()
        if normalized in COMMAND_ALIASES:
            return COMMAND_ALIASES[normalized]
        if normalized.startswith("/bando "):
            return f"/bando {stripped.removeprefix('/bando ').strip()}"
        if normalized.startswith("bando "):
            return f"/bando {stripped[6:].strip()}"
    return None


normalize_explicit_command = normalize_command
