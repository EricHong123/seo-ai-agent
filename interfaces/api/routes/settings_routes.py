"""Settings API — read/write .env configuration from the Web UI."""

import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])

ENV_PATH = Path(__file__).parent.parent.parent.parent / ".env"


class SettingsData(BaseModel):
    deepseek_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_llm: str = "deepseek"
    google_credentials_file: str = ""
    gsc_site_url: str = ""
    pagespeed_api_key: str = ""
    semrush_api_key: str = ""


def _read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    result = {}
    for line in ENV_PATH.read_text().split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value
    return result


ALLOWED_KEYS = {
    "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
    "DEFAULT_LLM", "GOOGLE_CREDENTIALS_FILE", "GSC_SITE_URL",
    "PAGESPEED_API_KEY", "SEMRUSH_API_KEY",
    "DB_URL", "CHROMA_PERSIST_DIR", "MAX_TOKENS",
}


def _write_env(updates: dict[str, str]):
    current = _read_env()
    for key, value in updates.items():
        if key not in ALLOWED_KEYS:
            continue  # Reject unknown keys
        # Strip newlines and other control characters
        sanitized = value.replace("\n", "").replace("\r", "").replace("\x00", "").strip()
        current[key] = sanitized

    lines = []
    for key in ALLOWED_KEYS:
        value = current.get(key, "")
        if value:
            lines.append(f"{key}={value}")
        else:
            lines.append(f"# {key}=")

    ENV_PATH.write_text("\n".join(lines) + "\n")


@router.get("", response_model=SettingsData)
async def get_settings():
    env = _read_env()
    return SettingsData(
        deepseek_api_key=_mask_key(env.get("DEEPSEEK_API_KEY", "")),
        anthropic_api_key=_mask_key(env.get("ANTHROPIC_API_KEY", "")),
        openai_api_key=_mask_key(env.get("OPENAI_API_KEY", "")),
        default_llm=env.get("DEFAULT_LLM", "deepseek"),
        google_credentials_file=env.get("GOOGLE_CREDENTIALS_FILE", ""),
        gsc_site_url=env.get("GSC_SITE_URL", ""),
        pagespeed_api_key=env.get("PAGESPEED_API_KEY", ""),
        semrush_api_key=env.get("SEMRUSH_API_KEY", ""),
    )


@router.put("")
async def update_settings(data: SettingsData):
    updates = {}

    if data.deepseek_api_key and not data.deepseek_api_key.startswith("sk-***"):
        updates["DEEPSEEK_API_KEY"] = data.deepseek_api_key
    if data.anthropic_api_key and not data.anthropic_api_key.startswith("sk-ant-***"):
        updates["ANTHROPIC_API_KEY"] = data.anthropic_api_key
    if data.openai_api_key and not data.openai_api_key.startswith("sk-***"):
        updates["OPENAI_API_KEY"] = data.openai_api_key
    if data.default_llm:
        updates["DEFAULT_LLM"] = data.default_llm
    if data.google_credentials_file is not None:
        updates["GOOGLE_CREDENTIALS_FILE"] = data.google_credentials_file
    if data.gsc_site_url is not None:
        updates["GSC_SITE_URL"] = data.gsc_site_url
    if data.pagespeed_api_key is not None:
        updates["PAGESPEED_API_KEY"] = data.pagespeed_api_key
    if data.semrush_api_key is not None:
        updates["SEMRUSH_API_KEY"] = data.semrush_api_key

    if not updates:
        return {"status": "no_changes"}

    _write_env(updates)

    # Hot-reload: update the global settings singleton immediately
    from config.settings import settings as global_settings
    for key, value in updates.items():
        setting_key = key.lower()
        if hasattr(global_settings, setting_key):
            setattr(global_settings, setting_key, value)

    return {"status": "saved", "updated_keys": list(updates.keys()), "hot_reloaded": True}


@router.post("/reload")
async def reload_settings():
    """Force reload settings from .env (for when env vars are changed externally)."""
    from config.settings import Settings
    import importlib
    import config.settings as settings_module
    importlib.reload(settings_module)
    return {"status": "reloaded"}


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 12:
        return key[:4] + "***"
    return key[:8] + "***" + key[-4:]
