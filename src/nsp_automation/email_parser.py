from __future__ import annotations

import email
from email import policy
from pathlib import Path


def load_email_body(path: Path) -> tuple[str, str | None]:
    """
    Load plain text from a .eml file or raw .txt that looks like an email body.
    Returns (body_text, subject_if_found).
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if raw.lstrip().startswith("From:") or "\nSubject:" in raw[:2000]:
        msg = email.message_from_string(raw, policy=policy.default)
        subject = msg.get("Subject")
        body_parts: list[str] = []
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    payload = part.get_content()
                    if isinstance(payload, str):
                        body_parts.append(payload)
        else:
            plain = msg.get_body(preferencelist=("plain",))
            if plain is not None:
                body_parts.append(plain.get_content())
            elif msg.get_content_type() == "text/plain":
                c = msg.get_content()
                if isinstance(c, str):
                    body_parts.append(c)
        return "\n".join(body_parts).strip() or raw.strip(), subject
    return raw.strip(), None


def split_headers_optional(text: str) -> str:
    """If user pasted headers + body, keep the narrative part after a blank line."""
    lines = text.splitlines()
    if len(lines) > 3 and lines[0].startswith("Subject:"):
        for i, line in enumerate(lines):
            if line.strip() == "":
                return "\n".join(lines[i + 1 :]).strip()
    return text
