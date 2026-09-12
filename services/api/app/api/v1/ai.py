"""AI endpoints (design #21, GOAL Phase 6).

Hard limits enforced by contract:
- vision: species/breed SUGGESTION only → user confirms; never service dog;
  never confirmed weight/height from an image.
- ocr: signage text + structured rule candidates → human review queue.
- nl query: parse into QueryContext DRAFT; final judgement stays with the
  deterministic evaluator.
"""

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.errors import ApiError
from app.core.security import get_current_user
from app.providers.factory import (
    get_ai_guard,
    get_nl_provider,
    get_ocr_provider,
    get_vision_provider,
)
from app.providers.mock import MockMapProvider

router = APIRouter(prefix="/ai", tags=["ai"])


class PetVisionOut(BaseModel):
    species: str
    breed_candidates: list[str]
    confidence: float
    requires_user_confirmation: bool = True
    note: str


@router.post("/pet-vision", response_model=PetVisionOut)
async def classify_pet(
    image: UploadFile = File(...),
    user=Depends(get_current_user),
) -> PetVisionOut:
    settings = get_settings()
    if settings.ai_provider == "mock" and not settings.feature_real_ai:
        provider = get_vision_provider()
    else:
        raise ApiError("真实 vision provider 未配置", code="provider_unavailable", status_code=503)
    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise ApiError("图片超过 10MB 限制", code="payload_too_large", status_code=413)
    suggestion = get_ai_guard().call("vision", "classify_pet", lambda: provider.classify_pet(data))
    return PetVisionOut(
        species=suggestion.species,
        breed_candidates=suggestion.breed_candidates,
        confidence=round(suggestion.confidence, 3),
        note="AI 仅为建议：品种需用户确认；服务犬身份与体重/肩高不可由图片认定。",
    )


class OcrOut(BaseModel):
    text_blocks: list[str]
    rule_candidates: list[dict]
    requires_review: bool = True


@router.post("/ocr-signage", response_model=OcrOut)
async def ocr_signage(
    image: UploadFile = File(...),
    user=Depends(get_current_user),
) -> OcrOut:
    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise ApiError("图片超过 10MB 限制", code="payload_too_large", status_code=413)
    result = get_ai_guard().call(
        "ocr", "extract_text", lambda: get_ocr_provider().extract_text(data)
    )
    return OcrOut(
        text_blocks=result.text_blocks,
        rule_candidates=result.rule_candidates,
        note="OCR 结果仅供审核队列参考，规则需人工结构化后才能生效。",
    )


class ParseQueryIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    lat: float | None = None
    lng: float | None = None


class ParseQueryOut(BaseModel):
    intent: str
    animal: dict | None = None
    keywords: list[str]
    note: str


@router.post("/parse-query", response_model=ParseQueryOut)
def parse_query(
    body: ParseQueryIn,
    user=Depends(get_current_user),
) -> ParseQueryOut:
    """Mock NL parsing: extracts animal + keywords only.

    Real LLM adapter would return the same shape; the deterministic evaluator
    remains the only rule judge (ADR-005).
    """
    parsed = get_ai_guard().call(
        "nlq",
        "parse_query",
        lambda: get_nl_provider().parse_query(body.text, body.lat, body.lng),
    )
    return ParseQueryOut(
        intent=parsed["intent"],
        animal=parsed.get("animal"),
        keywords=parsed["keywords"],
        note="解析仅为查询草稿，准入判定由确定性 evaluator 完成。",
    )


@router.get("/map/config")
def map_config(user=Depends(get_current_user)) -> dict:
    return MockMapProvider().render_config()
