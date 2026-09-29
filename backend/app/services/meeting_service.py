"""Meeting service coordinator.
Orchestrates the end-to-end pipeline:
Audio/Transcript -> Transcription -> Memory Extraction (Gemini) -> Long-Term Memory (Hindsight) -> Brief Preparation.
"""
from typing import Dict, Any, Optional, List
import uuid
import logging
from .transcription_service import transcription_service
from .memory_service import memory_service
from .ai_service import ai_service
from ..db.database import save_meeting

logger = logging.getLogger(__name__)


class MeetingService:
    """Coordinates meeting workflows between speech, memory, and preparation agents."""

    def __init__(self):
        self.transcription = transcription_service
        self.memory = memory_service
        self.ai = ai_service

    async def process_transcript(self, title: str, transcript: str) -> Dict[str, Any]:
        """Processes raw text transcript: extracts memories, retains in Hindsight, saves to SQLite."""
        if not transcript.strip():
            raise ValueError("Transcript content cannot be empty.")

        meeting_title = title.strip() or f"Meeting on {uuid.uuid4().hex[:6]}"
        doc_id = f"meeting_{uuid.uuid4().hex[:8]}"

        # 1. AI Memory Extraction (Gemini)
        logger.info(f"Extracting memories for '{meeting_title}'...")
        extracted_data = await self.ai.extract_memories_from_transcript(transcript)

        summary = extracted_data.get("summary", "")
        retain_statements = extracted_data.get("retain_statements", [])

        # If retain_statements wasn't generated, fallback to facts + decisions
        if not retain_statements:
            facts = extracted_data.get("facts", [])
            decisions = extracted_data.get("decisions", [])
            retain_statements = facts + decisions

        # 2. Retain in Hindsight Cloud
        hindsight_result = {"status": "skipped", "reason": "No retain statements found"}
        if retain_statements:
            logger.info(f"Retaining {len(retain_statements)} statements in Hindsight Cloud...")
            hindsight_result = await self.memory.retain(
                items=retain_statements,
                context=f"meeting:{meeting_title}",
                document_id=doc_id
            )

        # 3. Persist to SQLite Database
        meeting_id = save_meeting(
            title=meeting_title,
            transcript=transcript,
            summary=summary,
            status="completed"
        )

        return {
            "meeting_id": meeting_id,
            "title": meeting_title,
            "document_id": doc_id,
            "summary": summary,
            "extracted_data": extracted_data,
            "retained_count": len(retain_statements),
            "hindsight_result": hindsight_result
        }

    async def process_recording(self, file_path: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes an uploaded audio/video file and then executes full memory processing."""
        # Validate format
        is_valid = await self.transcription.validate_audio_file(file_path)
        if not is_valid:
            raise ValueError(f"Unsupported file format for: {file_path}")

        # 1. Transcribe audio/video
        logger.info(f"Transcribing recording at '{file_path}'...")
        transcription_result = await self.transcription.transcribe_audio(file_path)
        transcript = transcription_result.get("transcript", "")

        meeting_title = title.strip() if title else transcription_result.get("file_name", "Recorded Meeting")

        # 2. Process extracted transcript
        result = await self.process_transcript(title=meeting_title, transcript=transcript)
        result["transcription_metadata"] = {
            "file_name": transcription_result.get("file_name"),
            "size_mb": transcription_result.get("size_mb"),
            "mime_type": transcription_result.get("mime_type")
        }
        return result

    async def prepare_for_meeting(self, agenda: str) -> Dict[str, Any]:
        """Recalls historical memories from Hindsight and generates a personalized meeting brief via Gemini."""
        if not agenda.strip():
            raise ValueError("Meeting agenda or topic is required.")

        # 1. Recall relevant long-term memories from Hindsight Cloud
        logger.info(f"Recalling Hindsight memories for agenda: '{agenda}'...")
        recall_response = await self.memory.recall(query=agenda, budget="mid", max_tokens=4096)
        recalled_memories = recall_response.get("memories", [])

        # 2. Synthesize with Gemini
        logger.info(f"Synthesizing brief using Gemini with {len(recalled_memories)} recalled memories...")
        brief = await self.ai.generate_meeting_brief(agenda=agenda, recalled_memories=recalled_memories)

        return {
            "agenda": agenda,
            "recalled_memories_count": len(recalled_memories),
            "recalled_memories": recalled_memories,
            "brief": brief,
            "hindsight_status": recall_response.get("status")
        }


meeting_service = MeetingService()
