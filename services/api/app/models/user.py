"""User and PetProfile entities (design #5)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, PkMixin, TimestampMixin

from .enums import PetSpecies, ServiceRole, UserRole, UserStatus

if TYPE_CHECKING:
    from .observation import ObservationClaim


class User(Base, PkMixin, TimestampMixin):
    __tablename__ = "user"

    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(32), default=UserRole.USER, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        String(32), default=UserStatus.ACTIVE, nullable=False
    )

    pets: Mapped[list["PetProfile"]] = relationship(back_populates="user")
    observation_claims: Mapped[list["ObservationClaim"]] = relationship(back_populates="user")


class PetProfile(Base, PkMixin, TimestampMixin):
    """Rule-matching input, not a social profile (design #5.1)."""

    __tablename__ = "pet_profile"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    species: Mapped[PetSpecies] = mapped_column(String(32), nullable=False)
    breed_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    breed_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    shoulder_height_cm: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    service_role: Mapped[ServiceRole] = mapped_column(
        String(32), default=ServiceRole.NONE, nullable=False
    )
    registration_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vaccination_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="pets")
