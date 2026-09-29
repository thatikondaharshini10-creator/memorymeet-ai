"""Transcription service implementation using official Google GenAI SDK and gemini-3.5-transcribe.
Avoids local FFmpeg/CUDA requirements by leveraging hosted multimodal processing.
"""
from typing import Dict, Any, Optional
import os
import mimetypes
import logging
from google import genai
from ..core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Handles audio/video processing and Speech-to-Text transcription via Google GenAI SDK."""

    def __init__(self):
        self.provider = settings.STT_PROVIDER
        self.model = "gemini-3.5-transcribe"
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)

    def get_mime_type(self, file_path: str) -> str:
        """Determines the MIME type of an audio or video file."""
        mime, _ = mimetypes.guess_type(file_path)
        if mime:
            return mime
        
        ext = os.path.splitext(file_path.lower())[1]
        mapping = {
            ".mp3": "audio/mp3",
            ".wav": "audio/wav",
            ".m4a": "audio/m4a",
            ".aac": "audio/aac",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".ogg": "audio/ogg",
        }
        return mapping.get(ext, "audio/mp3")

    async def validate_audio_file(self, file_path: str) -> bool:
        """Checks if the uploaded file is a supported audio/video format."""
        supported_extensions = {".mp3", ".wav", ".m4a", ".aac", ".mp4", ".webm", ".ogg"}
        ext = os.path.splitext(file_path.lower())[1]
        return ext in supported_extensions

    async def transcribe_audio(self, file_path: str) -> Dict[str, Any]:
        """Transcribes an audio or video file using the official Google GenAI SDK."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Recording file not found at: {file_path}")

        mime_type = self.get_mime_type(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        logger.info(f"Uploading '{file_path}' to Google GenAI for transcription using model '{self.model}'...")
        uploaded_file = None
        try:
            # Upload local audio file to Gemini File API
            uploaded_file = self.client.files.upload(file=file_path)
            logger.info(f"File uploaded successfully to GenAI: {uploaded_file.name}")

            # Transcribe with gemini-3.5-transcribe
            response = self.client.models.generate_content(
                model=self.model,
                contents=[uploaded_file]
            )

            # Extract transcription text from response (supporting both response.text and audio_transcription parts)
            transcript_text = ""
            if response.text:
                transcript_text = response.text.strip()
            elif getattr(response, "candidates", None):
                for candidate in response.candidates:
                    if getattr(candidate, "content", None) and getattr(candidate.content, "parts", None):
                        for part in candidate.content.parts:
                            if getattr(part, "audio_transcription", None) and getattr(part.audio_transcription, "text", None):
                                transcript_text += part.audio_transcription.text + " "
                            elif getattr(part, "text", None):
                                transcript_text += part.text + " "
                transcript_text = transcript_text.strip()

            if not transcript_text:
                logger.error("GenAI returned an empty transcription.")
                raise RuntimeError("Gemini returned an empty transcription for the uploaded audio.")

            logger.info(f"Transcription successful ({len(transcript_text)} characters).")
            return {
                "transcript": transcript_text,
                "file_name": os.path.basename(file_path),
                "mime_type": mime_type,
                "size_mb": round(file_size_mb, 2)
            }
        except Exception as e:
            logger.error(f"GenAI audio transcription failed for '{file_path}': {e}", exc_info=True)
            raise RuntimeError(f"Audio transcription failed: {str(e)}") from e
        finally:
            if uploaded_file and hasattr(uploaded_file, "name"):
                try:
                    self.client.files.delete(name=uploaded_file.name)
                    logger.debug(f"Cleaned up remote GenAI file: {uploaded_file.name}")
                except Exception as del_err:
                    logger.warning(f"Could not delete temporary remote GenAI file {uploaded_file.name}: {del_err}")


transcription_service = TranscriptionService()
