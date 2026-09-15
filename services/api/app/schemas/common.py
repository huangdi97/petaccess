"""Shared pagination envelope and cross-schema field types."""

from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator

from app.models.enums import MandatoryLevel, normalize_mandatory_level

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


def _normalize_mandatory(value: object) -> object:
    """Map the legacy ``discretionary`` spelling onto its canonical value."""
    return normalize_mandatory_level(value) if isinstance(value, str) else value


#: Normative force (ADR-023). The normalisation runs *before* enum validation so
#: the read path and the write path accept exactly the same vocabulary — a row
#: stored under the legacy spelling round-trips instead of being rejected with a
#: 422. An unknown value still fails enum validation, which is the intent.
NormalizedMandatoryLevel = Annotated[MandatoryLevel, BeforeValidator(_normalize_mandatory)]
