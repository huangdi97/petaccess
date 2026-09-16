"""Synthetic demo seed (design #46, GOAL #18).

All demo data is fictional. Deterministic UUIDs make the seed repeatable:
running `python -m app.db.seed --demo` resets and re-inserts demo content.

Dev-only guard: refuses to run against a non-development environment.
"""

import argparse
import sys
import uuid
from datetime import UTC, datetime, timedelta

DEMO_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # RFC4122 "URL" ns


def uid(key: str) -> str:
    return str(uuid.uuid5(DEMO_NAMESPACE, f"petaccess-demo:{key}"))


NOW = datetime.now(UTC)
D = timedelta


# ---------------------------------------------------------------- places

DEMO_PLACES: list[dict] = [
    {
        "key": "place_xinghe_cafe",
        "canonical_name": "星河咖啡·测试店",
        "place_type": "cafe",
        "canonical_address": "演示市星河区云杉路 100 号（虚构地址）",
        "lng": 121.4737,
        "lat": 31.2304,
        # Search keys, not identity: the name this place used to carry, and the
        # short form people actually type. A hit on either must say which one
        # matched rather than silently returning a differently-named place.
        "alias_names": ["星河咖啡", "星河咖啡（云杉路旧址）", "Xinghe Coffee"],
    },
    {
        # Deliberate sibling: same brand, different branch. Search for the brand
        # alone must return both, each labelled by branch and address, instead of
        # one ambiguous row.
        # Key kept as `..._yunqi` on purpose: ids derive from it, and renaming a
        # key re-ids a place that already has rules pointed at it.
        "key": "place_xinghe_cafe_yunqi",
        "canonical_name": "星河咖啡·栖霞分店",
        "place_type": "cafe",
        "canonical_address": "演示市云栖区栖霞街 68 号（虚构地址）",
        "lng": 121.4655,
        "lat": 31.2246,
        "parent_place_id_key": "place_xinghe_cafe",
        # Named after its own street, not the district: a "云栖分店" collided
        # with 云栖中心 on the query "云栖" and buried the mall.
        "alias_names": ["星河咖啡", "星河咖啡栖霞店", "Xinghe Coffee Qixia"],
    },
    {
        "key": "place_qinglan_park",
        "canonical_name": "青岚公园·演示",
        "place_type": "park",
        "canonical_address": "演示市青岚区青岚大道 8 号（虚构地址）",
        "lng": 121.4880,
        "lat": 31.2380,
        # The park was renamed; the old name still circulates on local signage.
        "alias_names": ["青岚河滨绿地", "青岚公园"],
    },
    {
        "key": "place_yunqi_mall",
        "canonical_name": "云栖中心·测试商场",
        "place_type": "mall",
        "canonical_address": "演示市云栖区栖霞街 66 号（虚构地址）",
        "lng": 121.4650,
        "lat": 31.2240,
        "alias_names": ["云栖中心", "云栖购物中心", "Yunqi Center"],
    },
    {
        "key": "place_songfeng_community",
        "canonical_name": "松风社区·演示",
        "place_type": "residential_community",
        "canonical_address": "演示市松风区松风路 20 弄（虚构地址）",
        "lng": 121.4950,
        "lat": 31.2180,
        "alias_names": ["松风新村"],
    },
]

PARK_LNG, PARK_LAT = 121.4880, 31.2380


def ring(lng0: float, lat0: float, lng1: float, lat1: float) -> str:
    """Closed WKT polygon ring string."""
    return f"({lng0} {lat0},{lng1} {lat0},{lng1} {lat1},{lng0} {lat1},{lng0} {lat0})"


def poly(lng0: float, lat0: float, lng1: float, lat1: float) -> str:
    return f"POLYGON({ring(lng0, lat0, lng1, lat1)})"


def run_demo_seed() -> dict[str, int]:  # noqa: PLR0915 - linear demo data script
    from sqlalchemy import text

    from app.core.config import get_settings
    from app.db.session import get_session_factory
    from app.models import (
        AccessRule,
        AuditLog,
        DisputeCase,
        ExternalPlaceRef,
        JurisdictionRule,
        ObservationClaim,
        Operator,
        OperatorClaim,
        PetProfile,
        Place,
        PlaceGeometry,
        RuleCondition,
        Source,
        User,
        VerificationEvent,
        WatchSubscription,
        Zone,
    )
    from app.models.enums import (
        AnimalScope,
        Directness,
        DisputeCaseStatus,
        DisputeTargetType,
        GeometryType,
        IndoorOutdoor,
        IssuerVerification,
        JurisdictionLevel,
        JurisdictionReviewStatus,
        MandatoryLevel,
        ObservationDisputeStatus,
        ObservationStaffAction,
        OccurredPrecision,
        OperatorClaimStatus,
        OperatorOrgType,
        PersistencePermission,
        PlaceConfidence,
        RuleAction,
        RuleConditionType,
        RuleEffect,
        RuleOrigin,
        RuleStatus,
        ServiceRole,
        SourceAvailability,
        SourceType,
        SpatialPrecision,
        TemporaryAction,
        UserRole,
        WatchStatus,
        WatchTargetType,
        ZoneType,
    )

    session = get_session_factory()()
    if get_settings().app_env not in ("development", "test", "local"):
        raise RuntimeError("demo seed refuses to run outside development/test environments")
    counts: dict[str, int] = {}

    # --- reset demo tables (dev only; FK order respected) ---
    # v0.5 tables are listed before the entities they reference (source, place,
    # zone, organization). rule_candidate/rule_condition hang off source and
    # place, so they must be cleared before either.
    for table in (
        "audit_log",
        "watch_subscription",
        "dispute_case",
        "verification_event",
        "observation_claim",
        "rule_condition",
        "access_rule",
        "jurisdiction_rule",
        "operator_claim",
        "external_place_ref",
        "place_geometry",
        # --- v0.5 domain tables ---
        "rule_candidate",
        "observation_candidate",
        "evidence_bundle",
        "source_artifact",
        "data_source_job",
        "source_monitor",
        "policy_template_rule",
        "place_policy_binding",
        "policy_template",
        "organization",
        "boundary_preference",
        "boundary_profile",
        "coexistence_policy",
        "freshness_policy",
        "amenity",
        "entrance",
        "access_path",
        "event_policy",
        "data_license",
        "media_object",
        "zone",
        "place",
        "operator",
        "source",
        "pet_profile",
        '"user"',
    ):
        # `table` iterates a literal declared a few lines above; nothing from
        # outside this function reaches the string, so there is no injection
        # path. Marked rather than silenced by config so the marker stays
        # attached to the one line that has to justify itself.
        session.execute(text(f"DELETE FROM {table}"))  # nosec B608

    # --- users ---
    from app.core.security import hash_password

    admin_password = hash_password("admin12345")  # dev-only documented credential
    users = {
        "admin": User(
            id=uid("user_admin"),
            display_name="演示管理员",
            email="admin@demo-petaccess.com",
            password_hash=admin_password,
            role=UserRole.ADMIN,
        ),
        "operator": User(
            id=uid("user_operator"),
            display_name="云栖商业管理（演示）",
            email="operator@demo.local",
            role=UserRole.OPERATOR,
        ),
        "alice": User(id=uid("user_alice"), display_name="演示用户 A"),
        "bob": User(id=uid("user_bob"), display_name="演示用户 B"),
    }
    session.add_all(users.values())
    session.commit()

    # --- pets ---
    pets = [
        PetProfile(
            id=uid("pet_doudou"),
            user_id=users["alice"].id,
            display_name="豆豆",
            species="dog",
            breed_text="柴犬",
            weight_kg=9.5,
            shoulder_height_cm=38.0,
        ),
        PetProfile(
            id=uid("pet_axin"),
            user_id=users["bob"].id,
            display_name="阿信",
            species="dog",
            breed_text="拉布拉多（服务犬，用户声明）",
            service_role=ServiceRole.WORKING,
            weight_kg=28.0,
        ),
        PetProfile(
            id=uid("pet_mimi"),
            user_id=users["alice"].id,
            display_name="咪咪",
            species="cat",
        ),
    ]
    session.add_all(pets)

    # --- operators ---
    op_yunqi = Operator(
        id=uid("operator_yunqi"),
        name="云栖商业管理有限公司（演示）",
        org_type=OperatorOrgType.COMPANY,
        contact_email="mall@yunqi-demo.example",
        verified=True,
        verification_method="official_domain_email",
    )
    op_songfeng = Operator(
        id=uid("operator_songfeng"),
        name="松风物业服务中心（演示）",
        org_type=OperatorOrgType.PROPERTY_MGMT,
        contact_email="property@songfeng-demo.example",
        verified=True,
        verification_method="property_certificate",
    )
    session.add_all([op_yunqi, op_songfeng])

    # --- sources ---
    src_signage_cafe = Source(
        id=uid("src_signage_cafe"),
        source_type=SourceType.ONSITE_SIGNAGE,
        issuer="星河咖啡门店告示（虚构）",
        issuer_verification=IssuerVerification.UNVERIFIED,
        collected_at=NOW - D(days=16),
        observed_at=NOW - D(days=16),
        source_availability=SourceAvailability.AVAILABLE_OFFLINE,
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.PRECISE,
    )
    src_park_gov = Source(
        id=uid("src_park_gov"),
        source_type=SourceType.GOVERNMENT_SERVICE,
        issuer="演示市绿化市容管理局（虚构）",
        issuer_verification=IssuerVerification.VERIFIED,
        source_url="https://demo-gov.example/park-pet-policy",
        collected_at=NOW - D(days=120),
        published_at=NOW - D(days=200),
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.PRECISE,
    )
    src_park_signage = Source(
        id=uid("src_park_signage"),
        source_type=SourceType.ONSITE_SIGNAGE,
        issuer="青岚公园入口告示（用户上传，虚构）",
        issuer_verification=IssuerVerification.UNVERIFIED,
        collected_at=NOW - D(days=30),
        observed_at=NOW - D(days=30),
        source_availability=SourceAvailability.AVAILABLE_OFFLINE,
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.PRECISE,
    )
    src_mall_policy = Source(
        id=uid("src_mall_policy"),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY,
        issuer="云栖商业管理有限公司（演示）",
        issuer_verification=IssuerVerification.VERIFIED,
        source_url="https://yunqi-demo.example/pet-policy",
        collected_at=NOW - D(days=45),
        published_at=NOW - D(days=45),
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.PRECISE,
    )
    src_mall_policy_old = Source(
        id=uid("src_mall_policy_old"),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY,
        issuer="云栖商业管理有限公司（演示，旧版）",
        issuer_verification=IssuerVerification.VERIFIED,
        collected_at=NOW - D(days=400),
        published_at=NOW - D(days=400),
        source_availability=SourceAvailability.ARCHIVED,
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.PRECISE,
    )
    src_community_property = Source(
        id=uid("src_community_property"),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY,
        issuer="松风物业服务中心（演示）",
        issuer_verification=IssuerVerification.VERIFIED,
        collected_at=NOW - D(days=60),
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.APPROXIMATE,
    )
    src_city_regulation = Source(
        id=uid("src_city_regulation"),
        source_type=SourceType.STATUTE_OR_REGULATION,
        issuer="演示市人民政府（虚构）",
        issuer_verification=IssuerVerification.VERIFIED,
        source_url="https://demo-gov.example/dog-regulation",
        collected_at=NOW - D(days=300),
        published_at=NOW - D(days=1000),
        directness=Directness.DIRECT,
        spatial_precision=SpatialPrecision.UNKNOWN,
    )
    src_user_bob = Source(
        id=uid("src_user_bob"),
        source_type=SourceType.ORDINARY_USER,
        issuer="演示用户 B",
        issuer_verification=IssuerVerification.UNVERIFIED,
        collected_at=NOW - D(days=2),
        observed_at=NOW - D(days=2),
        directness=Directness.SECONDARY,
        spatial_precision=SpatialPrecision.APPROXIMATE,
    )
    session.add_all(
        [
            src_signage_cafe,
            src_park_gov,
            src_park_signage,
            src_mall_policy,
            src_mall_policy_old,
            src_community_property,
            src_city_regulation,
            src_user_bob,
        ]
    )
    session.commit()

    # --- places + geometry ---
    places: dict[str, Place] = {}
    for spec in DEMO_PLACES:
        p = Place(
            id=uid(spec["key"]),
            canonical_name=spec["canonical_name"],
            place_type=spec["place_type"],
            canonical_address=spec["canonical_address"],
            location=f"POINT({spec['lng']} {spec['lat']})",
            alias_names=list(spec.get("alias_names", [])),
        )
        places[spec["key"]] = p
    # Branch linkage is a second pass because a sibling may be declared before
    # the place it hangs off.
    for spec in DEMO_PLACES:
        parent_key = spec.get("parent_place_id_key")
        if parent_key:
            places[spec["key"]].parent_place_id = places[parent_key].id
    places["place_yunqi_mall"].operator_id = op_yunqi.id
    places["place_songfeng_community"].operator_id = op_songfeng.id
    session.add_all(places.values())
    session.flush()

    session.add_all(
        [
            ExternalPlaceRef(
                place_id=places["place_xinghe_cafe"].id,
                provider="mock",
                external_id="mock-poi-10001",
                persistence_permission=PersistencePermission.RESTRICTED,
                last_resolved_at=NOW,
            ),
            ExternalPlaceRef(
                place_id=places["place_qinglan_park"].id,
                provider="mock",
                external_id="mock-poi-10002",
                persistence_permission=PersistencePermission.RESTRICTED,
                last_resolved_at=NOW,
            ),
        ]
    )

    # --- zones ---
    z_cafe_indoor = Zone(
        id=uid("zone_cafe_indoor"),
        place_id=places["place_xinghe_cafe"].id,
        name="室内堂食区",
        zone_type=ZoneType.DINING_AREA,
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_cafe_outdoor = Zone(
        id=uid("zone_cafe_outdoor"),
        place_id=places["place_xinghe_cafe"].id,
        name="户外座位区",
        zone_type=ZoneType.AREA,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_park_lawn_a = Zone(
        id=uid("zone_park_lawn_a"),
        place_id=places["place_qinglan_park"].id,
        name="A 草坪",
        zone_type=ZoneType.LAWN,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_park_children = Zone(
        id=uid("zone_park_children"),
        place_id=places["place_qinglan_park"].id,
        name="儿童活动区",
        zone_type=ZoneType.CHILDREN_AREA,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_park_pet = Zone(
        id=uid("zone_park_pet"),
        place_id=places["place_qinglan_park"].id,
        name="宠物活动区",
        zone_type=ZoneType.PET_AREA,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_park_night = Zone(
        id=uid("zone_park_night"),
        place_id=places["place_qinglan_park"].id,
        name="夜间草坪",
        zone_type=ZoneType.LAWN,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_mall_1f = Zone(
        id=uid("zone_mall_1f"),
        place_id=places["place_yunqi_mall"].id,
        name="1F 公共区",
        zone_type=ZoneType.FLOOR,
        floor_ref="1F",
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_mall_2f = Zone(
        id=uid("zone_mall_2f"),
        place_id=places["place_yunqi_mall"].id,
        name="2F 公共区",
        zone_type=ZoneType.FLOOR,
        floor_ref="2F",
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_mall_3f = Zone(
        id=uid("zone_mall_3f"),
        place_id=places["place_yunqi_mall"].id,
        name="3F 宠物区",
        zone_type=ZoneType.PET_AREA,
        floor_ref="3F",
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_mall_4f = Zone(
        id=uid("zone_mall_4f"),
        place_id=places["place_yunqi_mall"].id,
        name="4F 餐饮层",
        zone_type=ZoneType.DINING_AREA,
        floor_ref="4F",
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_mall_b1 = Zone(
        id=uid("zone_mall_b1"),
        place_id=places["place_yunqi_mall"].id,
        name="B1 超市",
        zone_type=ZoneType.SUPERMARKET,
        floor_ref="B1",
        indoor_outdoor=IndoorOutdoor.INDOOR,
    )
    z_cm_road = Zone(
        id=uid("zone_cm_road"),
        place_id=places["place_songfeng_community"].id,
        name="公共道路",
        zone_type=ZoneType.ROAD,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_cm_children = Zone(
        id=uid("zone_cm_children"),
        place_id=places["place_songfeng_community"].id,
        name="儿童活动区",
        zone_type=ZoneType.CHILDREN_AREA,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_cm_lawn = Zone(
        id=uid("zone_cm_lawn"),
        place_id=places["place_songfeng_community"].id,
        name="中心草坪",
        zone_type=ZoneType.LAWN,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    z_cm_pet = Zone(
        id=uid("zone_cm_pet"),
        place_id=places["place_songfeng_community"].id,
        name="宠物活动区",
        zone_type=ZoneType.PET_AREA,
        indoor_outdoor=IndoorOutdoor.OUTDOOR,
    )
    all_zones = [
        z_cafe_indoor,
        z_cafe_outdoor,
        z_park_lawn_a,
        z_park_children,
        z_park_pet,
        z_park_night,
        z_mall_1f,
        z_mall_2f,
        z_mall_3f,
        z_mall_4f,
        z_mall_b1,
        z_cm_road,
        z_cm_children,
        z_cm_lawn,
        z_cm_pet,
    ]
    session.add_all(all_zones)
    session.flush()

    # --- geometries: place points already denormalized; zone polygons below ---
    geometries = [
        PlaceGeometry(
            place_id=places["place_qinglan_park"].id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(PARK_LNG - 0.004, PARK_LAT - 0.003, PARK_LNG + 0.004, PARK_LAT + 0.003),
            source_id=src_park_gov.id,
            precision=SpatialPrecision.APPROXIMATE,
        ),
        PlaceGeometry(
            zone_id=z_park_lawn_a.id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(PARK_LNG - 0.0035, PARK_LAT - 0.0025, PARK_LNG - 0.0005, PARK_LAT + 0.0005),
            source_id=src_park_gov.id,
            precision=SpatialPrecision.APPROXIMATE,
        ),
        PlaceGeometry(
            zone_id=z_park_children.id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(PARK_LNG + 0.0010, PARK_LAT - 0.0025, PARK_LNG + 0.0035, PARK_LAT + 0.0000),
            source_id=src_park_gov.id,
            precision=SpatialPrecision.APPROXIMATE,
        ),
        PlaceGeometry(
            zone_id=z_park_pet.id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(PARK_LNG - 0.0020, PARK_LAT + 0.0010, PARK_LNG + 0.0025, PARK_LAT + 0.0028),
            source_id=src_park_gov.id,
            precision=SpatialPrecision.APPROXIMATE,
        ),
        PlaceGeometry(
            zone_id=z_cafe_outdoor.id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(121.4740, 31.2300, 121.4748, 31.2308),
            source_id=src_signage_cafe.id,
            precision=SpatialPrecision.PRECISE,
        ),
        PlaceGeometry(
            zone_id=z_cm_pet.id,
            geometry_type=GeometryType.POLYGON,
            geom=poly(121.4955, 31.2185, 121.4975, 31.2195),
            source_id=src_community_property.id,
            precision=SpatialPrecision.APPROXIMATE,
        ),
    ]
    session.add_all(geometries)
    session.flush()

    def rule(
        key: str,
        *,
        zone: Zone | None,
        place: Place | None,
        scope: AnimalScope,
        action: RuleAction,
        effect: RuleEffect,
        source: Source,
        origin: RuleOrigin,
        status: RuleStatus = RuleStatus.CURRENT,
        effective_from: datetime | None = None,
        effective_to: datetime | None = None,
        recorded_at: datetime | None = None,
        last_verified_at: datetime | None = None,
        review_due_at: datetime | None = None,
        supersedes: str | None = None,
        note: str | None = None,
    ) -> AccessRule:
        return AccessRule(
            id=uid(key),
            place_id=place.id if place else None,
            zone_id=zone.id if zone else None,
            animal_scope=scope,
            action=action,
            effect=effect,
            source_id=source.id,
            rule_origin=origin,
            status=status,
            effective_from=effective_from,
            effective_to=effective_to,
            recorded_at=recorded_at or NOW - D(days=16),
            last_verified_at=last_verified_at,
            review_due_at=review_due_at,
            supersedes_rule_id=supersedes,
            note=note,
        )

    def cond(key: str, rule_: AccessRule, ctype: RuleConditionType, **values) -> RuleCondition:
        return RuleCondition(id=uid(key), rule_id=rule_.id, condition_type=ctype, **values)

    # --- rules: 星河咖啡 ---
    r_cafe_in = rule(
        "rule_cafe_indoor_prohibit",
        zone=z_cafe_indoor,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.PROHIBITED,
        source=src_signage_cafe,
        origin=RuleOrigin.ONSITE_SIGNAGE,
        last_verified_at=NOW - D(days=16),
        review_due_at=NOW + D(days=75),
    )
    r_cafe_out = rule(
        "rule_cafe_outdoor_leash",
        zone=z_cafe_outdoor,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.CONDITIONAL,
        source=src_signage_cafe,
        origin=RuleOrigin.ONSITE_SIGNAGE,
        last_verified_at=NOW - D(days=16),
        review_due_at=NOW + D(days=75),
    )
    r_cafe_out_leash = cond(
        "rule_cafe_outdoor_leash_cond",
        r_cafe_out,
        RuleConditionType.LEASH_REQUIRED,
        value_flag=True,
    )
    r_cafe_sd = rule(
        "rule_cafe_service_dog",
        place=places["place_xinghe_cafe"],
        zone=None,
        scope=AnimalScope.SERVICE_DOG,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_signage_cafe,
        origin=RuleOrigin.ONSITE_SIGNAGE,
        last_verified_at=NOW - D(days=16),
    )
    # stale superseded rule kept for history (design #40)
    r_cafe_out_old = rule(
        "rule_cafe_outdoor_old",
        zone=z_cafe_outdoor,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_signage_cafe,
        origin=RuleOrigin.ONSITE_SIGNAGE,
        status=RuleStatus.SUPERSEDED,
        effective_from=NOW - D(days=400),
        effective_to=NOW - D(days=16),
        recorded_at=NOW - D(days=400),
        supersedes=None,
        note="旧版：户外曾无条件允许（已废止，用于版本历史演示）",
    )
    session.add_all([r_cafe_in, r_cafe_out, r_cafe_sd, r_cafe_out_old, r_cafe_out_leash])

    # --- rules: 青岚公园 ---
    r_lawn_a = rule(
        "rule_park_lawn_leash",
        zone=z_park_lawn_a,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.WALK,
        effect=RuleEffect.CONDITIONAL,
        source=src_park_gov,
        origin=RuleOrigin.OFFICIAL_REGULATION,
        recorded_at=NOW - D(days=120),
        last_verified_at=NOW - D(days=20),
        review_due_at=NOW + D(days=70),
    )
    r_lawn_a_leash = cond(
        "rule_park_lawn_leash_cond", r_lawn_a, RuleConditionType.LEASH_REQUIRED, value_flag=True
    )
    r_children = rule(
        "rule_park_children_prohibit",
        zone=z_park_children,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.PROHIBITED,
        source=src_park_gov,
        origin=RuleOrigin.OFFICIAL_REGULATION,
        recorded_at=NOW - D(days=120),
        last_verified_at=NOW - D(days=20),
    )
    r_pet_zone = rule(
        "rule_park_pet_zone",
        zone=z_park_pet,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.OFF_LEASH,
        effect=RuleEffect.ALLOWED,
        source=src_park_gov,
        origin=RuleOrigin.OFFICIAL_REGULATION,
        recorded_at=NOW - D(days=120),
        last_verified_at=NOW - D(days=20),
    )
    r_night = rule(
        "rule_park_night_window",
        zone=z_park_night,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.CONDITIONAL,
        source=src_park_gov,
        origin=RuleOrigin.OFFICIAL_REGULATION,
        recorded_at=NOW - D(days=120),
    )
    r_night_window = cond(
        "rule_park_night_window_cond",
        r_night,
        RuleConditionType.TIME_WINDOWS,
        value_json=[{"days": [0, 1, 2, 3, 4, 5, 6], "start": "21:00", "end": "23:30"}],
    )
    r_park_sd = rule(
        "rule_park_service_dog",
        place=places["place_qinglan_park"],
        zone=None,
        scope=AnimalScope.SERVICE_DOG,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_park_gov,
        origin=RuleOrigin.OFFICIAL_REGULATION,
        recorded_at=NOW - D(days=120),
    )
    # CONFLICT demo: community-contributed signage contradicts the government rule on A 草坪
    r_lawn_a_signage = rule(
        "rule_park_lawn_signage_conflict",
        zone=z_park_lawn_a,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.WALK,
        effect=RuleEffect.PROHIBITED,
        source=src_park_signage,
        origin=RuleOrigin.ONSITE_SIGNAGE,
        recorded_at=NOW - D(days=30),
    )
    session.add_all(
        [
            r_lawn_a,
            r_lawn_a_leash,
            r_children,
            r_pet_zone,
            r_night,
            r_night_window,
            r_park_sd,
            r_lawn_a_signage,
        ]
    )

    # --- rules: 云栖中心（商场）---
    mall_entities: list[AccessRule | RuleCondition] = []
    for f in ("1f", "2f"):
        zone = {"1f": z_mall_1f, "2f": z_mall_2f}[f]
        r = rule(
            f"rule_mall_{f}_carrier",
            zone=zone,
            place=None,
            scope=AnimalScope.ORDINARY_PET,
            action=RuleAction.ENTER,
            effect=RuleEffect.CONDITIONAL,
            source=src_mall_policy,
            origin=RuleOrigin.OPERATOR_DECLARED,
            recorded_at=NOW - D(days=45),
            last_verified_at=NOW - D(days=45),
            review_due_at=NOW + D(days=140),
        )
        mall_entities.append(r)
        mall_entities.append(
            cond(
                f"rule_mall_{f}_carrier_c1", r, RuleConditionType.CARRIER_REQUIRED, value_flag=True
            )
        )
        mall_entities.append(
            cond(
                f"rule_mall_{f}_carrier_c2", r, RuleConditionType.STROLLER_REQUIRED, value_flag=True
            )
        )
    r_mall_petzone = rule(
        "rule_mall_3f_petzone",
        zone=z_mall_3f,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_mall_policy,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=45),
        last_verified_at=NOW - D(days=45),
    )
    r_mall_b1 = rule(
        "rule_mall_b1_prohibit",
        zone=z_mall_b1,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.PROHIBITED,
        source=src_mall_policy,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=45),
    )
    r_mall_4f_old = rule(
        "rule_mall_4f_old",
        zone=z_mall_4f,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_mall_policy_old,
        origin=RuleOrigin.OPERATOR_DECLARED,
        status=RuleStatus.SUPERSEDED,
        recorded_at=NOW - D(days=400),
        effective_from=NOW - D(days=400),
        effective_to=NOW - D(days=45),
        note="旧版：4F 曾允许（已废止）",
    )
    r_mall_4f_new = rule(
        "rule_mall_4f_new",
        zone=z_mall_4f,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.ENTER,
        effect=RuleEffect.PROHIBITED,
        source=src_mall_policy,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=45),
        last_verified_at=NOW - D(days=45),
        supersedes=r_mall_4f_old.id,
    )
    r_mall_elevator = rule(
        "rule_mall_elevator",
        place=places["place_yunqi_mall"],
        zone=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.RIDE_ELEVATOR,
        effect=RuleEffect.CONDITIONAL,
        source=src_mall_policy,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=45),
    )
    r_mall_elev_cond = cond(
        "rule_mall_elevator_cond",
        r_mall_elevator,
        RuleConditionType.DESIGNATED_ELEVATOR,
        value_text="2号宠物梯",
    )
    r_mall_entrance = cond(
        "rule_mall_entrance_cond",
        r_mall_elevator,
        RuleConditionType.DESIGNATED_ENTRANCE,
        value_text="南门宠物通道",
    )
    r_mall_sd = rule(
        "rule_mall_service_dog",
        place=places["place_yunqi_mall"],
        zone=None,
        scope=AnimalScope.SERVICE_DOG,
        action=RuleAction.ENTER,
        effect=RuleEffect.ALLOWED,
        source=src_mall_policy,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=45),
    )
    session.add_all(
        [
            *mall_entities,
            r_mall_petzone,
            r_mall_b1,
            r_mall_4f_old,
            r_mall_4f_new,
            r_mall_elevator,
            r_mall_elev_cond,
            r_mall_entrance,
            r_mall_sd,
        ]
    )

    # --- rules: 松风社区 ---
    r_cm_road = rule(
        "rule_cm_road_leash",
        zone=z_cm_road,
        place=None,
        scope=AnimalScope.DOG,
        action=RuleAction.PASS_THROUGH,
        effect=RuleEffect.CONDITIONAL,
        source=src_community_property,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=60),
        last_verified_at=NOW - D(days=60),
    )
    r_cm_road_cond = cond(
        "rule_cm_road_leash_cond", r_cm_road, RuleConditionType.LEASH_REQUIRED, value_flag=True
    )
    r_cm_children = rule(
        "rule_cm_children_prohibit",
        zone=z_cm_children,
        place=None,
        scope=AnimalScope.DOG,
        action=RuleAction.ENTER,
        effect=RuleEffect.PROHIBITED,
        source=src_community_property,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=60),
    )
    r_cm_pet = rule(
        "rule_cm_pet_area",
        zone=z_cm_pet,
        place=None,
        scope=AnimalScope.ORDINARY_PET,
        action=RuleAction.OFF_LEASH,
        effect=RuleEffect.ALLOWED,
        source=src_community_property,
        origin=RuleOrigin.OPERATOR_DECLARED,
        recorded_at=NOW - D(days=60),
    )
    # 中心草坪：故意无规则 → evaluator 返回 UNKNOWN（GOAL #18 演示矩阵）
    session.add_all([r_cm_road, r_cm_road_cond, r_cm_children, r_cm_pet])

    # --- jurisdiction regulations (three-way 'no rule' split, design #18) ---
    regs = [
        JurisdictionRule(
            id=uid("reg_city_leash"),
            jurisdiction_level=JurisdictionLevel.MUNICIPAL,
            jurisdiction_id="demo-city",
            authority="演示市城市管理行政执法局（虚构）",
            instrument_type="regulation",
            document_name="演示市养犬管理条例（虚构）",
            clause_ref="第二十二条",
            clause_text_ref="https://demo-gov.example/dog-regulation#art22",
            animal_scope=AnimalScope.DOG,
            venue_scope="public_place",
            action=RuleAction.WALK,
            effect=RuleEffect.CONDITIONAL,
            conditions=[{"condition_type": "leash_required", "value_flag": True}],
            mandatory_level=MandatoryLevel.MANDATORY,
            effective_from=NOW - D(days=1000),
            source_id=src_city_regulation.id,
            status="current",
            review_status=JurisdictionReviewStatus.REVIEWED_ACTIVE,
            reviewed_at=NOW - D(days=90),
            reviewed_by=uid("user_admin"),
        ),
        JurisdictionRule(
            id="reg_city_dining",
            jurisdiction_level=JurisdictionLevel.MUNICIPAL,
            jurisdiction_id="demo-city",
            authority="演示市市场监督管理局（虚构）",
            instrument_type="regulation",
            document_name="演示市食品安全管理条例（虚构）",
            clause_ref="第十七条",
            animal_scope=AnimalScope.ORDINARY_PET,
            venue_scope="food_service",
            action=RuleAction.ENTER,
            effect=RuleEffect.PROHIBITED,
            conditions=None,
            mandatory_level=MandatoryLevel.MANDATORY,
            effective_from=NOW - D(days=800),
            source_id=src_city_regulation.id,
            status="current",
            review_status=JurisdictionReviewStatus.REVIEWED_ACTIVE,
            reviewed_at=NOW - D(days=90),
        ),
        JurisdictionRule(
            id="reg_city_pet_cafe",
            jurisdiction_level=JurisdictionLevel.DISTRICT,
            jurisdiction_id="demo-district-xinghe",
            authority="星河区相关部门（虚构）",
            instrument_type="notice",
            document_name="星河区宠物友好商业试点通知（虚构）",
            animal_scope=AnimalScope.ORDINARY_PET,
            venue_scope="pet_friendly_business",
            action=None,
            effect=None,
            conditions=None,
            mandatory_level=MandatoryLevel.OPERATOR_DISCRETION,
            source_id=src_city_regulation.id,
            status="current",
            review_status=JurisdictionReviewStatus.EXPLICIT_OPERATOR_DISCRETION,
            reviewed_at=NOW - D(days=80),
        ),
        JurisdictionRule(
            id="reg_city_greenway",
            jurisdiction_level=JurisdictionLevel.MUNICIPAL,
            jurisdiction_id="demo-city",
            authority="演示市绿化市容管理局（虚构）",
            instrument_type="regulation",
            document_name="演示市绿道管理办法（虚构）",
            animal_scope=AnimalScope.ORDINARY_PET,
            venue_scope="greenway",
            action=None,
            effect=None,
            conditions=None,
            mandatory_level=MandatoryLevel.MANDATORY,
            source_id=src_city_regulation.id,
            status="current",
            review_status=JurisdictionReviewStatus.NOT_REVIEWED,
        ),
    ]
    session.add_all(regs)

    # --- operator claims: 云栖中心 claimed & approved ---
    claim_yunqi = OperatorClaim(
        id=uid("claim_yunqi"),
        place_id=places["place_yunqi_mall"].id,
        operator_id=op_yunqi.id,
        claimant_user_id=users["operator"].id,
        status=OperatorClaimStatus.APPROVED,
        verification_method="official_domain_email",
        evidence_refs={"email_domain": "yunqi-demo.example", "docs": ["business_license_mock"]},
        reviewed_by=users["admin"].id,
        reviewed_at=NOW - D(days=50),
    )
    # pending claim on 松风社区 for admin queue demo
    claim_songfeng_pending = OperatorClaim(
        id=uid("claim_songfeng_pending"),
        place_id=places["place_songfeng_community"].id,
        operator_id=op_songfeng.id,
        claimant_user_id=users["operator"].id,
        status=OperatorClaimStatus.SUBMITTED,
        verification_method="property_certificate",
        evidence_refs={"docs": ["property_certificate_mock"]},
    )
    session.add_all([claim_yunqi, claim_songfeng_pending])

    # --- observations (parallel facts; some contradict rules, design #46) ---
    obs_1 = ObservationClaim(
        id=uid("obs_cafe_outdoor"),
        place_id=places["place_xinghe_cafe"].id,
        zone_id=z_cafe_outdoor.id,
        user_id=users["alice"].id,
        occurred_at=NOW - D(days=4),
        occurred_precision=OccurredPrecision.SAME_DAY,
        reported_at=NOW - D(days=4),
        animal_scope=AnimalScope.DOG,
        observed_action=RuleAction.ENTER,
        staff_action=ObservationStaffAction.NO_INTERACTION_OBSERVED,
        place_confidence=PlaceConfidence.CONFIRMED_ON_SITE,
        note="用户报告：携犬进入户外区域，店员未干预（观察，不构成规则）",
        proximity_verified=True,
        distance_bucket="<100m",
        accuracy_bucket="10-50m",
        proximity_verified_at=NOW - D(days=4),
    )
    # observation contradicting indoor prohibition — stays separate from rule, has open dispute
    obs_2 = ObservationClaim(
        id=uid("obs_cafe_indoor_conflict"),
        place_id=places["place_xinghe_cafe"].id,
        zone_id=z_cafe_indoor.id,
        user_id=users["bob"].id,
        occurred_at=NOW - D(days=6),
        occurred_precision=OccurredPrecision.SAME_DAY,
        reported_at=NOW - D(days=6),
        animal_scope=AnimalScope.DOG,
        observed_action=RuleAction.ENTER,
        staff_action=ObservationStaffAction.EXPLICITLY_ALLOWED,
        place_confidence=PlaceConfidence.MEDIUM,
        note="用户报告：看到有顾客携犬进入室内（与现行规则不一致，双方事实并存）",
        dispute_status=ObservationDisputeStatus.UNDER_REVIEW,
    )
    obs_3 = ObservationClaim(
        id=uid("obs_park_petzone"),
        place_id=places["place_qinglan_park"].id,
        zone_id=z_park_pet.id,
        user_id=users["alice"].id,
        occurred_at=NOW - D(days=10),
        occurred_precision=OccurredPrecision.SAME_WEEK,
        reported_at=NOW - D(days=10),
        animal_scope=AnimalScope.DOG,
        observed_action=RuleAction.OFF_LEASH,
        staff_action=ObservationStaffAction.NO_INTERACTION_OBSERVED,
        place_confidence=PlaceConfidence.CONFIRMED_ON_SITE,
        note="宠物活动区内有犬只松绳玩耍",
    )
    session.add_all([obs_1, obs_2, obs_3])
    session.flush()

    # --- verification events ---
    ver_1 = VerificationEvent(
        id=uid("ver_cafe_signage"),
        place_id=places["place_xinghe_cafe"].id,
        rule_id=r_cafe_in.id,
        user_id=users["alice"].id,
        event_type="rule_confirmed",
        result="still_valid",
        note="现场核验：门口告示仍有效",
        proximity_verified=True,
        distance_bucket="<100m",
        accuracy_bucket="10-50m",
        occurred_at=NOW - D(days=16),
    )
    ver_2 = VerificationEvent(
        id=uid("ver_mall_policy"),
        place_id=places["place_yunqi_mall"].id,
        rule_id=r_mall_b1.id,
        user_id=users["operator"].id,
        event_type="field_check",
        result="still_valid",
        note="管理方自查：B1 超市仍禁止普通宠物",
        proximity_verified=True,
        distance_bucket="<50m",
        accuracy_bucket="5-20m",
        occurred_at=NOW - D(days=45),
    )
    session.add_all([ver_1, ver_2])

    # --- dispute: operator disputes the contradicting observation ---
    dispute_1 = DisputeCase(
        id=uid("dispute_cafe_indoor_obs"),
        target_type=DisputeTargetType.OBSERVATION_CLAIM,
        target_id=obs_2.id,
        claimant_user_id=users["operator"].id,
        reason_code="observation_inaccurate",
        notice_text="管理方声明：店内监控时段未见该描述场景，请求复核该观察记录。",
        evidence_refs=[{"type": "operator_statement", "ref": "yunqi-cafe-statement-001"}],
        temporary_action=TemporaryAction.MARK_DISPUTED,
        status=DisputeCaseStatus.UNDER_REVIEW,
        counter_statement="提交人坚持现场所见，愿提供补充照片。",
        counter_party_user_id=users["bob"].id,
    )
    session.add(dispute_1)

    # --- watch subscription demo ---
    watch_1 = WatchSubscription(
        id=uid("watch_alice_park"),
        user_id=users["alice"].id,
        target_type=WatchTargetType.PLACE,
        target_id=places["place_qinglan_park"].id,
        channels=["in_app"],
        status=WatchStatus.ACTIVE,
    )
    session.add(watch_1)

    # --- v0.5 demo data (NEXT_GOAL Track B) ---
    from app.models.v05 import (
        AccessPath,
        Amenity,
        BoundaryPreference,
        BoundaryProfile,
        CoexistencePolicy,
        DataLicense,
        Entrance,
        EventPolicy,
        FreshnessPolicy,
        Organization,
        PlacePolicyBinding,
        PolicyTemplate,
        PolicyTemplateRule,
        SourceMonitor,
    )

    org_yunqi = Organization(
        id=uid("org_yunqi"),
        name="云栖集团（演示）",
        kind="brand",
        contact_email="group@yunqi-demo.example",
    )
    template_mall = PolicyTemplate(
        id=uid("template_mall"),
        organization_id=org_yunqi.id,
        name="云栖集团商场宠物通则（演示）",
        version=1,
        status="current",
        venue_scope="mall",
    )
    tr1 = PolicyTemplateRule(
        id=uid("template_rule_carrier"),
        template_id=template_mall.id,
        animal_scope="ordinary_pet",
        action="enter",
        effect="conditional",
        conditions=[{"condition_type": "carrier_required", "value_flag": True}],
        rule_layer="OPERATOR_POLICY",
        notes="集团：公共区域需宠物包",
    )
    tr2 = PolicyTemplateRule(
        id=uid("template_rule_sd"),
        template_id=template_mall.id,
        animal_scope="service_dog",
        action="enter",
        effect="allowed",
        rule_layer="OPERATOR_POLICY",
        notes="集团：服务犬通用通行",
    )
    binding_yunqi = PlacePolicyBinding(
        id=uid("binding_yunqi"),
        place_id=places["place_yunqi_mall"].id,
        template_id=template_mall.id,
        is_active=True,
        overrides=[
            {
                "id": "ovr-b1",
                "zone_id": z_mall_b1.id,
                "animal_scope": "ordinary_pet",
                "action": "enter",
                "effect": "prohibited",
                "note": "门店 override：B1 超市集团通则之上明确禁止",
            }
        ],
        source_id=src_mall_policy.id,
    )
    session.add_all([org_yunqi, template_mall, tr1, tr2])
    session.flush()
    session.add(binding_yunqi)
    session.flush()

    coex_cafe = [
        CoexistencePolicy(
            id=uid("coex_outdoor"),
            place_id=places["place_xinghe_cafe"].id,
            zone_id=z_cafe_outdoor.id,
            attribute="ordinary_pet_outdoor_dining",
            value="allowed",
            source_id=src_signage_cafe.id,
            verified_at=NOW - D(days=16),
        ),
        CoexistencePolicy(
            id=uid("coex_indoor"),
            place_id=places["place_xinghe_cafe"].id,
            zone_id=z_cafe_indoor.id,
            attribute="ordinary_pet_indoor_dining",
            value="prohibited",
            source_id=src_signage_cafe.id,
            verified_at=NOW - D(days=16),
        ),
        CoexistencePolicy(
            id=uid("coex_tableware"),
            place_id=places["place_xinghe_cafe"].id,
            zone_id=None,
            attribute="animal_use_customer_tableware",
            value="prohibited",
            source_id=src_signage_cafe.id,
            verified_at=NOW - D(days=16),
        ),
        CoexistencePolicy(
            id=uid("coex_seat"),
            place_id=places["place_xinghe_cafe"].id,
            zone_id=None,
            attribute="animal_on_customer_seat",
            value="prohibited",
            source_id=src_signage_cafe.id,
            verified_at=NOW - D(days=16),
        ),
    ]
    session.add_all(coex_cafe)

    session.add_all(
        [
            Amenity(
                id=uid("amen_water"),
                place_id=places["place_qinglan_park"].id,
                zone_id=z_park_pet.id,
                amenity_type="PET_WATER",
                status="available",
                source_id=src_park_gov.id,
                verified_at=NOW - D(days=20),
            ),
            Amenity(
                id=uid("amen_bag"),
                place_id=places["place_qinglan_park"].id,
                zone_id=z_park_pet.id,
                amenity_type="WASTE_BAG",
                status="available",
                source_id=src_park_gov.id,
                verified_at=NOW - D(days=20),
            ),
            Entrance(
                id=uid("entrance_south"),
                place_id=places["place_yunqi_mall"].id,
                zone_id=z_mall_1f.id,
                name="南门宠物通道",
                entrance_type="PET_DESIGNATED",
                access_notes="宠物推车/包从南门专用通道进入",
                source_id=src_mall_policy.id,
            ),
            AccessPath(
                id=uid("path_pet_zone"),
                place_id=places["place_yunqi_mall"].id,
                name="南门 → 3F 宠物区路线",
                from_node="南门",
                to_node="3F 宠物区",
                steps=[
                    {"step": 1, "node": "南门宠物通道"},
                    {"step": 2, "node": "2号宠物梯"},
                    {"step": 3, "node": "3F 宠物区"},
                ],
                animal_scope="ordinary_pet",
                conditions=[{"condition_type": "carrier_required", "value_flag": True}],
                source_id=src_mall_policy.id,
            ),
            SourceMonitor(
                id=uid("monitor_park"),
                source_id=src_park_gov.id,
                url="https://demo-gov.example/park-pet-policy",
                schedule_minutes=1440,
                place_id=places["place_qinglan_park"].id,
                content_hash="seedhash0001",
            ),
            FreshnessPolicy(
                id=uid("freshness_default"), name="默认 90 天复核", review_interval_days=90
            ),
            DataLicense(
                id=uid("license_park_gov"),
                source_id=src_park_gov.id,
                display_allowed=True,
                storage_allowed=True,
                redistribution_allowed=False,
                commercial_use_allowed=False,
                attribution_required=True,
                license_name="演示政府公开数据协议",
            ),
            BoundaryProfile(
                id=uid("boundary_alice"),
                user_id=users["alice"].id,
                name="A 的共处边界",
                is_default=True,
            ),
            BoundaryPreference(
                id=uid("bpref_indoor"),
                profile_id=uid("boundary_alice"),
                attribute="ordinary_pet_indoor_dining",
                stance="avoid",
                note="不接受普通宠物室内堂食",
            ),
            BoundaryPreference(
                id=uid("bpref_outdoor"),
                profile_id=uid("boundary_alice"),
                attribute="ordinary_pet_outdoor_dining",
                stance="accept",
            ),
            BoundaryPreference(
                id=uid("bpref_seat"),
                profile_id=uid("boundary_alice"),
                attribute="animal_on_customer_seat",
                stance="avoid",
            ),
            BoundaryPreference(
                id=uid("bpref_tableware"),
                profile_id=uid("boundary_alice"),
                attribute="animal_use_customer_tableware",
                stance="require_prohibited",
            ),
            EventPolicy(
                id=uid("event_market"),
                place_id=places["place_qinglan_park"].id,
                zone_id=z_park_pet.id,
                name="周末宠物市集（演示）",
                animal_scope="ordinary_pet",
                action="enter",
                effect="allowed",
                effective_from=NOW + D(days=7),
                effective_to=NOW + D(days=9),
                source_id=src_park_gov.id,
            ),
        ]
    )

    # --- audit log entry for the operator claim approval (design #25) ---
    session.add(
        AuditLog(
            id=uid("audit_claim_approval"),
            actor_user_id=users["admin"].id,
            actor_role=UserRole.ADMIN,
            action="operator_claim.approve",
            target_type="operator_claim",
            target_id=claim_yunqi.id,
            before_state={"status": "verifying"},
            after_state={"status": "approved"},
            detail={"place_id": places["place_yunqi_mall"].id},
        )
    )

    session.commit()
    counts.update(
        {
            "users": len(users),
            "pets": len(pets),
            "places": len(places),
            "zones": len(all_zones),
            "geometries": len(geometries),
            "sources": 8,
            "jurisdiction_rules": len(regs),
            "operator_claims": 2,
            "observations": 3,
            "verification_events": 2,
            "disputes": 1,
            "watches": 1,
        }
    )
    session.close()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic demo seed")
    parser.add_argument("--demo", action="store_true", help="load the fictional demo dataset")
    args = parser.parse_args()
    if not args.demo:
        print("Nothing to do: pass --demo")
        sys.exit(2)
    counts = run_demo_seed()
    print("Demo seed complete:", counts)


if __name__ == "__main__":
    main()
