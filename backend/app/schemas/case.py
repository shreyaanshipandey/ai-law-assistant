import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CaseAnalysisRequest(BaseModel):
    case_summary: str = Field(min_length=20, description="Plain-language description of the incident/case")
    case_category: str | None = Field(
        default=None, description="Optional hint, e.g. 'theft', 'assault', 'cybercrime'"
    )


class BNSSectionHit(BaseModel):
    section_number: str
    section_title: str
    description: str
    punishment: str
    imprisonment_term: str
    bailable: str  # "Bailable" | "Non-Bailable"
    cognizable: str  # "Cognizable" | "Non-Cognizable"
    relevance_score: float = Field(ge=0, le=1)


class BNSPredictionResult(BaseModel):
    applicable_sections: list[BNSSectionHit]
    overall_severity: str  # "Low" | "Moderate" | "High" | "Severe"
    severity_explanation: str
    recommended_next_steps: list[str]
    disclaimer: str = (
        "This is an AI-generated preliminary analysis for informational purposes only "
        "and does not constitute legal advice. Please consult a licensed advocate."
    )


class CaseAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_summary: str
    case_category: str | None
    predicted_sections: dict
    created_at: datetime
