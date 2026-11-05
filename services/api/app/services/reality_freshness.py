"""Shared Reality freshness mapping.

Kept outside API and contribution modules so domain services never import API
routers. This prevents a dependency cycle while preserving one freshness
definition for both publication and contribution paths.
"""

from datetime import datetime

from app.models.enums import RealityFreshnessState
from app.services.reality_summary import freshness_for


def freshness_state(observed_at: datetime | None) -> RealityFreshnessState | None:
    """Map an observed timestamp onto the persisted Reality freshness enum."""
    if observed_at is None:
        return None
    return RealityFreshnessState(freshness_for(observed_at).lower())
