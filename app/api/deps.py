"""
Shared FastAPI dependencies.
get_current_teacher — verifies JWT and returns the authenticated teacher's ID.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.core.security import decode_token
from app.models.teacher import TeacherMaster
from app.models.user import UserMaster

bearer_scheme = HTTPBearer()

_DEV_TEACHER = TeacherMaster(
    teacher_id=1,
    full_name="Dev Teacher",
    email_id="dev@swais.edu",
    subject_name="Social Studies",
    class_id=8,
    section_1="A",
    is_active=True,
)


def get_current_teacher(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> TeacherMaster:
    token = credentials.credentials

    if settings.APP_ENV == "development" and token == "dev":
        return _DEV_TEACHER

    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    teacher_id: int = payload.get("teacher_id")
    if not teacher_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing teacher_id")

    teacher = db.query(TeacherMaster).filter(TeacherMaster.teacher_id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    return teacher
