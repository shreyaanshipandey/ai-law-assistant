"""
File upload validation and text-extraction helpers, shared by the
petition-scanner and CSV-uploader endpoints.
"""
import io
import os
import uuid

import pdfplumber
from docx import Document
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_PETITION_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CSV_EXTENSIONS = {".csv"}


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]


async def validate_and_read_upload(
    file: UploadFile, allowed_extensions: set[str]
) -> bytes:
    """
    Enforces max size (settings.MAX_UPLOAD_SIZE_MB) and allowed extension.
    Reads and returns the raw bytes (stream is consumed).
    """
    ext = _get_extension(file.filename or "")
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    contents = await file.read()
    size_bytes = len(contents)
    if size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit "
                   f"(received {size_bytes / (1024*1024):.2f}MB).",
        )
    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    await file.seek(0)
    return contents


def save_upload_to_disk(contents: bytes, original_filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = _get_extension(original_filename)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(contents)
    return path


def extract_text_from_bytes(contents: bytes, filename: str) -> str:
    """Extracts plain text from PDF, DOCX, or TXT byte content."""
    ext = _get_extension(filename)

    if ext == ".txt":
        return contents.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n".join(text_parts).strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from PDF. It may be a scanned image without OCR.",
            )
        return text

    if ext == ".docx":
        doc = Document(io.BytesIO(contents))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from DOCX file.",
            )
        return text

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported extension: {ext}")
