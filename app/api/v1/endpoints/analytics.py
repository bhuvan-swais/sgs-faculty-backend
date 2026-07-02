from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import student_analytics, class_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


class StudentAnalyticsRequest(BaseModel):
    studentName: str
    subject: str


class ClassAnalyticsRequest(BaseModel):
    subject: str


@router.post("/student")
async def student(
    body: StudentAnalyticsRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await student_analytics(
        student_name=body.studentName,
        subject=body.subject,
        teacher=teacher,
    )


@router.post("/class")
async def class_report(
    body: ClassAnalyticsRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await class_analytics(
        subject=body.subject,
        teacher=teacher,
    )
