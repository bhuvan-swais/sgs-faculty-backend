from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import virtual_slate

router = APIRouter(prefix="/virtual-slate", tags=["virtual-slate"])


class VirtualSlateRequest(BaseModel):
    rawText: str
    action: str = "format"


@router.post("/format")
async def format_slate(
    body: VirtualSlateRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await virtual_slate(
        raw_text=body.rawText,
        action=body.action,
        teacher=teacher,
    )
