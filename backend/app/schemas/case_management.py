import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case_management import CaseStatus


class CaseRecordCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=120)
    court_name: str = Field(min_length=1, max_length=255)
    petitioner_name: str = Field(min_length=1, max_length=255)
    respondent_name: str = Field(min_length=1, max_length=255)
    filing_date: date | None = None
    next_hearing_date: date | None = None
    status: CaseStatus = CaseStatus.PENDING
    stage_notes: str | None = None


class CaseRecordUpdate(BaseModel):
    next_hearing_date: date | None = None
    status: CaseStatus | None = None
    stage_notes: str | None = None


class CaseRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_number: str
    court_name: str
    petitioner_name: str
    respondent_name: str
    filing_date: date | None
    next_hearing_date: date | None
    status: CaseStatus
    stage_notes: str | None
    is_ongoing: bool
    created_at: datetime
    updated_at: datetime