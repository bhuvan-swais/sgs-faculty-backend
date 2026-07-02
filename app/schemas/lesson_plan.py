from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LessonPlanGenerateRequest(BaseModel):
    chapterId: int
    chapterName: str
    durationMinutes: int = 45


class LessonPlanSaveRequest(BaseModel):
    plan: dict


class LessonPlanOut(BaseModel):
    lesson_plan_id: int
    title: str
    chapter_text: Optional[str]
    duration_minutes: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class LessonPlanListResponse(BaseModel):
    plans: list[LessonPlanOut]
