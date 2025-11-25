## PDF → MCQ Learning Agent (FastAPI backend)

Minimal FastAPI service that:
- Accepts PDF upload
- Extracts text
- Generates MCQs via OpenAI (fallback stub if no API key)
- Stores quiz state in memory and lets clients answer with hints/explanations

### Endpoints
- `POST /upload-pdf` — multipart `file`; returns `{quiz_id, num_questions}`
- `GET /quiz/{quiz_id}` — returns quiz (without correct answers)
- `POST /quiz/{quiz_id}/answer` — body `{question_id, selected_option_index}`; returns correctness + hint/explanation
- `GET /config` — returns `max_questions`, `max_pages`

### Project layout
```
backend/
  main.py        # FastAPI app + routes
  models.py      # Pydantic models
  storage.py     # In-memory quiz store
  pdf_utils.py   # PDF text extraction
  llm.py         # OpenAI MCQ generator (with stub fallback)
  config.py      # Basic settings (env-driven)
  requirements.txt
  config.example.json
  config.local.json (gitignored)
frontend/
  index.html
  app.js
  styles.css
  config.example.json
```

### Setup (local dev)
1) Create venv (optional): `python -m venv .venv && source .venv/bin/activate`
2) Install deps: `pip install -r backend/requirements.txt`
3) Configure LLM provider and keys:
   - Copy `backend/config.example.json` → `backend/config.local.json`, set `LLM_PROVIDER` to `openrouter`, `openai`, or `dummy`, and fill in keys accordingly.
   - Env vars still work and override missing fields.
   - `BACKEND_URL` / `FRONTEND_URL` in config are used for CORS and docs; adjust as needed.
4) Run server: `uvicorn backend.main:app --reload --port 8000` From the main directory.

### Tests
- Install deps (already in `backend/requirements.txt`).
- Live integration test (requires `OPENAI_API_KEY` or `OPENROUTER_API_KEY` and network): `pytest -m openai_live`

### Frontend (vanilla JS)
- Files live in `frontend/` (`index.html`, `app.js`, `styles.css`, `config.example.json`).
- Copy `frontend/config.example.json` → `frontend/config.local.json` and set `BACKEND_URL` (e.g., `http://localhost:8000`).
- Quick run (from repo root): `python -m http.server 3000 --directory frontend`
  - Then open `http://localhost:3000` and upload a PDF; it will call the backend using the URL from the frontend config.

### Notes
- If `OPENAI_API_KEY` is missing, the service returns a single dummy question.
- Text extraction reads the first `MAX_PDF_PAGES` (env, default 5) and generates up to `MAX_QUESTIONS` (env, default 6).
- CORS is wide open for local prototyping; tighten for production.
- To use OpenRouter, set `OPENROUTER_API_KEY` (and optionally `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`, `OPENROUTER_SITE`). Config can be in `backend/config.local.json`.



### Running tests->
- python -m pytest -m openai_live

Run pytest with stdout + skip reasons:
- python -m pytest -m openai_live -s -rs
