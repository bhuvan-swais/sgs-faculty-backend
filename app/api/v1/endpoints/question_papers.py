from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import generate_question_paper

router = APIRouter(prefix="/question-papers", tags=["question-papers"])


class QuestionPaperRequest(BaseModel):
    chapterId: int
    difficulty: str = "Medium"
    totalMarks: int = 50


@router.post("/generate")
async def generate(
    body: QuestionPaperRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await generate_question_paper(
        chapter_id=body.chapterId,
        difficulty=body.difficulty,
        total_marks=body.totalMarks,
        teacher=teacher,
    )
