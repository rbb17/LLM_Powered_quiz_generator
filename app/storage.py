from collections.abc import Iterable
from typing import Dict

from .models import Quiz, Question

# In-memory store keyed by quiz_id.
QUIZ_STORE: Dict[str, Quiz] = {}


def save_quiz(quiz: Quiz) -> None:
    QUIZ_STORE[quiz.quiz_id] = quiz


def get_quiz(quiz_id: str) -> Quiz | None:
    return QUIZ_STORE.get(quiz_id)


def all_correct(questions: Iterable[Question]) -> bool:
    return all(q.is_correct for q in questions)
