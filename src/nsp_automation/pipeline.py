from __future__ import annotations

import json
import logging
from pathlib import Path

from nsp_automation.email_parser import load_email_body, split_headers_optional
from nsp_automation.llm_client import extract_enquiry
from nsp_automation.models import EnquiryExtraction

logger = logging.getLogger(__name__)


def run_pipeline(
    email_path: Path,
    *,
    attachment_paths: list[Path] | None = None,
) -> EnquiryExtraction:
    n_img = len(attachment_paths) if attachment_paths else 0
    logger.info(
        "Pipeline start: email=%s attachment_count=%s",
        email_path,
        n_img,
    )
    body, _subject = load_email_body(email_path)
    body = split_headers_optional(body)
    logger.debug("Email body length after normalisation: %s chars", len(body))
    result = extract_enquiry(body, image_paths=attachment_paths)
    logger.info(
        "Pipeline complete: confidence=%s open_questions=%s",
        result.confidence,
        len(result.open_questions),
    )
    return result


def result_to_json(result: EnquiryExtraction) -> str:
    return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
