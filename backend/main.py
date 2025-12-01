import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend import pdf_utils, storage
from backend.config import settings
from backend.llm import generate_mcqs_from_text
from backend.models import (
    AnswerRequest,
    AnswerResponse,
    Quiz,
    QuizResponse, 
    QuizResponseQuestion,
    UploadResponse,
    ConfigResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("pdf_mcq_backend")

app = FastAPI(title="PDF MCQ Agent", version="0.1.0")

# Allow local dev frontends. Tighten in production.
cors_origins = ["*"]
if settings.frontend_url:
    cors_origins = [settings.frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request, call_next):
    client_host = request.client.host if request.client else "unknown"
    logger.info("Incoming request %s %s from %s", request.method, request.url.path, client_host)
    try:
        response = await call_next(request)
        logger.info("Completed request %s %s -> %s", request.method, request.url.path, response.status_code)
        return response
    except Exception:
        logger.exception("Error handling request %s %s", request.method, request.url.path)
        raise


@app.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    num_questions: int | None = Form(None),
) -> UploadResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        text = pdf_utils.extract_text(tmp_path, max_pages=settings.max_pages)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    requested = num_questions or settings.max_questions
    target_questions = min(max(requested, 1), settings.max_questions)

    questions = generate_mcqs_from_text(text, max_questions=target_questions)
    quiz_id = uuid.uuid4().hex
    quiz = Quiz(quiz_id=quiz_id, source_pdf_name=file.filename, questions=questions)
    storage.save_quiz(quiz)
    return UploadResponse(quiz_id=quiz_id, num_questions=len(questions))


@app.get("/quiz/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str) -> QuizResponse:
    quiz = storage.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions = [
        QuizResponseQuestion(
            id=q.id,
            question=q.question,
            options=q.options,
            is_correct=q.is_correct,
        )
        for q in quiz.questions
    ]
    return QuizResponse(quiz_id=quiz.quiz_id, completed=quiz.completed, questions=questions)


@app.post("/quiz/{quiz_id}/answer", response_model=AnswerResponse)
def submit_answer(quiz_id: str, payload: AnswerRequest) -> AnswerResponse:
    quiz = storage.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    question = next((q for q in quiz.questions if q.id == payload.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    if payload.selected_option_index < 0 or payload.selected_option_index >= len(question.options):
        raise HTTPException(status_code=400, detail="Invalid option index.")

    is_correct = payload.selected_option_index == question.correct_option_index
    if is_correct:
        question.is_correct = True
        quiz.completed = storage.all_correct(quiz.questions)
    storage.save_quiz(quiz)

    return AnswerResponse(
        correct=is_correct,
        explanation=question.explanation if is_correct else None,
        hint=None if is_correct else question.hint,
        question_completed=is_correct,
        quiz_completed=quiz.completed,
    )


@app.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(max_questions=settings.max_questions, max_pages=settings.max_pages)
