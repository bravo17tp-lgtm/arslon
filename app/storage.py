"""Supabase Storage orqali doimiy fayl (rasm/video) saqlash."""

import logging
import os
import uuid

import httpx

logger = logging.getLogger("sevgi.storage")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BUCKET = os.environ.get("SUPABASE_BUCKET", "media")


def _object_endpoint(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"


def public_url(path: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"


async def upload_bytes(content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """Faylni Supabase Storage'ga yuklaydi va ochiq (public) URL qaytaradi."""
    ext = os.path.splitext(filename)[1] or ""
    object_path = f"{uuid.uuid4().hex}{ext}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": content_type or "application/octet-stream",
        "x-upsert": "true",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(_object_endpoint(object_path), headers=headers, content=content)
        if resp.status_code not in (200, 201):
            logger.error("Supabase yuklashda xato: %s %s", resp.status_code, resp.text)
            raise RuntimeError(f"Fayl yuklanmadi: {resp.status_code}")
    return public_url(object_path)
