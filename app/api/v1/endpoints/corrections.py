from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import correct_answer

router = APIRouter(prefix="/corrections", tags=["corrections"])


class CorrectionRequest(BaseModel):
    question: str
    studentAnswer: str
    maxMarks: int = 5
    rubric: str = ""


@router.post("/check")
async def check(
    body: CorrectionRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await correct_answer(
        question=body.question,
        student_answer=body.studentAnswer,
        max_marks=body.maxMarks,
        rubric=body.rubric,
        teacher=teacher,
    )
