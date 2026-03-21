from pydantic import BaseModel


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
