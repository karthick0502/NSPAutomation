from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DimensionValue(BaseModel):
    """A single measured dimension when the customer specifies one."""

    label: str = Field(
        description="What is being measured, e.g. internal length, case depth, wheel height"
    )
    value: float | None = Field(
        default=None,
        description="Numeric value if stated; null if only qualitative",
    )
    unit: Literal["mm", "cm", "m", "in", "ft", "unknown"] = "unknown"
    raw_text: str = Field(
        default="",
        description="Verbatim phrase from the email for this dimension",
    )


class AttachmentInsight(BaseModel):
    filename: str | None = None
    kind: Literal["image", "drawing", "document", "unknown"] = "unknown"
    summary: str = Field(
        default="",
        description="What the attachment appears to show, if described or inferable",
    )


class EnquiryExtraction(BaseModel):
    """Structured output for a custom flight-case enquiry email."""

    summary: str = Field(
        description="2-4 sentence executive summary of what the customer wants"
    )
    product_type: str = Field(
        default="",
        description="e.g. rack case, pedal board case, camera case, generic flight case",
    )
    use_case: str = Field(
        default="",
        description="Primary use, environment, or industry context",
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="Bullet-level requirements: foam, wheels, handles, IP rating, etc.",
    )
    dimensions: list[DimensionValue] = Field(
        default_factory=list,
        description="All explicit dimensions; do not invent numbers",
    )
    quantity: int | None = Field(
        default=None,
        description="Number of cases if stated",
    )
    timeline: str | None = Field(
        default=None,
        description="Requested delivery or event date if mentioned",
    )
    contact_hint: str | None = Field(
        default=None,
        description="Name, company, or phone/email fragment if clearly in the body",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Clarifications needed before quoting or designing",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="How complete and unambiguous the email is",
    )
    attachments: list[AttachmentInsight] = Field(
        default_factory=list,
        description="Insights for each attachment mentioned or supplied out-of-band",
    )
