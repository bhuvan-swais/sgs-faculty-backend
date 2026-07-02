from fastapi import APIRouter, Depends

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import get_assignment_reminders, get_completion_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/due-date")
async def due_date_alerts(
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await get_assignment_reminders(teacher)


@router.post("/completion")
async def completion_alerts(
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await get_completion_alerts(teacher)
