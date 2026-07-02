from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import translate_text, translate_audio

router = APIRouter(prefix="/translate", tags=["translate"])


class TextTranslateRequest(BaseModel):
    text: str
    targetLanguage: str


class AudioTranslateRequest(BaseModel):
    audioFile: str
    targetLanguage: str


@router.post("/text")
async def translate_text_endpoint(
    body: TextTranslateRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await translate_text(
        text=body.text,
        target_language=body.targetLanguage,
        teacher=teacher,
    )


@router.post("/audio")
async def translate_audio_endpoint(
    body: AudioTranslateRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await translate_audio(
        audio_file=body.audioFile,
        target_language=body.targetLanguage,
        teacher=teacher,
    )
