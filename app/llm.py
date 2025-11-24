import json
import time
import uuid
from typing import List, Tuple

from openai import OpenAI, RateLimitError

from .config import settings
from .models import Question


MCQ_SYSTEM_PROMPT = """You are a teaching assistant. Given input text, create clear multiple-choice questions.
Each question must have 4 options, exactly one correct answer, a short hint, and a brief explanation.
Respond ONLY with JSON that follows the provided schema."""


MCQ_USER_PROMPT = """Text:
{content}

Generate up to {max_questions} multiple-choice questions that test understanding of this text.
Respond in exactly this JSON structure:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_option_index": 1,
      "hint": "string",
      "explanation": "string"
    }}
  ]
}}"""


def _dummy_questions() -> List[Question]:
    # Simple fallback when no API key is configured.
    options = ["Option A", "Option B", "Option C", "Option D"]
    return [
        Question(
            id="q1",
            question="Sample question because OPENAI_API_KEY is not set.",
            options=options,
            correct_option_index=0,
            hint="Pretend you read the PDF and recall the key idea.",
            explanation="This is a placeholder. Configure OPENAI_API_KEY to generate from the PDF.",
        )
    ]


def _parse_questions(raw_json: str) -> List[Question]:
    payload = json.loads(raw_json)
    questions = payload.get("questions", [])
    parsed: list[Question] = []
    for idx, q in enumerate(questions, start=1):
        parsed.append(
            Question(
                id=q.get("id") or f"q{idx}",
                question=q["question"],
                options=q["options"],
                correct_option_index=q["correct_option_index"],
                hint=q["hint"],
                explanation=q["explanation"],
            )
        )
    return parsed


def _select_client_and_model() -> Tuple[OpenAI, str] | tuple[None, None]:
    """
    Returns (client, model) or (None, None) if no keys are set.
    Provider selection order is controlled by settings.llm_provider.
    """
    provider = settings.llm_provider

    if provider == "openrouter":
        if settings.openrouter_api_key:
            client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                default_headers={
                    # OpenRouter recommends setting these for tracking.
                    "HTTP-Referer": settings.openrouter_site,
                    "X-Title": settings.openrouter_title,
                },
            )
            return client, settings.openrouter_model
        # fallthrough to openai if configured
        if settings.openai_api_key:
            client = OpenAI(api_key=settings.openai_api_key)
            return client, "gpt-4o-mini"

    if provider == "openai":
        if settings.openai_api_key:
            client = OpenAI(api_key=settings.openai_api_key)
            return client, "gpt-4o-mini"
        # fallthrough to openrouter if configured
        if settings.openrouter_api_key:
            client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                default_headers={
                    "HTTP-Referer": settings.openrouter_site,
                    "X-Title": settings.openrouter_title,
                },
            )
            return client, settings.openrouter_model

    # explicit dummy or nothing set
    return None, None

def generate_mcqs_from_text(content: str, max_questions: int) -> List[Question]:
    client, model = _select_client_and_model()
    if not client:
        return _dummy_questions()

    # Simple backoff to reduce 429s when quota is tight.
    last_err: RateLimitError | None = None
    for attempt, delay in enumerate([0, 2, 4], start=1):
        try:
            message = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": MCQ_SYSTEM_PROMPT},
                    {"role": "user", "content": MCQ_USER_PROMPT.format(content=content, max_questions=max_questions)},
                ],
                temperature=0.3,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            break
        except RateLimitError as err:
            last_err = err
            if attempt == 3:
                raise
            time.sleep(delay)
    else:
        # Should not reach; defensive
        raise last_err or RuntimeError("Unexpected OpenAI error")

    raw_json = message.choices[0].message.content
    questions = _parse_questions(raw_json)
    # Ensure stable IDs
    for q in questions:
        if not q.id:
            q.id = f"q{uuid.uuid4().hex[:8]}"
    return questions
