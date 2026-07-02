from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_teacher
from app.models.teacher import TeacherMaster
from app.services.ai_service import speech_to_text, text_to_speech

router = APIRouter(prefix="/speech", tags=["speech"])


class SpeechToTextRequest(BaseModel):
    audioFile: str
    language: str = "English"


class TextToSpeechRequest(BaseModel):
    text: str
    language: str = "English"
    voice: str = "Female"


@router.post("/to-text")
async def stt(
    body: SpeechToTextRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await speech_to_text(
        audio_file=body.audioFile,
        language=body.language,
        teacher=teacher,
    )


@router.post("/to-voice")
async def tts(
    body: TextToSpeechRequest,
    teacher: TeacherMaster = Depends(get_current_teacher),
):
    return await text_to_speech(
        text=body.text,
        language=body.language,
        voice=body.voice,
        teacher=teacher,
    )
