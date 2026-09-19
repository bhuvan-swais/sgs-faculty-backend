from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_teacher
from app.models.teacher    import TeacherMaster
from app.models.student    import StudentMaster
from app.models.assessment import Assessment, AssessmentResult
from app.schemas.report    import ReportResponse, StudentReportRow
from app.services import student_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportResponse)
def get_report(
    teacher: TeacherMaster = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    tid = teacher.teacher_id
    # Same roll as the Dashboard headcount and the Students tab — see
    # student_service. This used to filter on class_id alone, so inactive and
    # deleted students were counted here but nowhere else.
    students = (
        student_service.roll_query(db, teacher.class_id)
        .order_by(StudentMaster.roll_no)
        .all()
    )
    assessments = db.query(Assessment).filter(Assessment.teacher_id == tid).all()
    total_assessments = len(assessments)

    rows: list[StudentReportRow] = []
    for student in students:
        marks_list = [
            float(r.marks_obtained)
            for r in student.results
            if not r.is_absent and r.marks_obtained is not None
            and r.assessment.teacher_id == tid
        ]
        pct_list = [
            float(r.marks_obtained) / float(r.assessment.max_marks) * 100
            for r in student.results
            if not r.is_absent and r.marks_obtained is not None
            and r.assessment.teacher_id == tid
        ]

        avg_pct = round(sum(pct_list) / len(pct_list), 1) if pct_list else None
        avg_raw = round(sum(marks_list) / len(marks_list), 1) if marks_list else None

        rows.append(StudentReportRow(
            student_id=student.student_id,
            name=student.full_name or "",
            roll_number=student.roll_no or "",
            total_assessed=len(marks_list),
            average_marks=avg_raw,
            average_percent=avg_pct,
            highest_marks=max(marks_list) if marks_list else None,
            lowest_marks=min(marks_list) if marks_list else None,
            rank=0,
        ))

    rows.sort(key=lambda r: (-(r.average_percent or 0), r.roll_number))
    for i, row in enumerate(rows, start=1):
        row.rank = i

    return ReportResponse(
        teacher_id=tid,
        class_name=str(teacher.class_id) if teacher.class_id else "8",
        section=teacher.section_1 or "A",
        total_students=len(students),
        total_assessments=total_assessments,
        students=rows,
    )
