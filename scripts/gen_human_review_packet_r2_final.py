"""Generate the FINAL GOV-01 sign-off packet (revision **R2-FINAL-R3**).

``R2-FINAL-R3`` is the human sign-off round. It moves **no business datum**: the
register, the packet and the quick table are the ``R2-FINAL-R2`` content with the
revision label aligned to the round the human reviewer actually reviewed and
signed. The label had been one step behind the round — commit ``086c064`` was
titled "R2-FINAL-R3" while every artifact still stamped ``R2-FINAL-R2`` — which
is precisely the drift a signature gate must not tolerate: the authorising
document named a revision that no artifact carried.

Revision history
----------------

``R2-FINAL`` closed the ADR-028 compound-term split and set every sign-off field
blank. A human audit of that packet then found real defects, all fixed here:

  1. **Two decision vocabularies.** The quick table invited ``APPROVE`` /
     ``REJECT`` while the publisher read ``APPROVED`` / ``REJECTED``. The
     canonical set now lives in ``scripts/human_decisions.py`` and both sides
     import it — no aliases are printed or accepted without explicit mapping.
  2. **Provenance printed from the wrong place.** The per-row ``source_url`` came
     from the hand-maintained R2 register JSON while the quote came from the
     database, so one row showed a booking.com URL above a fairmont.com quote.
     Everything is now read from the *evidence chain*, and a divergence between
     what a row claims and what its chain supports is printed, not smoothed over.
  3. **Unproven operator source.** ``fp-pets-op`` was labelled ``primary_direct``
     while anchored on an OTA aggregator (tertiary, unverified,
     ``needs_verification=True``). The base prohibition now has its own row on the
     operator's page, sharing one licence-bearing first-party bundle with the
     guide-dog exception (``scripts/repair_fairmont_provenance_r1.py``). The
     superseded rows keep their evidence — nothing was deleted.
  4. **Claims the cited quote does not support.** ``gc-other-keep`` asserted
     ``other_areas = PROHIBITED`` from a quote that only establishes that a pilot
     exists. It is refused, not recommended.
  5. **Implicit statutory applicability.** The Disney legal rows projected a
     statute onto a ``scenic_area`` without ever showing that the venue falls in
     one of the categories the statute enumerates. Applicability is derived and
     displayed; un-evidenced rows are held.
  6. **Undated temporary policies.** ``TEMPORARY_POLICY`` rows must show
     effective_from / effective_to (or why it is open-ended) and when the current
     status was last verified; unverified rows are held.
  7. **Rows with no traceable locator.** The two xm rows had ``source_url=None``
     and no licence record, yet were passed as ``EVIDENCE_TRACEABLE``. They are
     held with the missing links named.

``R2-FINAL-R1`` was then re-audited and one more real defect surfaced, closed
here as **R2-FINAL-R2**:

  8. **Cross-layer exception binding.** The §1.7 plan attached operator
     carve-outs to *legal* prohibitions (``dl-sd-op → dl-legal-dog``,
     ``fp-sd-op-firstparty → fp-legal-dog``, ``lib-sd-op-* → lib-legal-dog``,
     ``qt-sd-op → qt-indoor-legal``). Because ``rule_exception`` inherits the
     base rule's layer, an operator's "guide dogs are welcome" would have been
     laundered into the LEGAL layer and would have out-voted the statute. Every
     carve-out now binds **inside its own layer** — legal exception → its own
     legal base, operator carve-out → the operator's own base rule — so the
     resolver's LEGAL > OPERATOR_POLICY precedence is never bypassed.
  9. **Operator carve-out with no legal basis.** 上海图书馆's own notice excepts
     军警犬 as well as 导盲犬, but the statute it is read against excepts only
     guide dogs. The operator rows therefore asserted an allowance that would
     silently relax a binding legal prohibition; they are held with
     ``LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED`` until a legal or
     administrative basis is produced.

Every row carries the full provenance block (issuer, locator, key quote, place
match, licence, temporal coverage, conflicts, exception binding) so a reviewer
can decide without opening the database.

Nothing here signs anything: all sign-off fields are emitted **blank**.

Usage: python scripts/gen_human_review_packet_r2_final.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import psycopg

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "services" / "api"))

from human_decisions import (  # noqa: E402
    HUMAN_DECISIONS,
    LABELS_ZH,
)

from app.rulespec.animal_scope import SCOPE_SUBJECTS  # noqa: E402

AUDIT = REPO / "docs" / "reality_audit"
REGISTRY_R2 = AUDIT / "review_decisions_r2.json"
REGISTRY_FINAL = AUDIT / "review_decisions_r2_final.json"
FAIRMONT_SIDECAR = AUDIT / "fp_firstparty_provenance_r1.json"

PACKET = REPO / "HUMAN_REVIEW_PACKET_R2_FINAL.md"
QUICK_TABLE = REPO / "HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md"
DECISIONS = REPO / "HUMAN_REVIEW_DECISIONS_R2_FINAL.json"

DB_URL = "postgresql://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess"
REVISION = "R2-FINAL-R3"

WEAK = {"search_snippet", "social_lead"}

#: A carve-out may only ever attach to a base rule **in its own layer**
#: (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE, principles B/C/D). A lower-layer
#: carve-out bound to a higher-layer prohibition is not a carve-out at all — it
#: would let an operator's "we allow it" rewrite a statute.
#:
#: Reason code for an operator carve-out that would relax an established legal
#: prohibition with no legal/administrative basis for that specific subject.
LEGAL_BASIS_REASON = "LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED"

#: rows whose evidence simply does not say what the row asserts
REJECT_RULES = {
    "gh-outdoor-keep": ["INSUFFICIENT_PLACE_ZONE_EVIDENCE", "LEGAL_SCOPE_CONFLICT"],
    "mn-outdoor-media": ["PLACE_ATTRIBUTION_ERROR", "INSUFFICIENT_PLACE_ZONE_EVIDENCE"],
    # R2-FINAL-R1: the cited quote establishes that 广场公园（黄浦段） *has* a pilot
    # pet area; it says nothing about the rest of the park being closed to pets.
    # Publishing it would invent a prohibition — refuse it instead.
    "gc-other-keep": [
        "CLAIM_NOT_SUPPORTED_BY_QUOTE",
        "INSUFFICIENT_PLACE_ZONE_EVIDENCE",
    ],
}

#: rows superseded by an equivalent row built on the operator's own channel.
#: The superseded rows keep their evidence (audit history is never deleted) but
#: must not be what we publish from.
SUPERSEDED_BY_FIRST_PARTY = {
    "fp-sd-op": "fp-sd-op-firstparty",
    "fp-pets-op": "fp-pets-op-firstparty",
}

#: The compound-term split (ADR-028): replaces one R2 row with three
LIBRARY_SPLIT = [
    ("lib-sd-op-guide", "76d0dfc3-64ae-4d2b-a152-18ff8ebed588"),
    ("lib-sd-op-police", "81168603-f74a-4130-8fd7-c09a645a4840"),
    ("lib-sd-op-military", "21578527-5b09-4d53-b868-512c3603b83f"),
]
LIBRARY_SPLIT_ORIGINAL = "lib-sd-op"

#: Rows introduced by the provenance repair (absent from the R2 register). Each
#: carries the id of the register row it is modelled after, so adding one cannot
#: silently drop the other — they replace the OTA twins, they do not replace
#: each other.
FIRST_PARTY_NEW_ROWS: list[tuple[str, str, str]] = [
    # (new rule_id, candidate_id, template rule_id)
    ("fp-sd-op-firstparty", "0de7771a-d461-4f86-8190-dac0604b9970", "fp-sd-op"),
    ("fp-pets-op-firstparty", "02454820-f30c-47de-851d-894496c36914", "fp-pets-op"),
]

#: 《上海市养犬管理条例》第二十三条 enumerates the venue categories it governs.
STATUTE_CATEGORIES = (
    "办公楼",
    "学校",
    "医院",
    "体育场馆",
    "博物馆",
    "图书馆",
    "文化娱乐场所",
    "候车（机、船）室",
    "餐饮场所",
    "商场",
    "宾馆",
)

#: place.place_type → the enumerated statutory category it plainly is.
#: ``None`` means the type does not map onto any enumerated category; applying the
#: statute to it is a legal interpretation that must be evidenced, not assumed.
PLACE_TYPE_TO_CATEGORY: dict[str, str | None] = {
    "cafe": "餐饮场所",
    "library": "图书馆",
    "mall": "商场",
    "hotel": "宾馆",
    "restaurant": "餐饮场所",
    "store": "商场",
    "museum": "博物馆",
    "hospital": "医院",
    "stadium": "体育场馆",
    "school": "学校",
    "office": "办公楼",
    "park": None,
    "scenic_area": None,
    "residential_community": None,
    "other": None,
    "unknown": None,
}

#: source url → moves that make the operator's channel explicit
LAYER_ZH = {
    "LEGAL": "法规",
    "REGULATORY_GUIDANCE": "监管指引",
    "OPERATOR_POLICY": "运营方政策",
    "TEMPORARY_POLICY": "临时/事件政策",
}
EFFECT_ZH = {"allowed": "允许", "prohibited": "禁止", "conditional": "有条件允许"}
SCOPE_ZH = {
    "dog": "犬（通用）",
    "ordinary_pet": "普通宠物",
    "service_dog": "服务犬（粗粒度 API scope）",
    "cat": "猫",
    "ordinary_dog": "普通犬",
    "guide_dog": "导盲犬",
    "hearing_dog": "助听犬",
    "assistance_dog": "辅助犬",
    "other_service_dog": "其他服务犬",
    "police_dog": "警犬",
    "military_working_dog": "军用工作犬",
}
NORM_ZH = {
    "exact": "精确（来源即此 scope，具备法律效力）",
    "compound_term_split": "复合词穷尽拆分（具备法律效力，成员集固定）",
    "parent_group_for_query_only": "仅用于查询分组（无法律效力）",
    "legal_interpretation_required": "需法律解释（当前无法律效力）",
}
STRENGTH_ZH = {
    "primary_direct": "官方一手直抓（逐字）",
    "primary_captured": "一手抓取",
    "secondary_reputable": "可靠二手（权威媒体直抓）",
    "search_snippet": "搜索摘要（未核验原文）",
    "social_lead": "社媒线索（仅线索）",
    "user_submitted": "用户提交",
}
MANDATORY_ZH = {"mandatory": "强制", "advisory": "建议", "operator_discretion": "运营方裁量"}
VERIFY_ZH = {"verified": "已核验", "unverified": "未核验", "disputed": "有争议"}
DIRECTNESS_ZH = {"direct": "直接", "secondary": "二手", "tertiary": "三手（聚合）"}


def _jdump(value) -> str:
    """Serialise for output; DB timestamps become their ISO text.

    Using ``str`` rather than raising keeps a temporal column from being able to
    take the whole packet down — better an ISO string than no sign-off register.
    """
    return json.dumps(value, ensure_ascii=False, default=str)


def fetch_chain(candidate_ids: list[str]) -> dict[str, dict]:
    """Authoritative provenance per candidate, straight from the evidence chain."""
    sql = """
    SELECT rc.id, rc.animal_scope, rc.action, rc.effect, rc.rule_layer,
           rc.mandatory_level, rc.review_status, rc.source_scope_exact,
           rc.subject_scope_normalized, rc.normalization_type,
           rc.normative_effect, rc.holder_scope, rc.zone_id, rc.source_id,
           rc.evidence_bundle_id, rc.raw_text,
           z.name AS zone_name, z.zone_type, z.indoor_outdoor,
           p.canonical_name AS place_name, p.place_type,
           p.canonical_address AS place_address,
           s.source_type, s.issuer, s.issuer_verification, s.source_url,
           s.source_snapshot_ref, s.source_availability, s.directness,
           s.spatial_precision, s.published_at AS src_published_at,
           s.observed_at, s.collected_at, s.notes AS src_notes,
           eb.id AS bundle_id, eb.source_url AS bundle_url, eb.source_platform,
           eb.publisher_type, eb.evidence_class, eb.quoted_fragment,
           eb.extracted_fragment, eb.content_hash, eb.place_match_evidence,
           eb.temporal_evidence, eb.license_metadata, eb.captured_at,
           eb.published_at AS bundle_published_at, eb.screenshot_ref,
           eb.snapshot_ref, eb.artifact_id,
           art.artifact_type, art.source_url AS artifact_url,
           art.source_content_id, art.snapshot_ref AS artifact_snapshot_ref,
           art.collector_type, art.evidence_strength AS artifact_strength,
           art.storage_allowed, art.display_allowed, art.redistribution_allowed,
           art.publisher_type AS artifact_publisher
      FROM rule_candidate rc
      LEFT JOIN zone  z  ON z.id  = rc.zone_id
      LEFT JOIN place p  ON p.id  = rc.place_id
      LEFT JOIN source s ON s.id  = rc.source_id
      LEFT JOIN evidence_bundle eb ON eb.id = rc.evidence_bundle_id
      LEFT JOIN source_artifact art ON art.id = eb.artifact_id
     WHERE rc.id = ANY(%s)
    """
    out: dict[str, dict] = {}
    with psycopg.connect(DB_URL, connect_timeout=10) as conn, conn.cursor() as cur:
        cur.execute(sql, (candidate_ids,))
        description = cur.description
        if description is None:
            # a SELECT always yields one; failing loudly beats indexing None
            raise RuntimeError("证据链查询未返回列描述")
        cols = [c.name for c in description]
        for raw in cur.fetchall():
            d = dict(zip(cols, raw, strict=True))
            out[d["id"]] = d
    return out


def derive_evidence_strength(st: dict) -> tuple[str, list[str]]:
    """Recompute strength from the chain instead of trusting the register entry.

    The register field is the *opinion recorded at ingest time*. The chain is what
    we can actually defend: an aggregator page is not a first-party capture no
    matter what its row says.
    """
    notes = st.get("src_notes") or ""
    needs_verification = "needs_verification=True" in notes
    directness = (st.get("directness") or "").lower()
    verification = (st.get("issuer_verification") or "").lower()
    platform = (st.get("source_platform") or "").lower()
    claimed = st.get("artifact_strength")

    if directness == "direct" and verification == "verified" and not needs_verification:
        return "primary_direct", []
    if directness == "secondary" and not needs_verification:
        return "secondary_reputable", []
    if directness == "tertiary" or needs_verification:
        return "search_snippet", [
            f"source.directness={directness or '未标注'} / "
            f"issuer_verification={verification or '未标注'} / "
            f"needs_verification={needs_verification} —— 不代表运营方一手来源"
        ]
    if "search_snippet" in platform:
        return "search_snippet", []
    return claimed or "primary_captured", []


def effective_window(st: dict) -> dict:
    """Temporal coverage, plus how confident we are about *right now*.

    ``last_verified_at`` falls back through capture metadata so ordinary rows can
    show when we last looked at the page. That fallback is deliberately flagged:
    for a temporary policy it does **not** count as a freshness check, because
    "we captured this once in 2025" says nothing about whether it is still in
    force in 2026.
    """
    te = st.get("temporal_evidence") or {}
    explicit = te.get("last_verified_at")
    fallback = (
        te.get("captured_at")
        or st.get("captured_at")
        or st.get("observed_at")
        or st.get("collected_at")
    )
    if explicit is not None:
        last_verified, how = explicit, "explicit"
    elif fallback is not None:
        last_verified, how = fallback, "capture_fallback"
    else:
        last_verified, how = None, "missing"
    return {
        "effective_from": te.get("effective_from"),
        "effective_to": te.get("effective_to"),
        "open_ended_reason": te.get("open_ended_reason"),
        "last_verified_at": last_verified,
        "last_verified_provenance": how,
        "needs_verification": te.get("needs_verification"),
        "published_at": te.get("published_at"),
        "captured_at": te.get("captured_at") or st.get("captured_at"),
    }


def _freshness_problems(st: dict, win: dict, rule_layer: str) -> list[str]:
    """Temporal facts missing that a reviewer is entitled to see.

    Only a *bounded* policy needs an end date. Treating a missing ``effective_to``
    as a defect for a statute would flag every standing law in the register,
    which would make "HOLD" meaningless — so the requirement is scoped to the
    layers whose validity genuinely expires.
    """
    out: list[str] = []
    bounded = rule_layer in {"TEMPORARY_POLICY", "REGULATORY_GUIDANCE"}
    if bounded:
        if not win.get("effective_from"):
            out.append("缺 effective_from")
        if not win.get("effective_to") and not win.get("open_ended_reason"):
            out.append("缺 effective_to 且未记录 open-ended 原因")
        if win.get("last_verified_provenance") != "explicit":
            out.append("缺 last_verified_at（捕获时间不能代替「当前是否仍有效」的复核）")
    if win.get("needs_verification") is True:
        out.append("source 仍标记 needs_verification=True（未复核当前状态）")
    return out


def _source_locator(st: dict) -> tuple[str | None, list[str], list[str]]:
    """The strongest reproducible pointer we can hand a reviewer.

    Returns ``(url, blockers, notes)``. A blocker means the chain is genuinely
    untraceable and the row cannot be cleared; a note is something a reviewer
    should see but that does not, on its own, invalidate the evidence.

    That distinction matters: almost no capture in this corpus has a formal
    snapshot, and calling that a blocker would hold every row in the register —
    which would make HOLD worthless as a signal. Reproducibility here rests on
    canonical URL + content_hash; the missing snapshot is disclosed, not fatal.
    """
    blockers: list[str] = []
    notes: list[str] = []
    url = st.get("source_url") or st.get("bundle_url") or st.get("artifact_url")
    if not url:
        blockers.append("source.source_url 为空 —— 无可追溯 capture locator")
    if not st.get("artifact_id"):
        blockers.append("无 SourceArtifact 记录")
    if not st.get("content_hash"):
        blockers.append("无 content_hash —— 摘录不可复现校验")
    if not (
        st.get("snapshot_ref") or st.get("artifact_snapshot_ref") or st.get("source_snapshot_ref")
    ):
        notes.append("无快照/归档 locator（可复现性依赖线上 URL + content_hash）")
    if not st.get("source_url"):
        notes.append(
            "source.source_url 为空，本行 URL 取自助证 bundle/artifact locator"
            if url
            else "无任何可用 URL"
        )
    return url, blockers, notes


def _license_problems(st: dict) -> list[str]:
    out: list[str] = []
    lm = st.get("license_metadata")
    if not lm:
        out.append("bundle.license_metadata 为空")
    else:
        for key, label in (
            ("storage_allowed", "storage_allowed"),
            ("display_allowed", "display_allowed"),
            ("redistribution_allowed", "redistribution_allowed"),
        ):
            if lm.get(key) is None:
                out.append(f"license 未声明 {label}")
    if st.get("storage_allowed") is None:
        out.append("SourceArtifact 未记录 storage/display/redistribution 三态")
    return out


def _applicability(st: dict) -> dict:
    """Does anything evidence that this venue is one the statute governs?

    A legal projection is only as strong as the link between the place and the
    category the statute names. Making that link explicit either clears the row or
    shows exactly what is missing — never left implicit.
    """
    place_type = st.get("place_type") or "unknown"
    category = PLACE_TYPE_TO_CATEGORY.get(place_type)
    if category is None:
        return {
            "place_type": place_type,
            "statutory_category": None,
            "status": "NOT_EVIDENCED",
            "venue_scope": None,
            "note": (
                f"场所类型 place_type={place_type} 不属于第二十三条枚举的任一类别"
                f"（{'/'.join(STATUTE_CATEGORIES)}）；"
                "将其纳入该法条适用范围属法律解释，需显式证据支撑。"
            ),
        }
    return {
        "place_type": place_type,
        "statutory_category": category,
        "status": "ENUMERATED_IN_STATUTE",
        "venue_scope": "whole_place",
        "note": "场所类型与法条枚举类别直接对应，适用性可自证。",
    }


def _covers_scope(base_scope: str, base_norm: str | None, row_norm: str | None) -> bool:
    """True when a prohibition on ``base`` would also cover ``row``'s subject."""
    if row_norm is None:
        return True
    covered = SCOPE_SUBJECTS.get(base_scope) or SCOPE_SUBJECTS.get(base_norm or "")
    if covered is None:
        return True
    return row_norm in covered


def _subject_covered_by(base_row: dict, subject: str | None) -> bool:
    """Does ``base_row``'s recorded scope legally cover ``subject``?

    Unlike :func:`_covers_scope` this is only ever asked about a *legal* rule
    (scope ``dog``), so it answers "would the statute reach this subject?".
    """
    if not subject:
        return False
    scope = base_row.get("subject_scope_normalized") or base_row.get("animal_scope") or ""
    covered = SCOPE_SUBJECTS.get(scope)
    if covered is None:
        return False
    return subject in covered


def _same_operator_channel(base: dict, me: dict) -> bool:
    """Both rules quote the *same* source record — the operator's own document.

    An operator's page states the prohibition and its carve-out in one breath
    ("禁止宠物入内。导盲犬可随时进入酒店。"), so the two rows share a ``source_id``.
    That shared origin is what makes the allowance a carve-out *of that rule*
    rather than of some other layer's rule.
    """
    src = me.get("source_id")
    return bool(src) and base.get("source_id") == src


def carve_out_bases(row_id: str, rows: list[dict], *, same_layer_only: bool = True) -> list[str]:
    """Base prohibition rows this row must become an exception *to*.

    An allowed row that overlaps a prohibition in the same place is not a
    contradiction to publish twice — it is a carve-out, which the schema models
    as ``rule_exception`` bound to the base rule.

    **Layer faithfulness (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE).** With
    ``same_layer_only`` (the default, and the only mode the plan uses) a base is
    eligible only when it sits in the *same* layer: a LEGAL exception binds its
    own legal base, an OPERATOR_POLICY carve-out binds the operator's own base
    rule. Passing ``same_layer_only=False`` reproduces the old, layer-blind
    behaviour — used solely to *detect* the cross-layer overrides the earlier
    revision contained, never to publish from.
    """
    me = next((r for r in rows if r["rule_id"] == row_id), None)
    if me is None or me["effect"] not in ("allowed", "conditional"):
        return []
    bases: list[str] = []
    for other in rows:
        if other["rule_id"] == row_id or other["effect"] != "prohibited":
            continue
        if other["place_key"] != me["place_key"]:
            continue
        if same_layer_only and other["rule_layer"] != me["rule_layer"]:
            continue
        same_zone = other["zone_id"] == me["zone_id"]
        if not (same_zone or not other["zone_id"] or not me["zone_id"]):
            continue
        # Scope coverage alone can never justify an operator carve-out: the
        # operator writes its ban against `ordinary_pet`, which excludes service
        # dogs, so the shared *document* is the binding evidence.
        if _covers_scope(
            other["animal_scope"],
            other["subject_scope_normalized"],
            me["subject_scope_normalized"],
        ) or _same_operator_channel(other, me):
            bases.append(other["rule_id"])
    return sorted(set(bases))


def cross_layer_bases(row_id: str, rows: list[dict]) -> list[str]:
    """Bases the layer-blind rule would have attached, minus the faithful ones.

    Non-empty ⇒ this carve-out was, in an earlier revision, pointed at a rule in
    a different (higher) layer. That is exactly the override the plan must never
    publish, so it is surfaced as a finding rather than silently dropped.
    """
    naive = set(carve_out_bases(row_id, rows, same_layer_only=False))
    faithful = set(carve_out_bases(row_id, rows))
    return sorted(naive - faithful)


def _legal_basis_gap(row: dict, rows: list[dict]) -> str | None:
    """An operator allowance that would relax an established legal prohibition.

    Principle C: an operator's policy saying "allowed" is not, by itself, an
    exception to a legal prohibition. When the statute (or the reviewer's
    applicable reading of it) already prohibits the subject, the operator
    carve-out can only hold if the *law* provides for that subject too — a
    statutory proviso, or a legal exception row with its own basis. Otherwise
    the allowance would silently relax a binding rule; it is held instead.

    Returns a human-readable list of the shadowing legal rules, or ``None`` when
    there is nothing to answer for.
    """
    if row["rule_layer"] != "OPERATOR_POLICY" or row["effect"] not in ("allowed", "conditional"):
        return None
    subject = row.get("subject_scope_normalized")
    if not subject:
        return None
    shadowing = [
        other
        for other in rows
        if other["rule_layer"] == "LEGAL"
        and other["effect"] == "prohibited"
        and other["place_key"] == row["place_key"]
        and other.get("proposed_decision") == "RECOMMEND_APPROVE"
        and _subject_covered_by(other, subject)
    ]
    if not shadowing:
        return None
    covered = any(
        other["rule_layer"] == "LEGAL"
        and other["effect"] in ("allowed", "conditional")
        and other["place_key"] == row["place_key"]
        and other.get("subject_scope_normalized") == subject
        and other.get("proposed_decision") == "RECOMMEND_APPROVE"
        for other in rows
    )
    if covered:
        return None
    return "；".join(f"`{o['rule_id']}`" for o in shadowing)


def recommend(row: dict, rows: list[dict]) -> tuple[str, str, list[str] | None]:
    rule_id = row["rule_id"]
    codes: list[str] = list(row.get("reject_reason_codes") or [])

    if rule_id in REJECT_RULES:
        return "RECOMMEND_REJECT", "REJECT_CURRENT_CLAIM", REJECT_RULES[rule_id]

    if rule_id in SUPERSEDED_BY_FIRST_PARTY:
        return (
            "RECOMMEND_REJECT",
            "SUPERSEDED_BY_FIRST_PARTY_SOURCE",
            [
                "SUPERSEDED_BY_FIRST_PARTY_SOURCE",
                "SOURCE_NOT_OPERATOR_OF_RECORD",
                f"替代行：{SUPERSEDED_BY_FIRST_PARTY[rule_id]}",
            ],
        )

    gaps: list[str] = []
    if row["evidence_strength"] in WEAK:
        gaps.append(f"证据强度 {row['evidence_strength']} 未达一手标准（ADR-021）")
        gaps.extend(row["strength_notes"])
    gaps.extend(row["locator_gaps"])
    gaps.extend(row["license_problems"])
    gaps.extend(row["freshness_problems"])

    # Principle C: an operator's "we allow it" never licenses an exception to a
    # legal prohibition. Asked only of operator carve-outs, and only after the
    # legal layer has been decided (build_rows orders the passes that way).
    shadow = _legal_basis_gap(row, rows)
    if shadow:
        return (
            "RECOMMEND_HOLD",
            LEGAL_BASIS_REASON,
            [
                LEGAL_BASIS_REASON,
                f"该运营方豁免会放宽已生效的法规禁令 {shadow}，"
                f"但尚无针对 `{row['subject_scope_normalized']}` 的法律/行政依据；"
                "运营方政策不得作为法律禁令的例外（原则 B/C）。",
            ],
        )

    if row["rule_layer"] == "LEGAL":
        applic = row["applicability"]
        if applic and applic["status"] != "ENUMERATED_IN_STATUTE":
            return (
                "RECOMMEND_HOLD",
                "STATUTORY_APPLICABILITY_NOT_EVIDENCED",
                ["APPLICABILITY_EVIDENCE_MISSING", applic["note"]],
            )

    if row["rule_layer"] == "TEMPORARY_POLICY" and any(
        p.startswith("缺 last_verified_at") or p.startswith("source 仍标记")
        for p in row["freshness_problems"]
    ):
        return (
            "RECOMMEND_HOLD",
            "TEMPORARY_STATUS_NOT_REVERIFIED",
            ["FRESHNESS_INCOMPLETE", "未复核该临时/试点政策当前是否仍有效"],
        )

    if row["normalization_type"] not in {"exact", "compound_term_split"}:
        return (
            "RECOMMEND_HOLD",
            "SCOPE_NOT_ESTABLISHED_AS_LEGAL",
            ["SCOPE_NORMALIZATION_NOT_LEGAL"],
        )

    if gaps:
        return "RECOMMEND_HOLD", "EVIDENCE_CHAIN_INCOMPLETE", codes + gaps

    return "RECOMMEND_APPROVE", "EVIDENCE_TRACEABLE", None


def load_base_rows() -> list[dict]:
    return json.loads(REGISTRY_R2.read_text(encoding="utf-8"))["rows"]


def expand_rows(base_rows: list[dict]) -> list[dict]:
    """Apply the ADR-028 split and append the new first-party rows."""
    expanded: list[dict] = []
    for row in base_rows:
        if row["rule_id"] == LIBRARY_SPLIT_ORIGINAL:
            for rule_id, cid in LIBRARY_SPLIT:
                clone = dict(row)
                clone["rule_id"] = rule_id
                clone["candidate_id"] = cid
                expanded.append(clone)
            continue
        expanded.append(dict(row))

    for rule_id, cid, template_id in FIRST_PARTY_NEW_ROWS:
        template = next(r for r in base_rows if r["rule_id"] == template_id)
        clone = dict(template)
        clone["rule_id"] = rule_id
        clone["candidate_id"] = cid
        expanded.append(clone)
    return expanded


def build_rows() -> list[dict]:
    rows = expand_rows(load_base_rows())
    chain = fetch_chain([r["candidate_id"] for r in rows])
    missing = [r["rule_id"] for r in rows if r["candidate_id"] not in chain]
    if missing:
        raise SystemExit(f"登记表中的候选不在数据库中：{missing}")

    for row in rows:
        st = chain[row["candidate_id"]]
        row["place_name"] = st.get("place_name") or row["place_name"]
        row["place_address"] = st.get("place_address")
        row["place_type"] = st.get("place_type")
        row["zone_id"] = st.get("zone_id")
        row["zone_name"] = st.get("zone_name")
        row["zone_type"] = st.get("zone_type")
        row["indoor_outdoor"] = st.get("indoor_outdoor")

        row["animal_scope"] = st["animal_scope"]
        row["action"] = st["action"]
        row["effect"] = st["effect"]
        row["rule_layer"] = st["rule_layer"]
        row["mandatory_level"] = st["mandatory_level"]
        row["review_status"] = st["review_status"]
        row["source_scope_exact"] = st["source_scope_exact"]
        row["subject_scope_normalized"] = st["subject_scope_normalized"]
        row["normalization_type"] = st["normalization_type"]
        row["normative_effect"] = st["normative_effect"]
        row["holder_scope"] = st["holder_scope"]

        row["source_id"] = st.get("source_id")
        row["source_type"] = st.get("source_type")
        row["issuer"] = st.get("issuer")
        row["issuer_verification"] = st.get("issuer_verification")
        row["bundle_url"] = st.get("bundle_url")
        row["artifact_id"] = st.get("artifact_id")
        row["artifact_url"] = st.get("artifact_url")
        row["artifact_type"] = st.get("artifact_type")
        row["snapshot_ref"] = (
            st.get("snapshot_ref")
            or st.get("artifact_snapshot_ref")
            or st.get("source_snapshot_ref")
        )
        row["source_content_id"] = st.get("source_content_id")
        row["directness"] = st.get("directness")
        row["spatial_precision"] = st.get("spatial_precision")
        row["source_availability"] = st.get("source_availability")
        row["quoted_fragment"] = st.get("quoted_fragment")
        row["content_hash"] = st.get("content_hash")
        row["place_match_evidence"] = st.get("place_match_evidence")
        row["license_metadata"] = st.get("license_metadata")
        row["artifact_license"] = {
            "storage_allowed": st.get("storage_allowed"),
            "display_allowed": st.get("display_allowed"),
            "redistribution_allowed": st.get("redistribution_allowed"),
        }
        row["captured_at"] = st.get("captured_at")
        row["raw_text"] = st.get("raw_text")

        strength, strength_notes = derive_evidence_strength(st)
        # Capture the claimed value *before* overwriting it — comparing after the
        # assignment would make every row look consistent.
        claimed_strength = row.get("evidence_strength")
        row["evidence_strength_claimed"] = claimed_strength
        row["evidence_strength"] = strength
        row["evidence_strength_conflict"] = claimed_strength != strength
        row["strength_notes"] = strength_notes

        win = effective_window(st)
        row["effective_from"] = win["effective_from"]
        row["effective_to"] = win["effective_to"]
        row["open_ended_reason"] = win["open_ended_reason"]
        row["last_verified_at"] = win["last_verified_at"]
        row["freshness_problems"] = _freshness_problems(st, win, row["rule_layer"])

        row["source_url"], row["locator_gaps"], row["locator_notes"] = _source_locator(st)
        row["license_problems"] = _license_problems(st)
        row["applicability"] = _applicability(st) if row["rule_layer"] == "LEGAL" else None

    for row in rows:
        row["carve_out_of"] = carve_out_bases(row["rule_id"], rows)
        row["cross_layer_dropped"] = cross_layer_bases(row["rule_id"], rows)
        row["exception_binding_required"] = bool(row["carve_out_of"])

    def _decide(row: dict) -> None:
        rec, reason, codes = recommend(row, rows)
        row["proposed_decision"] = rec
        row["proposed_reason"] = reason
        row["reject_reason_codes"] = codes
        row["final_decision"] = None
        row["reviewer"] = None
        row["reviewed_at"] = None
        row["review_note"] = None

    # The legal layer is decided first: an operator carve-out's legality is
    # judged against the legal layer's verdicts, so those must already exist.
    for row in rows:
        if row["rule_layer"] == "LEGAL":
            _decide(row)
    for row in rows:
        if row["rule_layer"] != "LEGAL":
            _decide(row)

    order = {"RECOMMEND_REJECT": 0, "RECOMMEND_HOLD": 1, "RECOMMEND_APPROVE": 2}
    rows.sort(key=lambda r: (order.get(r["proposed_decision"], 3), r["place_key"], r["rule_id"]))
    return rows


def validate_exception_binding(plan: list[dict]) -> None:
    """Refuse to emit a plan that contains a cross-layer binding.

    The plan is the instruction a human publishes from, and the resolver honours
    whatever base a ``rule_exception`` names (the exception inherits the base's
    layer). An operator carve-out attached to a legal prohibition would therefore
    *become* a legal rule and out-vote the statute. Refusing generation is the
    only safe outcome — closing the hole in the plan is what makes the closed
    resolver guarantee hold end to end.
    """
    offenders = [
        f"{entry['rule_id']} → {base['rule_id']}[{base['layer']}]"
        for entry in plan
        for base in entry["bases"]
        if not base["same_layer"] or base["layer"] != entry["layer"]
    ]
    if offenders:
        raise SystemExit(
            "RuleException 绑定必须层内一致（原则 A–D）；检测到跨层绑定：\n  - "
            + "\n  - ".join(offenders)
        )


def exception_plan(rows: list[dict]) -> list[dict]:
    """The RuleException binding table: every carve-out and the base it binds to.

    Emitted as machine-readable data (not only prose) so the publish step — and
    the audit — consume the *same* binding the reviewer read. Three invariants
    the plan is built to make impossible:

    * a carve-out binding a base in another layer (``same_layer`` must be true
      for every binding, and the section asserts a cross-layer count of 0);
    * an entry marked executable while its base is not itself being published
      (a held base cannot receive a published exception);
    * a carve-out published as a plain ``AccessRule`` instead of an exception.
    """
    plan: list[dict] = []
    for row in rows:
        if not row["exception_binding_required"]:
            continue
        # A candidate we recommend rejecting never becomes an AccessRule, so it
        # has nothing to bind to and no place in a publish plan.
        if row["proposed_decision"] == "RECOMMEND_REJECT":
            continue

        bases: list[dict] = []
        blocked: list[str] = []
        for base_id in row["carve_out_of"]:
            base = next((b for b in rows if b["rule_id"] == base_id), None)
            if base is None:
                continue
            same_layer = base["rule_layer"] == row["rule_layer"]
            base_ok = base["proposed_decision"] == "RECOMMEND_APPROVE"
            if not same_layer:
                blocked.append(f"{base_id}：跨层（不得绑定）")
            elif not base_ok:
                blocked.append(
                    f"{base_id}：基础规则 {base['proposed_decision']}，不可作为已发布例外的基础"
                )
            bases.append(
                {
                    "rule_id": base_id,
                    "layer": base["rule_layer"],
                    "decision": base["proposed_decision"],
                    "same_layer": same_layer,
                    "executable": base_ok and same_layer,
                }
            )

        self_publishable = row["proposed_decision"] == "RECOMMEND_APPROVE"
        if not self_publishable:
            blocked.insert(0, f"例外自身为 {row['proposed_decision']}，本批不发布")
        executable = bool(bases) and self_publishable and all(b["executable"] for b in bases)

        plan.append(
            {
                "rule_id": row["rule_id"],
                "candidate_id": row["candidate_id"],
                "place_key": row["place_key"],
                "place_name": row["place_name"],
                "zone_name": row["zone_name"],
                "layer": row["rule_layer"],
                "effect": row["effect"],
                "mandatory_level": row["mandatory_level"],
                "source_scope_exact": row["source_scope_exact"],
                "subject_scope_normalized": row["subject_scope_normalized"],
                "normalization_type": row["normalization_type"],
                "normative_effect": row["normative_effect"],
                "source_id": row["source_id"],
                "source_url": row["source_url"],
                "issuer": row["issuer"],
                "decision": row["proposed_decision"],
                "mode": "rule_exception" if bases else "non_conflicting_operator_carve_out",
                "bases": bases,
                "executable": executable,
                "cross_layer_dropped": row["cross_layer_dropped"],
                "blocked_reasons": blocked,
            }
        )
    validate_exception_binding(plan)
    return plan


def write_registry(rows: list[dict]) -> None:
    # A row already signed by a named human keeps that signature: the register is
    # rebuilt from the database so the machine proposal stays honest, not so the
    # human's ruling can be regenerated away.
    preserve_signature(rows, _read_existing(REGISTRY_FINAL).get("rows"))
    doc = {
        "_readme": [
            f"{REVISION} GOV-01 sign-off register (ADR-025 / ADR-028).",
            "Generated FROM THE DATABASE evidence chain, so the packet cannot",
            "disagree with what publishing would consume.",
            "Supersedes review_decisions_r2.json (which superseded _r1).",
            "上海图书馆 compound exception (导盲犬、军警犬例外) is split into three",
            "source-exact rows; the compound wording is preserved verbatim.",
            "RuleException binding is LAYER-FAITHFUL: a carve-out binds only a base",
            "rule in its own layer, so an operator's allowance can never be",
            "laundered into the LEGAL layer (RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE).",
            "proposed_decision is a MACHINE PROPOSAL, not a ruling. A named human must",
            "set final_decision + reviewer + reviewed_at before publish_reviewed_r1.py runs.",
            f"Allowed final_decision values: {' | '.join(HUMAN_DECISIONS)}.",
        ],
        "revision": REVISION,
        "supersedes": "docs/reality_audit/review_decisions_r2.json",
        "human_signoff_required": True,
        "human_decisions": list(HUMAN_DECISIONS),
        "exception_binding": {
            "policy": "same-layer-only",
            "legal_exception_binds": "LEGAL",
            "operator_carve_out_binds": "OPERATOR_POLICY",
            "cross_layer_override_allowed": False,
        },
        "exception_plan": exception_plan(rows),
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": rows,
    }
    REGISTRY_FINAL.write_text(_jdump(doc) + "\n", encoding="utf-8", newline="\n")


def _fmt(v) -> str:
    if v is None or v == "" or v == [] or v == {}:
        return "—"
    if isinstance(v, list):
        return "；".join(str(x) for x in v)
    return str(v)


def _conditions(row: dict) -> str:
    conds = row.get("conditions") or []
    if not conds:
        return "无"
    return "、".join(
        str(c.get("condition_type", c)) if isinstance(c, dict) else str(c) for c in conds
    )


def _license_line(row: dict) -> str:
    parts: list[str] = []
    lm = row.get("license_metadata") or {}
    if lm:
        parts.append(
            f"bundle: storage={lm.get('storage_allowed')} / "
            f"display={lm.get('display_allowed')} / "
            f"redistrib={lm.get('redistribution_allowed')}"
        )
        if lm.get("license_name"):
            parts.append(f"《{lm['license_name']}》")
        if lm.get("reproducibility"):
            parts.append(str(lm["reproducibility"]))
    art = row.get("artifact_license") or {}
    parts.append(
        f"artifact: storage={art.get('storage_allowed')} / "
        f"display={art.get('display_allowed')} / "
        f"redistrib={art.get('redistribution_allowed')}"
    )
    return "；".join(parts)


def _library_split_section(rows: list[dict]) -> str:
    L = ["### 1.1 上海图书馆复合词拆分（ADR-028）", ""]
    L.append("来源原文：`请勿携带活禽以及猫、狗（导盲犬、军警犬除外）等动物入馆。`")
    L.append("")
    L.append("| rule_id | source_scope_exact（原话） | normalized | normalization_type |")
    L.append("|---|---|---|---|")
    for r in rows:
        if r["rule_id"].startswith("lib-sd-op-"):
            L.append(
                f"| `{r['rule_id']}` | {r['source_scope_exact']} | "
                f"{r['subject_scope_normalized']} | `{r['normalization_type']}` |"
            )
    L.append("")
    L.append(
        "> 「军警犬」未在原文中区分军犬/警犬，故 `source_scope_exact` **原样保留「军警犬」**，"
    )
    L.append("> 由两行分别承载 `police_dog` 与 `military_working_dog`；两行并集恰为「军警犬」，")
    L.append("> 且**不包含**任何其他 working dog。")
    L.append("")
    return "\n".join(L)


def _fairmont_section() -> str:
    sidecar = (
        json.loads(FAIRMONT_SIDECAR.read_text(encoding="utf-8"))
        if FAIRMONT_SIDECAR.exists()
        else None
    )
    zh = "https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html"
    L = ["### 1.2 和平饭店：一手来源到底挂在哪（修 §2 缺陷）", ""]
    L.append("审计发现的自相矛盾及其根因：")
    L.append("")
    L.append("- **逐条里的 `fp-sd-op` 显示 booking.com**：该行 `source.source_url` 确实仍指向")
    L.append("  OTA 聚合页（`directness=tertiary`、`issuer_verification=unverified`、")
    L.append("  `needs_verification=True`）。")
    L.append("- **前文却说已挂 fairmont.com**：一手来源自 2026-09-13 起就存在并被")
    L.append("  `fp-sd-op-firstparty` 正确引用；当时的生成器把 `source_url` 取手工登记表、")
    L.append("  把引文取数据库，两者拼在一行里就自相矛盾了。")
    L.append("- **`fp-pets-op` 声称 primary_direct**：它的确不配这个等级（源为 OTA），")
    L.append("  本轮的 EvidenceStrength 由**证据链推导**，不再采信登记表自述。")
    L.append("")
    L.append("**本轮处置**：生成端一律从证据链读取；两个 OTA 行改为 REJECT")
    L.append("（源非运营方一手、且被同名一手行取代），旧证据**一条未删**。")
    L.append("")
    L.append("| 项 | 内容 |")
    L.append("|---|---|")
    if sidecar:
        L.append(f"| 一手来源 URL（zh） | {zh} |")
        L.append(
            f"| 一手 bundle | `{sidecar.get('bundle_id')}` · content_hash "
            f"`{str(sidecar.get('content_hash'))[:16]}…` |"
        )
        L.append(
            "| 共用行 | 基础规则 `fp-pets-op-firstparty`（禁止宠物）· "
            "例外 `fp-sd-op-firstparty`（导盲犬） |"
        )
        L.append(f"| 实读复核 | {sidecar.get('reverified_at')} 复核 zh+en 双语页，逐字一致 |")
        L.append("| 被取代的旧行 | `fp-sd-op` / `fp-pets-op`（证据保留，不再作为发布依据） |")
    L.append("")
    L.append("> 禁止宠物基础规则与导盲犬例外**共用同一句原文**，因此不需要两条独立证据。")
    L.append("")
    return "\n".join(L)


def _gc_other_keep_section() -> str:
    return "\n".join(
        [
            "### 1.3 gc-other-keep：改判（修 §3 缺陷）",
            "",
            "该行断言「广场公园（黄浦段）其余区域禁止宠物」，但其唯一引文是：",
            "",
            "> 目前这3个地方都属于试点，我们在现场张贴了试点公告，"
            "待试点结束后，将根据实际情况形成正式的规定。",
            "",
            "这句话只证明**试点存在**，不证明公园其余区域禁止宠物——把「未列入试点」",
            "读成「明令禁止」是平台替来源做的推断。",
            "因此由 APPROVE 改判 **RECOMMEND_REJECT**"
            "（`CLAIM_NOT_SUPPORTED_BY_QUOTE` + `INSUFFICIENT_PLACE_ZONE_EVIDENCE`）。",
            "若运营方现场公告明确写了「宠物仅限 H6 区域」，请补充该一手取证后重开此行。",
            "",
        ]
    )


def _disney_section(rows: list[dict]) -> str:
    L = ["### 1.4 迪士尼 LEGAL 投影：适用性必须被证明（修 §4 缺陷）", ""]
    L.append("《上海市养犬管理条例》第二十三条管辖的是**它自己枚举的类别**：")
    L.append("")
    L.append("> " + "、".join(STATUTE_CATEGORIES))
    L.append("")
    L.append("| rule_id | place_type | 对应法条类别 | 适用性状态 | 建议 |")
    L.append("|---|---|---|---|---|")
    for r in rows:
        if r["rule_layer"] == "LEGAL" and r["place_key"] == "dl-disneyland":
            ap = r["applicability"]
            L.append(
                f"| `{r['rule_id']}` | `{ap['place_type']}` | "
                f"{_fmt(ap['statutory_category'])} | **{ap['status']}** | "
                f"{r['proposed_decision']} |"
            )
    L.append("")
    L.append("> 上海迪士尼 `place_type=scenic_area`（景区），**不在上述枚举名单内**。")
    L.append("> 「景区属于文化娱乐场所」是一个法律解释，不是已取证的事实；")
    L.append("> 在缺证据前不得让它承担法定禁止力度。")
    L.append("> 若取得主管部门或司法口径明确将景区纳入「文化娱乐场所」，补充该证据后重开此两行。")
    L.append("")
    L.append("同源的 OPERATOR_POLICY 行 `dl-pet-ban` / `dl-sd-op` 不受影响，独立处理。")
    L.append("")
    return "\n".join(L)


def _temporary_section(rows: list[dict]) -> str:
    L = ["### 1.5 临时 / 试点政策：必须有期限与复核（修 §5 缺陷）", ""]
    L.append(
        "| rule_id | effective_from | effective_to | open-ended 原因 | "
        "last_verified_at | 缺口 | 建议 |"
    )
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        if r["rule_layer"] != "TEMPORARY_POLICY":
            continue
        L.append(
            f"| `{r['rule_id']}` | {_fmt(r['effective_from'])} | "
            f"{_fmt(r['effective_to'])} | {_fmt(r['open_ended_reason'])} | "
            f"{_fmt(r['last_verified_at'])} | {_fmt(r['freshness_problems'])} | "
            f"{r['proposed_decision']} |"
        )
    L.append("")
    L.append("> 这两条来自 2025-09-02 的政府通稿，试点自 2025-09-01 起，")
    L.append("> **来源未标注终止日期**，且本轮未复核至今是否仍在施行。")
    L.append("> 「没写到期」不等于「仍然有效」，因此建议 **HOLD**，")
    L.append("> 待实地/官网复核当前状态后放行。")
    L.append("")
    return "\n".join(L)


def _locator_section(rows: list[dict]) -> str:
    L = ["### 1.6 缺失溯源链的行（修 §6 缺陷）", ""]
    L.append("| rule_id | Source URL | artifact | content_hash | 快照 locator | 建议 |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        if not r["locator_gaps"] and not r["license_problems"]:
            continue
        L.append(
            f"| `{r['rule_id']}` | {_fmt(r['source_url'])} | "
            f"{'有' if r['artifact_id'] else '**无**'} | "
            f"{'有' if r['content_hash'] else '**无**'} | "
            f"{_fmt(r['snapshot_ref'])} | {r['proposed_decision']} |"
        )
    L.append("")
    L.append("**逐行缺口明细**")
    L.append("")
    for r in rows:
        gaps = [*r["locator_gaps"], *r["license_problems"]]
        if gaps:
            L.append(f"- `{r['rule_id']}`：" + "；".join(f"`{g}`" for g in gaps))
    L.append("")
    L.append("> 这些行过去靠 `EVIDENCE_TRACEABLE` 四个字通过；现在必须真的能指出")
    L.append("> 取证位置、content_hash、快照与 license 三态。补全之前建议 **HOLD**。")
    L.append("")
    return "\n".join(L)


def _exception_section(rows: list[dict]) -> str:
    """RuleException publish plan — every carve-out, bound strictly within its layer."""
    plan = exception_plan(rows)
    L = [
        "### 1.7 RuleException 发布计划（层内绑定 · RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）",
        "",
    ]
    L.append(
        "例外**不是**再发一条普通 AccessRule：同一个 zone 里同时存在「禁止」与「允许」"
        "两条普通规则，会让求解器面对两条互相冲突的同层规则。"
    )
    L.append(
        "凡本表列为 carve-out 的行，必须在**基础规则发布之后**以 `rule_exception` 形式"
        "绑定到已发布的 `access_rule`（`rule_exception.rule_id` 外键）。"
    )
    L.append("")
    L.append("**硬原则（下表由同一算法生成，违反即拒绝生成）**")
    L.append("")
    L.append("- A. LEGAL 例外只能作用于与其法律依据对应的 **LEGAL** base rule。")
    L.append("- B. OPERATOR_POLICY carve-out **不得**直接 override 更高层的 LEGAL 规则。")
    L.append("- C. 运营方政策写「允许」**不构成**法律禁令的例外。")
    L.append(
        "- D. Resolver precedence 始终保持 **LEGAL > OPERATOR_POLICY**"
        "（例外只在自身层内替换 base）。"
    )
    L.append(
        "- E. 每条 RuleException 保留 source / layer / mandatory_level / "
        "source_scope_exact / subject_scope_normalized / normalization_type。"
    )
    L.append("")
    L.append(
        "| 例外行 | 层 | effect | 精确 scope | 归一化 | 强制级 | "
        "绑定基础规则（层） | base 裁决 | 可执行 | 说明 |"
    )
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for entry in plan:
        if entry["bases"]:
            bound = "、".join(f"`{b['rule_id']}`（{b['layer']}）" for b in entry["bases"])
            verdicts = "、".join(b["decision"] for b in entry["bases"])
        else:
            bound = "（无同层禁令——不构成冲突）"
            verdicts = "—"
        note = (
            "作为 `rule_exception` 发布"
            if entry["mode"] == "rule_exception"
            else "记录为运营方佐证豁免"
        )
        if entry["blocked_reasons"]:
            note = "**本批不发布**：" + "；".join(entry["blocked_reasons"])
        L.append(
            f"| `{entry['rule_id']}` | {entry['layer']} | {entry['effect']} | "
            f"`{_fmt(entry['subject_scope_normalized'])}` | `{entry['normalization_type']}` | "
            f"`{_fmt(entry['mandatory_level'])}` | {bound} | {verdicts} | "
            f"{'✅' if entry['executable'] else '❌'} | {note} |"
        )
    if not plan:
        L.append("| — | — | — | — | — | — | — | — | — | — |")
    L.append("")

    cross_layer = [e for e in plan if any(not b["same_layer"] for b in e["bases"])]
    recovered = [e for e in plan if e["cross_layer_dropped"]]
    held_with_exec = [
        e
        for e in plan
        if e["executable"] and any(b["decision"] != "RECOMMEND_APPROVE" for b in e["bases"])
    ]
    legal_ops = [e for e in plan if e["layer"] == "LEGAL"]
    operator_ops = [e for e in plan if e["layer"] == "OPERATOR_POLICY"]
    separation = not cross_layer and all(b["same_layer"] for e in plan for b in e["bases"])
    L.append("**层间隔离核对**")
    L.append("")
    L.append("| 检查项 | 结果 |")
    L.append("|---|---|")
    L.append(f"| 跨层绑定（cross-layer override，实际绑定表内） | **{len(cross_layer)}** |")
    L.append(f"| HOLD 基础规则收到「可执行例外」 | **{len(held_with_exec)}** |")
    L.append(f"| Legal / Operator 例外分离 | **{'PASS' if separation else 'FAIL'}** |")
    recovered_ids = "、".join(f"`{e['rule_id']}`" for e in recovered)
    L.append(
        f"| 旧算法遗留的跨层绑定（已丢弃，仅记录） | **{len(recovered)}**"
        f"{'（' + recovered_ids + '）' if recovered_ids else ''} |"
    )
    L.append(f"| 例外行分布 | LEGAL {len(legal_ops)} 条 · OPERATOR_POLICY {len(operator_ops)} 条 |")
    L.append("")
    L.append(
        "> 层内判定口径：LEGAL 例外只绑定**同场所的 LEGAL 禁令**（`dog` 覆盖 `guide_dog`）；"
        "OPERATOR_POLICY 豁免只绑定**同一份运营方文件**里的禁令（禁令与豁免出自同一 `source_id`，"
        "如「禁止宠物入内。导盲犬可随时进入酒店。」）。跨层绑定一律丢弃并在此计数。"
    )
    L.append("")
    L.append("**发布顺序（不可颠倒）**：")
    L.append("")
    L.append("1. 先发布基础禁止规则，取得 `access_rule.id`；")
    L.append("2. 再按上表逐条创建 `rule_exception`，把 scope / normalization /")
    L.append("   normative_effect / holder_scope 一并写入")
    L.append("   （否则又是一次 ADR-025 字段在写入时丢失）；")
    L.append(
        "3. 最后校验 resolver：`guide_dog` 命中例外得 allowed，其余命中基础规则得 prohibited，"
        "且 LEGAL 禁令不因任何运营方豁免而放宽。"
    )
    L.append("")
    L.append("> 本包只给出计划与绑定关系，**不执行**上述任何一步。")
    L.append("")
    return "\n".join(L)


def _render_row(i: int, r: dict) -> str:
    L: list[str] = []
    a = L.append
    a(f"### FINAL-{i:02d} · `{r['rule_id']}` — {r['place_name']}")
    a("")
    a(f"- **candidate_id**：`{r['candidate_id']}`")
    a(
        f"- **place**：{r['place_name']}（`{r['place_key']}`，place_type=`{r['place_type']}`）"
        f" · zone：{_fmt(r['zone_name'])} · {_fmt(r['indoor_outdoor'])}"
    )
    a(f"- **action / effect**：{r['action']} · **{EFFECT_ZH.get(r['effect'], r['effect'])}**")
    a(
        f"- **coarse animal_scope**：`{r['animal_scope']}`"
        f"（{SCOPE_ZH.get(r['animal_scope'], r['animal_scope'])}）"
    )
    a(f"- **source_scope_exact（来源原话）**：{_fmt(r['source_scope_exact'])}")
    a(f"- **subject_scope_normalized（精确 scope）**：`{_fmt(r['subject_scope_normalized'])}`")
    a(
        f"- **normalization_type**：`{r['normalization_type']}`"
        f"（{NORM_ZH.get(r['normalization_type'], _fmt(r['normalization_type']))}）"
    )
    a(
        f"- **normative_effect**：`{_fmt(r['normative_effect'])}`"
        f" · **holder_scope**：`{_fmt(r['holder_scope'])}`"
    )
    ml = r.get("mandatory_level") or "—"
    a(
        f"- **RuleLayer**：`{r['rule_layer']}`"
        f"（{LAYER_ZH.get(r['rule_layer'], r['rule_layer'])}）"
        f" · **MandatoryLevel**：`{ml}`（{MANDATORY_ZH.get(ml, ml)}）"
    )
    claimed = r["evidence_strength_claimed"]
    derived = r["evidence_strength"]
    warn = (
        " · ⚠️ 登记表声称 `" + str(claimed) + "` 与证据链推导不一致"
        if r["evidence_strength_conflict"]
        else ""
    )
    a(
        f"- **EvidenceStrength**：`{derived}`（{STRENGTH_ZH.get(derived, derived)}）"
        f" · chain directness：`{_fmt(r['directness'])}`"
        f"（{DIRECTNESS_ZH.get(r['directness'] or '', '')}）" + warn
    )
    a(
        f"- **Source issuer**：{_fmt(r['issuer'])}"
        f" · 核验：`{_fmt(r['issuer_verification'])}`"
        f"（{VERIFY_ZH.get(r['issuer_verification'] or '', '')}）"
    )
    a(f"- **Source URL（source.source_url）**：{_fmt(r['source_url'])}")
    if r["bundle_url"] and r["bundle_url"] != r["source_url"]:
        a(f"- **capture locator（bundle.source_url）**：{r['bundle_url']}  ⚠️ 与 source 不一致")
    a(
        f"- **artifact**：id=`{_fmt(r['artifact_id'])}` · type=`{_fmt(r['artifact_type'])}`"
        f" · content_hash=`{_fmt(r['content_hash'])}`"
    )
    a(
        f"- **snapshot_ref**：{_fmt(r['snapshot_ref'])}"
        f" · availability：`{_fmt(r['source_availability'])}`"
        f" · spatial：`{_fmt(r['spatial_precision'])}`"
    )
    a(f"- **关键原文引文**：> {_fmt(r['quoted_fragment'])}")
    pme = r.get("place_match_evidence")
    a(f"- **place_match_evidence**：`{_jdump(pme) if pme else '—'}`")
    a(f"- **DataLicense / SourcePolicy**：{_license_line(r)}")
    conflicts = "、".join(f"`{b}`" for b in r["carve_out_of"]) if r["carve_out_of"] else "无"
    a(f"- **conflict（同场所同层反向规则）**：{conflicts}")
    a(
        "- **exception**："
        + (
            f"需绑定为 `rule_exception` → {_fmt(r['carve_out_of'])}"
            f"（同层 {r['rule_layer']}）——不得作为普通 AccessRule 独立发布"
            if r["exception_binding_required"]
            else "不适用（本身即基础规则 / 无同层冲突）"
        )
    )
    if r.get("cross_layer_dropped"):
        dropped = "、".join(f"`{b}`" for b in r["cross_layer_dropped"])
        a(
            f"- **跨层绑定已丢弃**：{dropped} —— 旧算法曾把它指向更高层规则；"
            "按原则 B/C/D 丢弃，运营方豁免不得覆盖法规禁令"
        )
    a(
        f"- **effective_from / to**：{_fmt(r['effective_from'])} → {_fmt(r['effective_to'])}"
        f" · open-ended：{_fmt(r['open_ended_reason'])}"
    )
    a(
        f"- **freshness**：last_verified_at=`{_fmt(r['last_verified_at'])}`"
        f" · 缺口：{_fmt(r['freshness_problems'])}"
    )
    if r["applicability"]:
        ap = r["applicability"]
        a(
            f"- **applicability**：place_type=`{ap['place_type']}` → 法条类别 "
            f"{_fmt(ap['statutory_category'])} · 状态 `{ap['status']}` — {ap['note']}"
        )
    for n in r["strength_notes"]:
        a(f"- **strength note**：{n}")
    allgaps = [*r["locator_gaps"], *r["license_problems"]]
    if allgaps:
        a("- **provenance 缺口**：" + "；".join(f"`{g}`" for g in allgaps))
    a(f"- **conditions**：{_conditions(r)}")
    a(f"- **review_status**：`{r['review_status']}`")
    a(f"- **AI recommendation**：**{r['proposed_decision']}**")
    a(f"- **recommendation reason**：{r['proposed_reason']}")
    if r["reject_reason_codes"]:
        joined = "`, `".join(str(c) for c in r["reject_reason_codes"])
        a(f"- **reason codes**：`{joined}`")
    a("- **final_decision**：`________`  ← 留空，由具名评审员填写")
    a("")
    return "\n".join(L)


def render_packet(rows: list[dict]) -> str:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["proposed_decision"]].append(r)
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_PACKET_R2_FINAL.md")
    a("")
    a(f"> GOV-01 最终签署包（**{REVISION}**）· ADR-025 源忠实 scope / ADR-028 复合词拆分")
    a("> 取代 `HUMAN_REVIEW_PACKET_R2.md`（R2 与更早的 R1）")
    a(f"> 机器登记表：`docs/reality_audit/review_decisions_r2_final.json`（共 {len(rows)} 条）")
    a("> **本包逐行直接从数据库证据链生成**，不再引用手工维护的登记表字段，")
    a("> 因此不会出现「引文出自 A 页而 URL 写着 B 页」这类自相矛盾。")
    a("")
    a("## 0. 纪律（不可协商）")
    a("")
    a("1. **AI 不做最终裁决**（ADR-005 / Master Goal §0.9）。本包只提供事实与建议。")
    a("2. `final_decision` / `reviewer` / `reviewed_at` **全部保持空白**，由具名人类评审员填写。")
    a("3. 未获签署，任何候选不得批准，更不得 Publish。")
    a("4. 弱证据（`search_snippet` / `social_lead`）不得批准（ADR-021）。")
    a("5. 来源写「导盲犬」只能是 `guide_dog`；写「军警犬」拆为 `police_dog` +")
    a("   `military_working_dog`，**不得**扩张到其他 working dog（ADR-028）。")
    a("6. 本包**不执行发布**。")
    a("")
    a("### 0.1 决策词表（唯一来源：`scripts/human_decisions.py`）")
    a("")
    a("| 值 | 含义 |")
    a("|---|---|")
    for d in HUMAN_DECISIONS:
        a(f"| `{d}` | {LABELS_ZH[d]} |")
    a("")
    a("> 速填表、登记表与发布工具共用同一词表，**不存在别名**。")
    a("> 请勿使用 APPROVE / REJECT 等写法。")
    a("")
    a("## 1. 建议分布")
    a("")
    a("| 建议 | 条数 |")
    a("|---|---|")
    for dec in ("RECOMMEND_REJECT", "RECOMMEND_HOLD", "RECOMMEND_APPROVE"):
        a(f"| `{dec}` | **{len(by[dec])}** |")
    a(f"| **合计** | **{len(rows)}** |")
    a("")
    a(_library_split_section(rows))
    a(_fairmont_section())
    a(_gc_other_keep_section())
    a(_disney_section(rows))
    a(_temporary_section(rows))
    a(_locator_section(rows))
    a(_exception_section(rows))
    a("## 3. 逐条")
    a("")
    for i, r in enumerate(rows, 1):
        a(_render_row(i, r))
    a("---")
    a("")
    a(
        "\n".join(
            [
                "## 4. 签署与后续",
                "",
                "1. 在 `HUMAN_REVIEW_DECISIONS_R2_FINAL.json` 填写 `reviewer`（具名）、",
                "   `reviewed_at`（ISO 8601）与逐条 `final_decision`。",
                f"   `final_decision` 只能取：{' / '.join(f'`{d}`' for d in HUMAN_DECISIONS)}。",
                "2. 回填机器登记表 `docs/reality_audit/review_decisions_r2_final.json`。",
                "3. 校验：`python scripts/publish_reviewed_r1.py --dry-run`",
                "   （自动读取**最新**登记表）应返回 `signed=true`。",
                "4. **发布后**按 §1.7 的顺序创建 `rule_exception`；",
                "   先行的基础规则必须已 published。本包不执行该步骤，仅规定顺序。",
                "",
            ]
        )
    )
    return "\n".join(L) + "\n"


def render_quick_table(rows: list[dict]) -> str:
    L: list[str] = []
    a = L.append
    a("# HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md")
    a("")
    a(f"> GOV-01 最终速填表 · 一行一条（{REVISION}）· 取代 R2 / R1 速填表。")
    a("> 「我的决定」只能填下列四个值之一，**不存在别名**：")
    a("> " + " ｜ ".join(f"`{d}` = {LABELS_ZH[d]}" for d in HUMAN_DECISIONS))
    a("")
    a("**图例**：🔴 建议拒绝 ｜ 🟠 建议挂起 ｜ ⚖️ 法定强制 ｜ 🦮 导盲犬精确 scope ｜")
    a("🐕‍🦺 军警犬拆分 ｜ 📎 需绑定 rule_exception")
    a("")
    a("| 编号 | Place | Rule | 来源原话 | 精确 scope | 归一化 | Evidence | AI建议 | 我的决定 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        flags = ""
        if r["proposed_decision"] == "RECOMMEND_REJECT":
            flags = "🔴"
        elif r["proposed_decision"] == "RECOMMEND_HOLD":
            flags = "🟠"
        if r["rule_layer"] == "LEGAL" and r.get("mandatory_level") == "mandatory":
            flags += "⚖️"
        if r["subject_scope_normalized"] == "guide_dog":
            flags += "🦮"
        if r["normalization_type"] == "compound_term_split":
            flags += "🐕‍🦺"
        if r["exception_binding_required"]:
            flags += "📎"
        a(
            f"| **FINAL-{i:02d}** {flags} | {r['place_name']} | `{r['rule_id']}`"
            f"：{EFFECT_ZH.get(r['effect'], r['effect'])} | {_fmt(r['source_scope_exact'])}"
            f" | `{_fmt(r['subject_scope_normalized'])}` | `{r['normalization_type']}`"
            f" | {r['evidence_strength']} | {r['proposed_decision']} |  |"
        )
    a("")
    a("## 签署")
    a("")
    a("| 字段 | 值 |")
    a("|---|---|")
    a("| reviewer（具名） |  |")
    a("| reviewer_role |  |")
    a("| reviewed_at |  |")
    a("| 确认 ADR-025 源忠实 scope（不再泛化为 service_dog） | ☐ 是 ☐ 否 |")
    a("| 确认 ADR-028 复合词「军警犬」拆分不扩张到其他 working dog | ☐ 是 ☐ 否 |")
    a("| 确认例外按 §1.7 绑定为 rule_exception（不用反向 AccessRule 表达） | ☐ 是 ☐ 否 |")
    a("| 首批批准条数（≤ `--max-approve`） |  |")
    a("| 签名 |  |")
    a("")
    return "\n".join(L) + "\n"


#: Fields that belong to the human, not to the generator.
SIGN_OFF_FIELDS = ("final_decision", "reviewer", "reviewed_at", "review_note")


def preserve_signature(fresh: list[dict], previous_rows: list[dict] | None) -> list[dict]:
    """Carry an already-recorded human signature onto regenerated rows.

    Regenerating the artefacts must never un-sign the register. The packet is
    rebuilt from the database so the *machine proposal* stays honest, but a
    human decision is an immutable review event (POST_SIGNATURE_PUBLISHER_CLOSURE_R1
    §1) — "rebuild the row" must not quietly erase it. Until this existed,
    re-running the generator after a sign-off silently produced a blank sheet,
    and the human decision was simply gone.

    Keyed by ``candidate_id``, never by position: a row that moves cannot hand its
    signature to a different rule.
    """
    if not previous_rows:
        return fresh
    previous = {str(r.get("candidate_id")): r for r in previous_rows}
    for row in fresh:
        old = previous.get(str(row.get("candidate_id")))
        if not old:
            continue
        for field in SIGN_OFF_FIELDS:
            if old.get(field):
                row[field] = old[field]
    return fresh


def _read_existing(path: Path) -> dict:
    """The previous artefact, or {} when there is nothing to preserve."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def render_decisions(rows: list[dict], previous: dict | None = None) -> str:
    previous = previous or {}
    doc = {
        "revision": REVISION,
        "reviewer": previous.get("reviewer") or "",
        "reviewed_at": previous.get("reviewed_at") or "",
        "human_decisions": list(HUMAN_DECISIONS),
        "decisions": preserve_signature(
            [
                {"candidate_id": r["candidate_id"], "final_decision": "", "review_note": ""}
                for r in rows
            ],
            previous.get("decisions"),
        ),
    }
    # This file lives at the repo root, so Prettier owns it (unlike the register,
    # which .prettierignore exempts). Emit its canonical 2-space form directly
    # rather than leaving the frontend format gate to reformat a sign-off sheet.
    return json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n"


def main() -> int:
    rows = build_rows()
    plan = exception_plan(rows)
    write_registry(rows)
    PACKET.write_text(render_packet(rows), encoding="utf-8", newline="\n")
    QUICK_TABLE.write_text(render_quick_table(rows), encoding="utf-8", newline="\n")
    DECISIONS.write_text(
        render_decisions(rows, previous=_read_existing(DECISIONS)), encoding="utf-8", newline="\n"
    )

    counts = Counter(r["proposed_decision"] for r in rows)
    print(
        _jdump(
            {
                "revision": REVISION,
                "written": [str(REGISTRY_FINAL), str(PACKET), str(QUICK_TABLE), str(DECISIONS)],
                "total": len(rows),
                "recommendations": {
                    "APPROVE": counts["RECOMMEND_APPROVE"],
                    "HOLD": counts["RECOMMEND_HOLD"],
                    "REJECT": counts["RECOMMEND_REJECT"],
                },
                "all_decisions_blank": all(not r.get("final_decision") for r in rows),
                "all_reviewers_blank": all(not r.get("reviewer") for r in rows),
                "all_reviewed_at_blank": all(not r.get("reviewed_at") for r in rows),
                "rows_needing_an_exception": sum(
                    1 for r in rows if r["exception_binding_required"]
                ),
                "exception_plan_entries": len(plan),
                "cross_layer_bindings": sum(
                    1 for e in plan if any(not b["same_layer"] for b in e["bases"])
                ),
                "cross_layer_dropped": sum(1 for e in plan if e["cross_layer_dropped"]),
                "provenance_gaps": sum(
                    1 for r in rows if r["locator_gaps"] or r["license_problems"]
                ),
                "strength_conflicts": sum(1 for r in rows if r["evidence_strength_conflict"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
