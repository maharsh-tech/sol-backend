import os
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.parsers.pdf_parser import parse_pdf
from app.parsers.excel_parser import parse_excel
from app.parsers.pptx_parser import parse_pptx
from app.services.chunker import chunk_text
from app.embeddings.embedder import embed_texts
from app.vectorstore.store import add_chunks
from app.services.rag_pipeline import ask_question
from app.schemas.models import (
    AskRequest,
    AskResponse,
    UploadResponse,
    HealthResponse,
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

    uploaded_names: list[str] = []
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

        all_chunks: list[dict] = []
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
    result = await ask_question(body.question)
    return AskResponse(**result)
