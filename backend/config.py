import json
import os
from pathlib import Path


def _load_config(filename: str) -> dict:
    """
    Load config from the given JSON file if present alongside this module.
    Silently falls back to an empty dict on any parse error.
    """
    root = Path(__file__).resolve().parent
    cfg_path = root / filename
    if not cfg_path.exists():
        return {}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


_base_cfg = _load_config("config.json")
_local_cfg = _load_config("config.local.json")


def _get_setting(key: str, default: str | None = None) -> str | None:
    """
    Lookup order: config.local.json > config.json > env var > default.
    """
    return _local_cfg.get(key) or _base_cfg.get(key) or os.getenv(key) or default


class Settings:
    # Provider selection: "openrouter", "openai", or "dummy"
    llm_provider: str = (_get_setting("LLM_PROVIDER", "openrouter")).lower()

    openai_api_key: str | None = _get_setting("OPENAI_API_KEY")
    max_pages: int = int(_get_setting("MAX_PDF_PAGES", "5"))
    max_questions: int = int(_get_setting("MAX_QUESTIONS", "6"))

    # OpenRouter support (OpenAI-compatible API)
    openrouter_api_key: str | None = _get_setting("OPENROUTER_API_KEY")
    openrouter_base_url: str = _get_setting("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model: str = _get_setting("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    openrouter_site: str = _get_setting("OPENROUTER_SITE", "http://localhost")
    openrouter_title: str = _get_setting("OPENROUTER_TITLE", "PDF MCQ Agent")

    # App URLs (used for CORS and documentation)
    backend_url: str | None = _get_setting("BACKEND_URL")
    frontend_url: str | None = _get_setting("FRONTEND_URL")


settings = Settings()
