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
    get_map_provider,
    get_nl_provider,
    get_ocr_provider,
    get_vision_provider,
)
from app.providers.mock import MockMapProvider
from app.providers.tencent_map import ProviderError

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
    if (
        not settings.feature_real_ai
        or settings.vision_provider == "mock"
        or not settings.ai_api_key
    ):
        raise ApiError(
            "真实宠物图片分析尚未配置，请直接手填并确认宠物信息",
            code="provider_unavailable",
            status_code=503,
        )
    try:
        provider = get_vision_provider()
    except RuntimeError as exc:
        raise ApiError(
            "真实宠物图片分析尚未接入，当前不会返回模拟识别结果",
            code="provider_unavailable",
            status_code=503,
        ) from exc
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
    settings = get_settings()
    if not settings.feature_real_ai or settings.ocr_provider == "mock" or not settings.ai_api_key:
        raise ApiError(
            "真实规则牌 OCR 尚未配置；请手动录入规则线索或证据",
            code="provider_unavailable",
            status_code=503,
        )
    try:
        provider = get_ocr_provider()
    except RuntimeError as exc:
        raise ApiError(
            "真实规则牌 OCR 尚未接入，当前不会返回模拟文字或规则候选",
            code="provider_unavailable",
            status_code=503,
        ) from exc
    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise ApiError("图片超过 10MB 限制", code="payload_too_large", status_code=413)
    result = get_ai_guard().call("ocr", "extract_text", lambda: provider.extract_text(data))
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
    settings = get_settings()
    if not settings.feature_real_ai or not settings.ai_api_key:
        raise ApiError(
            "真实自然语言查询解析尚未配置；请使用结构化搜索与查询条件",
            code="provider_unavailable",
            status_code=503,
        )
    try:
        provider = get_nl_provider()
    except RuntimeError as exc:
        raise ApiError(
            "真实自然语言查询解析尚未接入，当前不会返回模拟解析结果",
            code="provider_unavailable",
            status_code=503,
        ) from exc
    parsed = get_ai_guard().call(
        "nlq",
        "parse_query",
        lambda: provider.parse_query(body.text, body.lat, body.lng),
    )
    return ParseQueryOut(
        intent=parsed["intent"],
        animal=parsed.get("animal"),
        keywords=parsed["keywords"],
        note="解析仅为查询草稿，准入判定由确定性 evaluator 完成。",
    )


class MapCoordinate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class MapTranslateIn(BaseModel):
    coordinates: list[MapCoordinate] = Field(min_length=1, max_length=50)


class MapNormalizeIn(BaseModel):
    coordinates: list[MapCoordinate] = Field(min_length=1, max_length=50)


@router.get("/map/config")
def map_config() -> dict:
    """Public render configuration for the consumer map.

    The Tencent browser key is intentionally client-visible: Tencent's own
    JavaScript GL API requires that key in the script URL. Deployments must
    restrict this *client* key by approved domains. The server WebService key
    remains private and is never returned here.
    """
    settings = get_settings()
    real_ready = bool(
        settings.feature_real_map
        and settings.map_provider == "tencent"
        and settings.tencent_map_key_client
        and settings.tencent_map_key_server
    )
    if not real_ready:
        return {
            **MockMapProvider().render_config(),
            "real_enabled": False,
            "client_key": None,
            "attribution": None,
            "reason": "real_map_not_configured",
        }

    config = get_map_provider().render_config()
    return {
        **config,
        "center": {"lat": 31.23, "lng": 121.47},
        "zoom": 14,
        "real_enabled": True,
        "client_key": settings.tencent_map_key_client,
        "attribution": "腾讯地图",
        "reason": None,
    }


@router.post("/map/translate")
def translate_map_coordinates(body: MapTranslateIn) -> dict:
    """Translate governed EPSG:4326 points for the configured render provider.

    Converted coordinates are response-only presentation data: PetAccess never
    writes provider coordinates back into Place.location or PlaceGeometry.
    """
    settings = get_settings()
    if not (
        settings.feature_real_map
        and settings.map_provider == "tencent"
        and settings.tencent_map_key_server
    ):
        return {
            "provider": "mock",
            "coordinate_system": "EPSG:4326",
            "coordinates": [point.model_dump() for point in body.coordinates],
        }

    try:
        translated = get_map_provider().translate_coordinates(
            [(point.lat, point.lng) for point in body.coordinates]
        )
    except ProviderError as exc:
        raise ApiError(
            "真实地图坐标转换暂不可用",
            code=f"map_{exc.code}",
            status_code=503,
        ) from exc
    return {
        "provider": "tencent",
        "coordinate_system": "GCJ-02",
        "coordinates": translated,
    }


@router.post("/map/normalize")
def normalize_map_coordinates(body: MapNormalizeIn) -> dict:
    """Normalize interactive render-center coordinates into EPSG:4326.

    The browser provider may render a different coordinate system. Nearby
    queries and persisted PetAccess geometry always remain WGS84.
    """
    settings = get_settings()
    if not (
        settings.feature_real_map
        and settings.map_provider == "tencent"
        and settings.tencent_map_key_server
    ):
        normalized = [point.model_dump() for point in body.coordinates]
        provider = "mock"
    else:
        normalized = get_map_provider().normalize_render_coordinates(
            [(point.lat, point.lng) for point in body.coordinates]
        )
        provider = "tencent"
    return {
        "provider": provider,
        "coordinate_system": "EPSG:4326",
        "coordinates": normalized,
    }
