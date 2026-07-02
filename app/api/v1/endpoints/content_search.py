from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import content_search

router = APIRouter(prefix="/content", tags=["content"])


class ContentSearchRequest(BaseModel):
    subject: str
    keyword: str


@router.post("/search")
async def search(
    body: ContentSearchRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await content_search(
        subject=body.subject,
        keyword=body.keyword,
        teacher=teacher,
    )
