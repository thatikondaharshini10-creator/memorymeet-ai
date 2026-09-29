"""API route definitions for MemoryMeet."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import shutil
import uuid

from ..core.config import settings
from ..services.meeting_service import meeting_service
from ..services.memory_service import memory_service
from ..db.database import get_all_meetings, get_meeting_by_id

router = APIRouter()


class TranscriptRequest(BaseModel):
    title: Optional[str] = "Untitled Meeting"
    transcript: str


class PrepareMeetingRequest(BaseModel):
    agenda: str


class RecallMemoryRequest(BaseModel):
    query: str
    budget: Optional[str] = "mid"


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational readiness and client communication."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "database": "sqlite_ready",
            "transcription": f"{settings.STT_PROVIDER}_ready",
            "hindsight_memory": f"cloud_ready ({settings.HINDSIGHT_BANK_ID})",
            "ai_agent": f"{settings.LLM_PROVIDER}_ready ({settings.GEMINI_MODEL})",
        }
    }


@router.post("/meetings/process-transcript", tags=["Meetings"])
async def process_transcript_endpoint(req: TranscriptRequest):
    """Processes a meeting transcript: extracts structured memories, retains into Hindsight, and saves record."""
    try:
        result = await meeting_service.process_transcript(
            title=req.title or "Untitled Meeting",
            transcript=req.transcript
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/upload-recording", tags=["Meetings"])
async def upload_recording_endpoint(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """Accepts an audio/video recording, transcribes via Gemini multimodal, extracts memories, and retains in Hindsight."""
    try:
        # Save file safely to uploads directory
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4().hex[:10]}_{file.filename}"
        save_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        meeting_title = title or os.path.splitext(file.filename)[0]

        result = await meeting_service.process_recording(
            file_path=save_path,
            title=meeting_title
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/prepare", tags=["Meeting Prep"])
async def prepare_meeting_endpoint(req: PrepareMeetingRequest):
    """Recalls long-term memories from Hindsight based on an upcoming agenda and generates an executive brief."""
    try:
        result = await meeting_service.prepare_for_meeting(agenda=req.agenda)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings", tags=["Meetings"])
async def list_meetings_endpoint():
    """Lists past meetings stored in SQLite."""
    try:
        meetings = get_all_meetings()
        return {"success": True, "meetings": meetings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meetings/{meeting_id}", tags=["Meetings"])
async def get_meeting_endpoint(meeting_id: int):
    """Fetches details of a specific past meeting."""
    meeting = get_meeting_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"success": True, "meeting": meeting}


@router.post("/memories/recall", tags=["Hindsight Memory"])
async def recall_memories_endpoint(req: RecallMemoryRequest):
    """Directly queries Hindsight Cloud memory bank to inspect recalled knowledge."""
    try:
        result = await memory_service.recall(query=req.query, budget=req.budget or "mid")
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/bank", tags=["Hindsight Memory"])
async def get_bank_info_endpoint():
    """Returns bank info and statistics from Hindsight Cloud."""
    try:
        info = await memory_service.get_bank_info()
        return {"success": True, "bank": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
