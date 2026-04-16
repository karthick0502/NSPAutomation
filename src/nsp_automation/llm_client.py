from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from nsp_automation.models import EnquiryExtraction
from nsp_automation.prompts import SYSTEM_PROMPT, USER_TEMPLATE

load_dotenv()

logger = logging.getLogger(__name__)


def _mime_for_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    if ext == ".gif":
        return "image/gif"
    return "application/octet-stream"


def _build_user_content(body: str, image_paths: list[Path] | None) -> str | list[dict]:
    text = USER_TEMPLATE.format(body=body)
    if not image_paths:
        return text
    parts: list[dict] = [{"type": "text", "text": text}]
    for p in image_paths:
        raw = p.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        mime = _mime_for_path(p)
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            }
        )
    return parts


def extract_enquiry(
    body: str,
    *,
    image_paths: list[Path] | None = None,
) -> EnquiryExtraction:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY is not set")
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    n_img = len(image_paths) if image_paths else 0
    logger.info(
        "Calling OpenAI: model=%s body_chars=%s vision_images=%s",
        model,
        len(body),
        n_img,
    )
    if image_paths:
        for p in image_paths:
            logger.debug("Vision image: %s (%s bytes)", p, p.stat().st_size)

    client = OpenAI(api_key=api_key)
    user_content = _build_user_content(body, image_paths)

    t0 = time.perf_counter()
    completion = client.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=EnquiryExtraction,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    usage = completion.usage
    if usage is not None:
        logger.info(
            "OpenAI response: id=%s latency_ms=%.0f "
            "prompt_tokens=%s completion_tokens=%s total_tokens=%s",
            completion.id,
            elapsed_ms,
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )
    else:
        logger.info(
            "OpenAI response: id=%s latency_ms=%.0f (usage unavailable)",
            completion.id,
            elapsed_ms,
        )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        fr = completion.choices[0].finish_reason
        logger.error("Model returned no structured output (finish_reason=%s)", fr)
        raise RuntimeError("Model returned no structured output.")
    return parsed
