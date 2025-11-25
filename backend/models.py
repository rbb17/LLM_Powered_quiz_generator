from pydantic import BaseModel, Field
from typing import List, Optional


class Question(BaseModel):
    id: str
    question: str
    options: List[str] = Field(min_items=4, max_items=4)
    correct_option_index: int = Field(ge=0, le=3)
    hint: str
    explanation: str
    is_correct: bool = False


class Quiz(BaseModel):
    quiz_id: str
    source_pdf_name: str
    questions: List[Question]
    completed: bool = False


class UploadResponse(BaseModel):
    quiz_id: str
    num_questions: int


class QuizResponseQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    is_correct: bool


class QuizResponse(BaseModel):
    quiz_id: str
    completed: bool
    questions: List[QuizResponseQuestion]


class AnswerRequest(BaseModel):
    question_id: str
    selected_option_index: int


class AnswerResponse(BaseModel):
    correct: bool
    explanation: Optional[str] = None
    hint: Optional[str] = None
    question_completed: bool
    quiz_completed: bool


class ConfigResponse(BaseModel):
    max_questions: int
    max_pages: int
