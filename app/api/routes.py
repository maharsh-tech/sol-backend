import os
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional, List

from app.core.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.parsers.pdf_parser import parse_pdf
from app.parsers.excel_parser import parse_excel
from app.parsers.pptx_parser import parse_pptx
from app.services.chunker import chunk_text
from app.embeddings.embedder import embed_texts
from app.vectorstore.store import add_chunks
from app.services.rag_pipeline import ask_question
from app.services.deepgram_service import transcribe_audio
from app.services.meeting_analysis_service import analyse_transcript
from app.services.slack_service import post_meeting_to_slack
from app.schemas.models import (
    AskRequest,
    AskResponse,
    UploadResponse,
    HealthResponse,
    MeetingAnalysisResponse,
    MeetingAnalyzeRequest,
    MeetingSlackRequest,
)

router = APIRouter()


PARSER_MAP = {
    ".pdf": parse_pdf,
    ".xlsx": parse_excel,
    ".pptx": parse_pptx,
}


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service="Knowledge Brain")


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    uploaded_names: List[str] = []
    total_chunks = 0

    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        parser = PARSER_MAP.get(ext)
        if parser is None:
            raise HTTPException(status_code=400, detail=f"No parser for {ext}")

        raw_sections = parser(str(file_path), file.filename)

        all_chunks: List[dict] = []
        for section in raw_sections:
            chunks = chunk_text(section["text"], section["metadata"])
            all_chunks.extend(chunks)

        if all_chunks:
            texts = [c["text"] for c in all_chunks]
            metas = [c["metadata"] for c in all_chunks]
            embeddings = embed_texts(texts)
            added = add_chunks(texts, embeddings, metas)
            total_chunks += added

        uploaded_names.append(file.filename)

        # Clean up uploaded file after processing
        os.remove(file_path)

    return UploadResponse(
        message="Documents processed and indexed successfully.",
        documents=uploaded_names,
        total_chunks=total_chunks,
    )


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = ask_question(body.question)
    return AskResponse(**result)


# ── Meeting Intelligence Endpoints ────────────────────────────────────────────

@router.post("/meeting/analyze", response_model=MeetingAnalysisResponse)
async def meeting_analyze(
    audio: Optional[UploadFile] = File(default=None),
    transcript: Optional[str] = Form(default=None),
):
    """
    Analyse a meeting.
    - Provide an audio file (mp3/wav/m4a) to transcribe via Deepgram first, OR
    - Provide a raw transcript string to skip transcription.
    Returns structured summary, action items and key decisions.
    """
    if audio is None and not (transcript or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Provide either an audio file or a transcript text.",
        )

    # Step 1 – Transcription (Deepgram) or use provided transcript
    if audio is not None:
        ext = Path(audio.filename).suffix.lower()
        if ext not in {".mp3", ".wav", ".m4a", ".ogg", ".webm"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {ext}. Allowed: .mp3, .wav, .m4a, .ogg, .webm",
            )
        try:
            audio_bytes = await audio.read()
            transcript_text = transcribe_audio(audio_bytes, mimetype=audio.content_type or "audio/mpeg")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Transcription failed: {str(exc)}") from exc
    else:
        transcript_text = (transcript or "").strip()

    # Step 2 – AI analysis (OpenRouter)
    try:
        analysis = analyse_transcript(transcript_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(exc)}") from exc

    return MeetingAnalysisResponse(
        transcript=transcript_text,
        summary=analysis["summary"],
        actionItems=analysis["actionItems"],
        keyDecisions=analysis["keyDecisions"],
    )


@router.post("/meeting/slack")
async def meeting_slack(body: MeetingSlackRequest):
    """Post a pre-analysed meeting summary to the configured Slack Incoming Webhook."""
    try:
        post_meeting_to_slack(
            summary=body.summary,
            action_items=[item.model_dump() for item in body.actionItems],
            key_decisions=body.keyDecisions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Slack post failed: {str(exc)}") from exc
    return {"message": "Meeting analysis posted to Slack successfully."}
