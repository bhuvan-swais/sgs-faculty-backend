from datetime import date
from pydantic import BaseModel, field_validator

from app.core.dates import reject_past


class AssignmentOut(BaseModel):
    assignment_id: int
    title: str | None = None
    subject: str | None = None
    chapter_id: int | None = None
    due_date: date | None = None
    submitted_count: int = 0
    total_students: int = 0


class AssignmentListResponse(BaseModel):
    assignments: list[AssignmentOut]
    total: int


class AssignmentCreate(BaseModel):
    title: str
    text: str | None = None
    subject_id: int | None = None
    chapter_id: int | None = None
    due_date: date | None = None

    # The date picker also blocks past dates; this is the check that holds
    # when the request doesn't come from the picker.
    @field_validator("due_date")
    @classmethod
    def _due_not_past(cls, v):
        return reject_past(v, "Due date")
