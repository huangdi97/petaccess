"""Pet profile endpoints (design #5, #31 /pets)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import PetProfile, User
from app.schemas.common import Page
from app.schemas.pets import PetIn, PetOut

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("", response_model=Page[PetOut])
def list_my_pets(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Page[PetOut]:
    rows = db.scalars(
        select(PetProfile).where(PetProfile.user_id == user.id).order_by(PetProfile.created_at)
    ).all()
    return Page(items=rows, total=len(rows), limit=len(rows), offset=0)


@router.post("", response_model=PetOut, status_code=201)
def create_pet(
    body: PetIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> PetProfile:
    pet = PetProfile(user_id=user.id, **body.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.patch("/{pet_id}", response_model=PetOut)
def update_pet(
    pet_id: str,
    body: PetIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PetProfile:
    pet = db.get(PetProfile, pet_id)
    if pet is None or pet.user_id != user.id:
        raise NotFound("宠物不存在")
    for k, v in body.model_dump().items():
        setattr(pet, k, v)
    db.commit()
    db.refresh(pet)
    return pet


@router.delete("/{pet_id}", status_code=204)
def delete_pet(
    pet_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    pet = db.get(PetProfile, pet_id)
    if pet is None or pet.user_id != user.id:
        raise NotFound("宠物不存在")
    db.delete(pet)
    db.commit()
