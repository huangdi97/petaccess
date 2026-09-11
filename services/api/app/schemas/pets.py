"""Pet profile DTOs (design #5)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PetSpecies, ServiceRole


class PetIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    species: PetSpecies
    breed_text: str | None = Field(default=None, max_length=120)
    breed_id: str | None = Field(default=None, max_length=64)
    weight_kg: float | None = Field(default=None, gt=0, le=300)
    shoulder_height_cm: float | None = Field(default=None, gt=0, le=250)
    # service_role is user-declared only; never derived from photos (design #19)
    service_role: ServiceRole = ServiceRole.NONE
    registration_status: str | None = Field(default=None, max_length=32)
    vaccination_status: str | None = Field(default=None, max_length=32)
    avatar_url: str | None = Field(default=None, max_length=512)


PetUpdate = PetIn


class PetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    species: PetSpecies
    breed_text: str | None
    weight_kg: float | None
    shoulder_height_cm: float | None
    service_role: ServiceRole
    registration_status: str | None
    vaccination_status: str | None
    avatar_url: str | None
    created_at: datetime
