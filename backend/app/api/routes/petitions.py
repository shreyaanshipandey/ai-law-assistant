import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.case import Petition
from app.models.user import User
from app.schemas.petition import PetitionGenerateRequest, PetitionOut
from app.services.ai_service import generate_petition_draft, scan_petition
from app.services.document_service import petition_to_docx, petition_to_pdf
from app.utils.validators import (
    ALLOWED_PETITION_EXTENSIONS,
    extract_text_from_bytes,
    save_upload_to_disk,
    validate_and_read_upload,
)

router = APIRouter(prefix="/petitions", tags=["Petitions"])


@router.post("/generate", response_model=PetitionOut, status_code=status.HTTP_201_CREATED)
async def generate_petition(
    payload: PetitionGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    draft_text = await generate_petition_draft(
        petitioner_name=payload.petitioner_name,
        respondent_name=payload.respondent_name,
        court_name=payload.court_name,
        case_summary=payload.case_summary,
        relief_sought=payload.relief_sought,
        applicable_sections=payload.applicable_sections,
    )
    title = f"Petition - {payload.petitioner_name} vs {payload.respondent_name}"

    record = Petition(
        user_id=current_user.id,
        title=title,
        source_type="generated",
        content_text=draft_text,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return PetitionOut.model_validate(record)


@router.get("/{petition_id}/download")
async def download_petition(
    petition_id: uuid.UUID,
    file_format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Petition).where(Petition.id == petition_id, Petition.user_id == current_user.id)
    )
    petition = result.scalar_one_or_none()
    if not petition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition not found.")

    if file_format not in {"pdf", "docx"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file_format must be 'pdf' or 'docx'.")

    if file_format == "pdf":
        path = petition_to_pdf(petition.title, petition.content_text)
        media_type = "application/pdf"
    else:
        path = petition_to_docx(petition.title, petition.content_text)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(path, media_type=media_type, filename=f"{petition.title}.{file_format}")


@router.post("/scan", response_model=PetitionOut, status_code=status.HTTP_201_CREATED)
async def upload_and_scan_petition(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Secure upload (<=10MB, .pdf/.docx/.txt only) → text extraction →
    AI validity scan for missing points, weak arguments, formatting flaws.
    """
    contents = await validate_and_read_upload(file, ALLOWED_PETITION_EXTENSIONS)
    extracted_text = extract_text_from_bytes(contents, file.filename or "upload.txt")
    stored_path = save_upload_to_disk(contents, file.filename or "upload.txt")

    scan_result = await scan_petition(extracted_text)

    record = Petition(
        user_id=current_user.id,
        title=file.filename or "Uploaded Petition",
        source_type="uploaded",
        content_text=extracted_text,
        file_path=stored_path,
        scan_result=scan_result.model_dump(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return PetitionOut.model_validate(record)


@router.get("/history", response_model=list[PetitionOut])
async def petition_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Petition).where(Petition.user_id == current_user.id).order_by(Petition.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{petition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_petition(
    petition_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Petition).where(Petition.id == petition_id, Petition.user_id == current_user.id)
    )
    petition = result.scalar_one_or_none()
    if not petition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition not found.")
    await db.delete(petition)
    await db.commit()
