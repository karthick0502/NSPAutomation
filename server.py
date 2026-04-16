"""
HTTP API for automation tools (n8n, Make, Zapier) to call the same extraction logic.

Run:
  pip install -r requirements.txt
  copy .env.example .env   # add OPENAI_API_KEY
  uvicorn server:app --reload --host 0.0.0.0 --port 8000

POST /extract
  JSON body: { "email_text": "...", "images": [ { "filename": "x.png", "mime_type": "image/png", "base64": "..." } ] }
  Returns: structured JSON (same schema as CLI).
"""

from __future__ import annotations

import base64
import logging
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

_ROOT = Path(__file__).resolve().parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from nsp_automation.llm_client import extract_enquiry
from nsp_automation.logging_config import configure_logging
from nsp_automation.models import EnquiryExtraction

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="NSP Enquiry Extractor", version="1.0.0")


class ImagePayload(BaseModel):
    filename: str | None = None
    mime_type: str = Field(default="image/png", description="e.g. image/png, image/jpeg")
    base64: str


class ExtractRequest(BaseModel):
    email_text: str
    images: list[ImagePayload] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract", response_model=EnquiryExtraction)
def extract(req: ExtractRequest) -> EnquiryExtraction:
    if not req.email_text.strip():
        raise HTTPException(status_code=400, detail="email_text is required")
    n_in = len(req.images) if req.images else 0
    logger.info(
        "POST /extract email_chars=%s inline_images=%s",
        len(req.email_text),
        n_in,
    )
    paths: list[Path] = []
    tmpdir: tempfile.TemporaryDirectory[str] | None = None
    try:
        if req.images:
            tmpdir = tempfile.TemporaryDirectory()
            base = Path(tmpdir.name)
            for i, img in enumerate(req.images):
                try:
                    raw = base64.b64decode(img.base64, validate=True)
                except Exception as exc:  # noqa: BLE001
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid base64 for image index {i}: {exc}",
                    ) from exc
                ext = ".png"
                if img.filename:
                    ext = Path(img.filename).suffix or ext
                elif "jpeg" in img.mime_type or "jpg" in img.mime_type:
                    ext = ".jpg"
                path = base / f"img_{i}{ext}"
                path.write_bytes(raw)
                paths.append(path)
        result = extract_enquiry(req.email_text, image_paths=paths or None)
        logger.info(
            "POST /extract done confidence=%s",
            result.confidence,
        )
        return result
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()
