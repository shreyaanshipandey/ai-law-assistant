import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CaseStatus(str, enum.Enum):
    PENDING = "Pending"
    ADJOURNED = "Adjourned"
    RESERVED = "Reserved for Orders"
    DISPOSED = "Disposed"
    DISMISSED = "Dismissed"


# A case is considered "ongoing" (still running in court) unless it has
# reached a final outcome (Disposed / Dismissed).
ONGOING_STATUSES = {CaseStatus.PENDING, CaseStatus.ADJOURNED, CaseStatus.RESERVED}


class CaseRecord(Base):
    """A user-tracked court case for the Digital Case Management module."""

    __tablename__ = "case_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    case_number: Mapped[str] = mapped_column(String(120), nullable=False)
    court_name: Mapped[str] = mapped_column(String(255), nullable=False)
    petitioner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    respondent_name: Mapped[str] = mapped_column(String(255), nullable=False)

    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_hearing_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status"), default=CaseStatus.PENDING, nullable=False
    )
    stage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="case_records")

    @property
    def is_ongoing(self) -> bool:
        """True if the case is still running in court (not disposed/dismissed)."""
        return self.status in ONGOING_STATUSES