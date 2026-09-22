"""
Question papers — generate with the AI, then keep the ones worth keeping.

  POST   /question-papers/generate   ask the AI for a paper (not stored)
  POST   /question-papers            save a generated paper
  GET    /question-papers            the teacher's saved papers, newest first
  GET    /question-papers/{id}       one saved paper, full content
  DELETE /question-papers/{id}       soft delete (record_status = Deleted)

Saved papers are the source for printing and for assigning a test later.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.session import get_db
from app.models.question_paper import TeacherQuestionPaper
from app.models.teacher import TeacherMaster
from app.services.ai_service import generate_question_paper

router = APIRouter(prefix="/question-papers", tags=["question-papers"])

DELETED = "Deleted"
_LIVE = or_(TeacherQuestionPaper.record_status.is_(None),
            TeacherQuestionPaper.record_status != DELETED)


# ── schemas ───────────────────────────────────────────────────────────────────

class QuestionPaperRequest(BaseModel):
    chapterId: int
    difficulty: str = "Medium"
    totalMarks: int = 50
    questionType: str | None = None   # None = all question types


class QuestionPaperSave(BaseModel):
    title: str
    chapterId: Optional[int] = None
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    totalMarks: Optional[int] = None
    questionType: Optional[str] = None
    # One of these must be present — whichever shape the AI produced.
    paperText: Optional[str] = None
    questions: Optional[list[Any]] = None

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title is required")
        return v[:255]


class QuestionPaperSummary(BaseModel):
    paper_id: int
    title: str
    subject: Optional[str] = None
    difficulty: Optional[str] = None
    total_marks: Optional[int] = None
    question_type: Optional[str] = None
    question_count: Optional[int] = None
    created_at: Optional[datetime] = None


class QuestionPaperOut(QuestionPaperSummary):
    chapter_id: Optional[int] = None
    paper_text: Optional[str] = None
    questions: Optional[list[Any]] = None


class QuestionPaperListResponse(BaseModel):
    papers: list[QuestionPaperSummary]
    total: int


def _summary(p: TeacherQuestionPaper) -> QuestionPaperSummary:
    return QuestionPaperSummary(
        paper_id=p.paper_id, title=p.title, subject=p.subject, difficulty=p.difficulty,
        total_marks=p.total_marks, question_type=p.question_type,
        question_count=len(p.questions) if isinstance(p.questions, list) else None,
        created_at=p.created_at,
    )


def _out(p: TeacherQuestionPaper) -> QuestionPaperOut:
    return QuestionPaperOut(**_summary(p).model_dump(), chapter_id=p.chapter_id,
                            paper_text=p.paper_text, questions=p.questions)


def _mine(db: Session, teacher_id: int, paper_id: int) -> TeacherQuestionPaper | None:
    return db.query(TeacherQuestionPaper).filter(
        TeacherQuestionPaper.paper_id == paper_id,
        TeacherQuestionPaper.teacher_id == teacher_id,
        _LIVE,
    ).first()


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate(
    body: QuestionPaperRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await generate_question_paper(
        chapter_id=body.chapterId,
        difficulty=body.difficulty,
        total_marks=body.totalMarks,
        question_type=body.questionType,
        teacher=teacher,
    )


@router.post("", response_model=QuestionPaperOut, status_code=status.HTTP_201_CREATED)
def save_paper(
    body: QuestionPaperSave,
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    text = (body.paperText or "").strip() or None
    questions = body.questions or None
    if not text and not questions:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nothing to save — the paper is empty")

    paper = TeacherQuestionPaper(
        teacher_id=teacher.teacher_id,
        chapter_id=body.chapterId,
        title=body.title,
        subject=body.subject,
        difficulty=body.difficulty,
        total_marks=body.totalMarks,
        question_type=body.questionType,
        paper_text=text,
        questions=questions,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        record_status="Active",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return _out(paper)


@router.get("", response_model=QuestionPaperListResponse)
def list_papers(
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    papers = (
        db.query(TeacherQuestionPaper)
        .filter(TeacherQuestionPaper.teacher_id == teacher.teacher_id, _LIVE)
        .order_by(TeacherQuestionPaper.created_at.desc().nullslast())
        .all()
    )
    return QuestionPaperListResponse(papers=[_summary(p) for p in papers], total=len(papers))


@router.get("/{paper_id}", response_model=QuestionPaperOut)
def get_paper(
    paper_id: int,
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    paper = _mine(db, teacher.teacher_id, paper_id)
    if not paper:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question paper not found")
    return _out(paper)


@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paper(
    paper_id: int,
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    paper = _mine(db, teacher.teacher_id, paper_id)
    if not paper:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question paper not found")
    paper.record_status = DELETED
    db.commit()
