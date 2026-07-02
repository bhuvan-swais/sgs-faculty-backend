from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.session import get_db
from app.models.teacher import TeacherMaster
from app.models.chapter import SgsChapterContent

router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("")
def get_chapters(
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(SgsChapterContent)
        .filter(
            SgsChapterContent.chapter_id.isnot(None),
            SgsChapterContent.is_active == True,
            SgsChapterContent.record_status == "Active",
        )
        .order_by(SgsChapterContent.chapter_id)
        .all()
    )

    chapters = [
        {
            "chapter_id":    row.chapter_id,
            "chapter_name":  row.chapter_name,
            "content_title": row.content_title,
        }
        for row in rows
    ]

    return {"chapters": chapters}
