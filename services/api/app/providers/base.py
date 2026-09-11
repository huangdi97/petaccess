"""Provider abstractions: AI/Vision/OCR, Map, Storage, Notification (AGENTS.md).

开发环境默认 mock/local；真实 Provider 只在环境变量开启时使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class PetSuggestion:
    """Vision provider suggestion — ALWAYS user-confirmed, never final.

    service_dog is never suggested from an image (design #5.2, #19);
    weight/height from images can never be `confirmed` (design #21).
    """

    species: str
    breed_candidates: list[str]
    confidence: float


@dataclass(frozen=True)
class OcrResult:
    text_blocks: list[str]
    rule_candidates: list[dict]


@runtime_checkable
class VisionProvider(Protocol):
    def classify_pet(self, image_bytes: bytes) -> PetSuggestion: ...


@runtime_checkable
class OCRProvider(Protocol):
    def extract_text(self, image_bytes: bytes) -> OcrResult: ...


@runtime_checkable
class NotificationProvider(Protocol):
    def send(self, user_id: str, channel: str, title: str, body: str) -> dict: ...


@runtime_checkable
class MapProvider(Protocol):
    """Map provider adapter (ADR-008): Tencent first, mock for dev."""

    def search_places(self, keyword: str, lat: float, lng: float, radius_m: int) -> list[dict]: ...

    def reverse_geocode(self, lat: float, lng: float) -> dict: ...

    def render_config(self) -> dict: ...

    def open_navigation(self, lat: float, lng: float, name: str) -> dict: ...
