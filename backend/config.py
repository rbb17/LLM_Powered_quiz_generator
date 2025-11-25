import json
import os
from pathlib import Path


def _load_local_config() -> dict:
    """
    Load API keys and overrides from config.local.json if present.
    File is expected alongside this module (backend/config.local.json).
    """
    root = Path(__file__).resolve().parent
    cfg_path = root / "config.local.json"
    if not cfg_path.exists():
        return {}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fall back silently if file is malformed.
        return {}


_local_cfg = _load_local_config()


class Settings:
    # Provider selection: "openrouter", "openai", or "dummy"
    llm_provider: str = (_local_cfg.get("LLM_PROVIDER") or os.getenv("LLM_PROVIDER") or "openrouter").lower()

    openai_api_key: str | None = _local_cfg.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    max_pages: int = int(_local_cfg.get("MAX_PDF_PAGES") or os.getenv("MAX_PDF_PAGES", "5"))
    max_questions: int = int(_local_cfg.get("MAX_QUESTIONS") or os.getenv("MAX_QUESTIONS", "6"))

    # OpenRouter support (OpenAI-compatible API)
    openrouter_api_key: str | None = _local_cfg.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: str = _local_cfg.get("OPENROUTER_BASE_URL") or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model: str = _local_cfg.get("OPENROUTER_MODEL") or os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
    openrouter_site: str = _local_cfg.get("OPENROUTER_SITE") or os.getenv("OPENROUTER_SITE", "http://localhost")
    openrouter_title: str = _local_cfg.get("OPENROUTER_TITLE") or os.getenv("OPENROUTER_TITLE", "PDF MCQ Agent")

    # App URLs (used for CORS and documentation)
    backend_url: str | None = _local_cfg.get("BACKEND_URL") or os.getenv("BACKEND_URL")
    frontend_url: str | None = _local_cfg.get("FRONTEND_URL") or os.getenv("FRONTEND_URL")


settings = Settings()
