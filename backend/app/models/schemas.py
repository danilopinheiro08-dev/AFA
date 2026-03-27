# API Schemas
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    intent: str
    sources: list[str]
    chunks_used: int
    guardrail_code: Optional[str] = None


class UploadResponse(BaseModel):
    file: str
    rows: int
    chunks: int
    columns: list[str]
    message: str


class ReportRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: str
    file_name: str
    analysis: str
    sources: list[str]
    chunks_used: int
    generated_at: str
    download_url: str


class AlertItem(BaseModel):
    id: str
    title: str
    description: str
    risk_level: str  # "high", "medium", "low"
    source_file: str
    detected_at: str
    recommended_action: str


class CollectionStats(BaseModel):
    total_chunks: int
    collection: str
    csv_files: list[str]
