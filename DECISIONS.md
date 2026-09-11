# DECISIONS.md
# Frozen Architecture Decisions

- ADR-001: Product models Access, not Friendliness.
- ADR-002: Core domain = Place → Zone → AccessRule.
- ADR-003: Place identity = platform UUID; map IDs are external refs.
- ADR-004: ObservationClaim never auto-converts to AccessRule.
- ADR-005: Deterministic rule evaluator; LLM only parses/extracts.
- ADR-006: Multi-dimensional Provenance; no core single trust score.
- ADR-007: Client = uni-app x + Vue 3 + TypeScript.
- ADR-008: Map = provider adapter; Tencent first.
- ADR-009: Backend = FastAPI + PostgreSQL/PostGIS + Redis + Celery.
- ADR-010: Admin = Vue 3 + TypeScript + Vite.
- ADR-011: OpenAPI = API contract SSOT.
- ADR-012: No default continuous location history.
- ADR-013: Residential communities = public-space rules only.
- ADR-014: User-selected filtering is neutral; editorial moral ranking is not.
- ADR-015: MVP does not depend on mass social scraping.
- ADR-016: Demo data is synthetic by default.

- ADR-017: Place.location is a denormalized geography(Point,4326) representative
  point synced by app logic; all authoritative geometry lives in place_geometry
  (Point/LineString/Polygon/MultiPolygon). Context: nearby queries need an
  indexed point without polygon centroid ambiguity. Status: accepted.
- ADR-018: Client = uni-app x source (apps/client, HBuilderX-built, all five
  targets) + platform-neutral @petaccess/client-core (shared business logic) +
  @petaccess/client-h5 Vite app as the locally verifiable H5 vehicle for
  G07/G17. Context: uni-app x has no npm CLI build path (no vite-uts branch,
  HBuilderX-only), and HBuilderX cannot be installed headlessly (BLOCKER B-01).
  The H5 app reuses the identical core; no business logic duplicated. Status: accepted.
- ADR-019: SQLAlchemy String columns store enum values; DB reads return plain
  str, so role/status comparisons use str values. response_models coerce back
  to enums at the API boundary. Status: accepted.

任何重大变更追加正式 ADR：
- Context
- Decision
- Alternatives
- Evidence
- Migration impact
- Status
