from pydantic import BaseModel
from typing import List


class AskRequest(BaseModel):
    question: str


class Citation(BaseModel):
    document_name: str
    page: int | str
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: str


class UploadResponse(BaseModel):
    message: str
    documents: list[str]
    total_chunks: int


class HealthResponse(BaseModel):
    status: str
    service: str


# ── Meeting Intelligence ──────────────────────────────────────────────────

class MeetingActionItem(BaseModel):
    task: str
    owner: str
    deadline: str
    priority: str  # High | Medium | Low


class MeetingAnalysisResponse(BaseModel):
    transcript: str
    summary: str
    actionItems: List[MeetingActionItem]
    keyDecisions: List[str]


class MeetingAnalyzeRequest(BaseModel):
    """Used when the caller provides a raw transcript (no audio file)."""
    transcript: str


class MeetingSlackRequest(BaseModel):
    summary: str
    actionItems: List[MeetingActionItem]
    keyDecisions: List[str]
