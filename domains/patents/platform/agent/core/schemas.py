from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProcessingStage(str, Enum):
    PENDING = 'pending'
    PARSING = 'parsing'
    PARSING_VERIFIED = 'parsing_verified'
    ANALYSIS = 'analysis'
    ANALYSIS_VERIFIED = 'analysis_verified'
    DRAFTING = 'drafting'
    FINALIZED = 'finalized'

class VerificationStatus(str, Enum):
    WAITING = 'waiting'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    NEEDS_MODIFICATION = 'needs_modification'

class HumanFeedback(BaseModel):
    stage: ProcessingStage
    status: VerificationStatus
    comments: str
    modified_content: dict[str, Any] | None = None
    timestamp: float

class PatentPacket(BaseModel):
    doc_id: str
    file_path: str
    current_stage: ProcessingStage = ProcessingStage.PENDING

    # Perception Layer Data
    parsed_data: dict[str, Any] | None = None

    # Cognition Layer Data
    # For novelty/creativity (Art 22)
    prior_art_refs: list[dict[str, Any] = Field(default_factory=list)
    novelty_analysis: str | None = None

    # For formal checks (Art 26, Rule 20)
    formal_defects: list[str] = Field(default_factory=list)

    # Decisions needing human input
    decisions_needed: list[dict[str, Any] = Field(default_factory=list)

    # Execution Layer Data
    draft_content: dict[str, str] | None = None # e.g., {'claims': '...', 'description': '...'}

    # History
    feedback_history: list[HumanFeedback] = Field(default_factory=list)
