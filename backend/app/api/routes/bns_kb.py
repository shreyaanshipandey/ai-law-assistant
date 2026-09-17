import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from app.api.deps import get_current_active_admin
from app.services.rag_service import knowledge_base
from app.utils.validators import ALLOWED_CSV_EXTENSIONS, validate_and_read_upload

router = APIRouter(prefix="/bns-kb", tags=["BNS Knowledge Base"])


@router.get("/sections")
async def list_sections():
    """Public: returns the current in-memory BNS section list (for search UI)."""
    return {"count": len(knowledge_base.df), "sections": knowledge_base.as_records()}


@router.post("/upload", dependencies=[Depends(get_current_active_admin)])
async def upload_bns_csv(file: UploadFile = File(...)):
    """
    Admin-only: replace/extend the BNS knowledge base with a new CSV.
    Required columns: section_number, section_title, description, punishment,
    imprisonment_term, bailable, cognizable.
    """
    contents = await validate_and_read_upload(file, ALLOWED_CSV_EXTENSIONS)
    try:
        df = pd.read_csv(io.BytesIO(contents))
        count = knowledge_base.reload_from_dataframe(df)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not parse CSV: {exc}")

    return {"message": "BNS knowledge base updated successfully.", "sections_loaded": count}
