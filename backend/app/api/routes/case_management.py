import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.case_management import CaseRecord
from app.models.user import User
from app.schemas.case_management import CaseRecordCreate, CaseRecordOut, CaseRecordUpdate

router = APIRouter(prefix="/case-management", tags=["Digital Case Management"])


@router.post("/", response_model=CaseRecordOut, status_code=status.HTTP_201_CREATED)
async def add_case(
    payload: CaseRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = CaseRecord(user_id=current_user.id, **payload.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return CaseRecordOut.model_validate(record)


@router.get("/", response_model=list[CaseRecordOut])
async def list_cases(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseRecord)
        .where(CaseRecord.user_id == current_user.id)
        .order_by(CaseRecord.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseRecordOut)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseRecord).where(CaseRecord.id == case_id, CaseRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case record not found.")
    return CaseRecordOut.model_validate(record)


@router.patch("/{case_id}", response_model=CaseRecordOut)
async def update_case(
    case_id: uuid.UUID,
    payload: CaseRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseRecord).where(CaseRecord.id == case_id, CaseRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case record not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)
    return CaseRecordOut.model_validate(record)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseRecord).where(CaseRecord.id == case_id, CaseRecord.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case record not found.")
    await db.delete(record)
    await db.commit()