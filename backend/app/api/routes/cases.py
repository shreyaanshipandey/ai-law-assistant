import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.case import CaseAnalysis
from app.models.user import User
from app.schemas.case import CaseAnalysisOut, CaseAnalysisRequest
from app.services.ai_service import predict_bns_sections

router = APIRouter(prefix="/cases", tags=["Case Analysis"])


@router.post("/analyze", response_model=CaseAnalysisOut, status_code=status.HTTP_201_CREATED)
async def analyze_case(
    payload: CaseAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prediction = await predict_bns_sections(payload.case_summary, payload.case_category)

    record = CaseAnalysis(
        user_id=current_user.id,
        case_summary=payload.case_summary,
        case_category=payload.case_category,
        predicted_sections=prediction.model_dump(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return CaseAnalysisOut.model_validate(record)


@router.get("/history", response_model=list[CaseAnalysisOut])
async def get_case_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseAnalysis)
        .where(CaseAnalysis.user_id == current_user.id)
        .order_by(CaseAnalysis.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseAnalysisOut)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseAnalysis).where(CaseAnalysis.id == case_id, CaseAnalysis.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case analysis not found.")
    return CaseAnalysisOut.model_validate(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CaseAnalysis).where(CaseAnalysis.id == case_id, CaseAnalysis.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case analysis not found.")
    await db.delete(case)
    await db.commit()
