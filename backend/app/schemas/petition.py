import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PetitionGenerateRequest(BaseModel):
    petitioner_name: str
    respondent_name: str
    court_name: str
    case_summary: str = Field(min_length=20)
    relief_sought: str
    applicable_sections: list[str] | None = None


class PetitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source_type: str
    content_text: str
    file_path: str | None
    scan_result: dict | None
    created_at: datetime


class PetitionScanIssue(BaseModel):
    category: str  # "Missing Point" | "Weak Argument" | "Formatting" | "Legal Citation"
    severity: str  # "Low" | "Medium" | "High"
    description: str
    suggestion: str


class PetitionScanResult(BaseModel):
    validity_score: int = Field(ge=0, le=100)
    summary: str
    issues: list[PetitionScanIssue]
    missing_sections_detected: list[str]
    strengths: list[str]
