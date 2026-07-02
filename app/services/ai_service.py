import re
import math
import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_TIMEOUT = 60.0


# ── Helpers ──────────────────────────────────────────────────────────────────

def _user_info(teacher) -> dict:
    return {
        "id": teacher.teacher_id,
        "name": teacher.full_name or "",
        "email": teacher.email_id or "",
        "role": "Teacher",
    }


def _ai_error(e: Exception):
    if isinstance(e, httpx.TimeoutException):
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="AI service timed out")
    if isinstance(e, httpx.HTTPStatusError):
        try:
            body = e.response.json()
            detail = body.get("details") or body.get("error") or body.get("message") or "AI service error"
        except Exception:
            detail = "AI service error"
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI service unreachable")


def _extract_section(text: str, heading: str) -> str:
    """Return the raw text block under a numbered section heading."""
    pattern = rf'\d+\.\s+{re.escape(heading)}.*?\n(.*?)(?=\n\d+\.\s+|\Z)'
    m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _bullets(block: str) -> list[str]:
    """Convert a text block of bullet points into a list of strings."""
    items = []
    for line in block.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip leading bullet markers
        cleaned = re.sub(r'^[-•*\d]+[.)]\s*', '', line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _parse_lesson_plan(raw_text: str, chapter: str, duration: int, objectives: list, teacher) -> dict:
    """
    Convert the Node.js plain-text lesson plan into the structured dict
    that the frontend PlanDisplay component expects.
    """
    obj_block   = _extract_section(raw_text, "Learning Objectives")
    mat_block   = _extract_section(raw_text, "Materials Required")
    intro_block = _extract_section(raw_text, "Lesson Introduction")
    steps_block = _extract_section(raw_text, "Step-by-Step Teaching Activities")
    qa_block    = _extract_section(raw_text, "Classroom Interaction Questions")
    assess_block= _extract_section(raw_text, "Assessment Questions")
    hw_block    = _extract_section(raw_text, "Homework")

    parsed_objectives = _bullets(obj_block) or objectives or [
        "Understand the key concepts of the chapter",
        "Apply knowledge through classroom activities",
    ]
    parsed_materials = _bullets(mat_block) or ["Textbook", "Blackboard", "Chalk"]

    # Build three plan sections proportional to duration
    intro_dur = max(5,  math.floor(duration * 0.20))
    core_dur  = max(10, math.floor(duration * 0.55))
    assess_dur= duration - intro_dur - core_dur

    plan_sections = [
        {
            "title": "Introduction",
            "duration": intro_dur,
            "activity": "Lesson Opening & Warm-up",
            "teacher_action": _bullets(intro_block)[0] if _bullets(intro_block) else "Introduce the topic and context",
            "student_action": "Listen, recall prior knowledge, and engage",
        },
        {
            "title": "Core Teaching",
            "duration": core_dur,
            "activity": "Step-by-Step Instruction",
            "teacher_action": _bullets(steps_block)[0] if _bullets(steps_block) else "Explain key concepts with examples",
            "student_action": "Take notes and participate in discussion",
        },
        {
            "title": "Assessment & Wrap-up",
            "duration": assess_dur,
            "activity": "Interactive Q&A and Closure",
            "teacher_action": _bullets(qa_block)[0] if _bullets(qa_block) else "Ask questions to check understanding",
            "student_action": "Answer questions and summarise learning",
        },
    ]

    return {
        "title": f"Lesson Plan: {chapter}",
        "duration_minutes": duration,
        "class_name": str(teacher.class_id or ""),
        "section": teacher.section_1 or "",
        "subject": teacher.subject_name or "",
        "chapter_text": chapter,
        "objectives": parsed_objectives[:5],
        "materials": parsed_materials[:8],
        "core_concept": intro_block.split("\n")[0] if intro_block else None,
        "plan_sections": plan_sections,
        "assessment_method": "\n".join(_bullets(assess_block)[:3]) or "Oral questioning and short written response",
        "homework": "\n".join(_bullets(hw_block)[:3]) or "Complete the chapter exercises in the textbook",
    }


# ── Internal chat caller ─────────────────────────────────────────────────────

async def _chat(message: str, target_language: str, teacher) -> str:
    """Call Node.js /api/v1/ai/teacher/chat and return the reply text."""
    payload = {
        "message": message,
        "targetLanguage": target_language,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/chat",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("reply") or data.get("message") or data.get("response") or ""
    except Exception as e:
        _ai_error(e)


# ── Public functions ──────────────────────────────────────────────────────────

async def generate_lesson_plan(
    chapter_id: int,
    chapter_name: str,
    duration_minutes: int,
    teacher,
) -> dict:
    payload = {
        "chapterId": chapter_id,
        "durationMinutes": duration_minutes,
        "userInfo": _user_info(teacher),
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/lesson-plan",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            raw_text = data.get("lessonPlan", "")
            return _parse_lesson_plan(raw_text, chapter_name, duration_minutes, [], teacher)
    except Exception as e:
        _ai_error(e)


async def generate_question_paper(
    chapter_id: int,
    difficulty: str,
    total_marks: int,
    teacher,
) -> dict:
    payload = {
        "chapterId": chapter_id,
        "difficulty": difficulty,
        "totalMarks": total_marks,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/question-paper",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def correct_answer(
    question: str,
    student_answer: str,
    max_marks: int,
    rubric: str,
    teacher,
) -> dict:
    payload = {
        "question": question,
        "studentAnswer": student_answer,
        "maxMarks": max_marks,
        "rubric": rubric,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/correct-answer",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def get_assignment_reminders(teacher) -> dict:
    payload = {"userInfo": _user_info(teacher)}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/assignment-reminders",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def get_completion_alerts(teacher) -> dict:
    payload = {"userInfo": _user_info(teacher)}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/completion-alerts",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def virtual_slate(raw_text: str, action: str, teacher) -> dict:
    payload = {
        "rawText": raw_text,
        "action": action,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/virtual-slate",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def student_analytics(student_name: str, subject: str, teacher) -> dict:
    payload = {
        "studentName": student_name,
        "subject": subject,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/student-analytics",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def class_analytics(subject: str, teacher) -> dict:
    payload = {
        "subject": subject,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/class-analytics",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def translate_text(text: str, target_language: str, teacher) -> dict:
    payload = {
        "text": text,
        "targetLanguage": target_language,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/translate",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def translate_audio(audio_file: str, target_language: str, teacher) -> dict:
    payload = {
        "audioFile": audio_file,
        "targetLanguage": target_language,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/audio-translate",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def speech_to_text(audio_file: str, language: str, teacher) -> dict:
    payload = {
        "audioFile": audio_file,
        "language": language,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/speech-to-text",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def text_to_speech(text: str, language: str, voice: str, teacher) -> dict:
    payload = {
        "text": text,
        "language": language,
        "voice": voice,
        "userInfo": _user_info(teacher),
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/text-to-speech",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)


async def content_search(subject: str, keyword: str, teacher) -> dict:
    payload = {
        "subject": subject,
        "keyword": keyword,
        "teacherId": teacher.teacher_id,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/ai/teacher/content-search",
                json=payload,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        _ai_error(e)
