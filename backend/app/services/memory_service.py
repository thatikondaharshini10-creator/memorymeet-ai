"""Hindsight Long-Term Memory Service implementation.
Connects to Vectorize.io Hindsight Cloud to retain durable meeting facts and recall contextual memory.
"""
from typing import List, Dict, Any, Optional, Union
import logging
import httpx
from ..core.config import settings

logger = logging.getLogger(__name__)


class HindsightMemoryService:
    """Manages long-term agent memory using Hindsight Cloud (Retain, Recall, Bank Stats)."""

    def __init__(self):
        self.endpoint = settings.HINDSIGHT_ENDPOINT.rstrip("/")
        self.bank_id = settings.HINDSIGHT_BANK_ID
        self.api_key = settings.HINDSIGHT_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        """Builds authorization and content headers."""
        if not self.api_key:
            raise ValueError("HINDSIGHT_API_KEY is not configured in environment.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_bank_info(self) -> Dict[str, Any]:
        """Retrieves bank metadata, status, and memory statistics."""
        url = f"{self.endpoint}/v1/default/banks"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                banks = resp.json().get("banks", [])
                target = next((b for b in banks if b.get("bank_id") == self.bank_id), None)
                if target:
                    return {
                        "status": "ready",
                        "bank_id": self.bank_id,
                        "fact_count": target.get("fact_count", 0),
                        "created_at": target.get("created_at"),
                        "updated_at": target.get("updated_at")
                    }
                return {"status": "not_found", "bank_id": self.bank_id}
            return {"status": "error", "code": resp.status_code, "detail": resp.text[:200]}

    async def retain(
        self,
        items: Union[List[str], List[Dict[str, Any]], str],
        context: Optional[str] = "meeting_memory",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingests and structures information into the Hindsight long-term memory bank."""
        url = f"{self.endpoint}/v1/default/banks/{self.bank_id}/memories"
        headers = self._get_headers()

        # Normalize items into Hindsight format
        if isinstance(items, str):
            formatted_items = [{"content": items, "context": context, "document_id": document_id}]
        elif isinstance(items, list):
            formatted_items = []
            for item in items:
                if isinstance(item, str):
                    formatted_items.append({"content": item, "context": context, "document_id": document_id})
                elif isinstance(item, dict):
                    formatted_items.append({
                        "content": item.get("content", str(item)),
                        "context": item.get("context", context),
                        "document_id": item.get("document_id", document_id)
                    })
        else:
            raise ValueError("Items to retain must be a string or list.")

        payload = {
            "items": formatted_items,
            "async": False
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code in (200, 201, 202):
                    data = response.json() if response.text else {}
                    return {
                        "status": "success",
                        "bank_id": self.bank_id,
                        "retained_count": len(formatted_items),
                        "details": data
                    }
                else:
                    logger.error(f"Hindsight retain failed ({response.status_code}): {response.text}")
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": response.text[:300]
                    }
        except Exception as e:
            logger.error(f"Exception during Hindsight retain: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def recall(
        self,
        query: str,
        budget: str = "mid",
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Recalls relevant memories using TEMPR multi-strategy search."""
        url = f"{self.endpoint}/v1/default/banks/{self.bank_id}/memories/recall"
        headers = self._get_headers()

        payload = {
            "query": query,
            "budget": budget,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    return {
                        "status": "success",
                        "bank_id": self.bank_id,
                        "query": query,
                        "count": len(results),
                        "memories": results,
                        "raw": data
                    }
                else:
                    logger.error(f"Hindsight recall failed ({response.status_code}): {response.text}")
                    return {
                        "status": "error",
                        "status_code": response.status_code,
                        "message": response.text[:300],
                        "memories": []
                    }
        except Exception as e:
            logger.error(f"Exception during Hindsight recall: {e}")
            return {
                "status": "error",
                "message": str(e),
                "memories": []
            }


memory_service = HindsightMemoryService()
