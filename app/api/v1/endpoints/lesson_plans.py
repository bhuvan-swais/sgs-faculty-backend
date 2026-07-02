import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.session import get_db
from app.models.lesson_plan import TeacherLessonPlan
from app.models.teacher import TeacherMaster
from app.schemas.lesson_plan import (
    LessonPlanGenerateRequest,
    LessonPlanSaveRequest,
    LessonPlanListResponse,
    LessonPlanOut,
)
from app.services.ai_service import generate_lesson_plan

router = APIRouter(prefix="/lesson-plans", tags=["lesson-plans"])


@router.post("/generate")
async def generate(
    body: LessonPlanGenerateRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    """Call Node.js AI service and return a structured lesson plan."""
    return await generate_lesson_plan(
        chapter_id=body.chapterId,
        chapter_name=body.chapterName,
        duration_minutes=body.durationMinutes,
        teacher=teacher,
    )


@router.get("", response_model=LessonPlanListResponse)
def list_plans(
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    plans = (
        db.query(TeacherLessonPlan)
        .filter(TeacherLessonPlan.teacher_id == teacher.teacher_id)
        .order_by(TeacherLessonPlan.created_at.desc())
        .all()
    )
    return LessonPlanListResponse(plans=plans)


@router.post("", status_code=status.HTTP_201_CREATED)
def save_plan(
    body: LessonPlanSaveRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    plan = body.plan
    record = TeacherLessonPlan(
        teacher_id=teacher.teacher_id,
        title=plan.get("title", "Untitled Plan"),
        chapter_text=plan.get("chapter_text"),
        duration_minutes=plan.get("duration_minutes"),
        plan_data=json.dumps(plan),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"lesson_plan_id": record.lesson_plan_id, "message": "Plan saved"}


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    record = db.query(TeacherLessonPlan).filter(
        TeacherLessonPlan.lesson_plan_id == plan_id,
        TeacherLessonPlan.teacher_id == teacher.teacher_id,
    ).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    db.delete(record)
    db.commit()
