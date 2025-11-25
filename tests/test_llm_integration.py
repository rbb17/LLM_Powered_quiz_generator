from pathlib import Path

import pytest

from backend.config import settings
from backend.llm import generate_mcqs_from_text
from backend import pdf_utils
from openai import RateLimitError


@pytest.mark.openai_live
def test_generate_mcqs_from_text_live():
    """
    Integration test that exercises the OpenAI call end-to-end.
    Requires network access and OPENAI_API_KEY set.
    """
    if not settings.openai_api_key and not settings.openrouter_api_key:
        pytest.skip("No API key configured (OPENAI_API_KEY or OPENROUTER_API_KEY).")

    pdf_path = Path(__file__).parent / "test_pdf_1.pdf"
    content = pdf_utils.extract_text(pdf_path, max_pages=settings.max_pages)
    assert content.strip(), "PDF extraction should yield text"

    try:
        questions = generate_mcqs_from_text(content, max_questions=5)
    except RateLimitError as err:
        pytest.skip(f"Rate limited by provider: {err}")

    assert questions, "Expected at least one question"
    for q in questions:
        assert q.question.strip(), "Question text should be non-empty"
        assert len(q.options) == 4, "Each question should have exactly 4 options"
        assert 0 <= q.correct_option_index <= 3, "Correct option index should be within 0-3"
        assert q.hint.strip(), "Hint should be non-empty"
        assert q.explanation.strip(), "Explanation should be non-empty"

    # Debug output: show questions and answers for inspection.
    print("\nGenerated MCQs:")
    for q in questions:
        print(f"- {q.id}: {q.question}")
        for idx, opt in enumerate(q.options):
            label = chr(ord("A") + idx)
            print(f"    {label}) {opt}")
        print(f"    Correct: option {q.correct_option_index} ({q.options[q.correct_option_index]})")
        print(f"    Hint: {q.hint}")
        print(f"    Explanation: {q.explanation}")
    
