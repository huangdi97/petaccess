"""Unclassified evidence is not upgraded to an invented credibility level."""

from types import SimpleNamespace

from app.models.enums import EvidenceStrength
from app.services.evidence_service import strength_for_artifact


def test_unknown_collector_keeps_unclassified_strength() -> None:
    artifact = SimpleNamespace(collector_type="UnclassifiedExternalCollector")
    source = SimpleNamespace(source_type="external_web_reference", directness="secondary")
    assert strength_for_artifact(artifact, source) is None


def test_on_site_capture_retains_documented_capture_strength() -> None:
    artifact = SimpleNamespace(collector_type="OnsiteEvidenceCollector")
    source = SimpleNamespace(source_type="onsite_signage", directness="direct")
    assert strength_for_artifact(artifact, source) == EvidenceStrength.PRIMARY_CAPTURED.value


def test_user_source_cannot_turn_into_primary_authority() -> None:
    artifact = SimpleNamespace(collector_type="ManualVerificationCollector")
    source = SimpleNamespace(source_type="ordinary_user", directness="secondary")
    assert strength_for_artifact(artifact, source) == EvidenceStrength.USER_SUBMITTED.value
