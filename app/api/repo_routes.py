"""
RepoSense API routes — POST /repo/analyze
"""

import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.repo_ingestor import ingest_repo

router = APIRouter()


class RepoAnalyzeRequest(BaseModel):
    repo_url: str
    token: Optional[str] = None


class RepoAnalyzeResponse(BaseModel):
    success: bool
    repo: str
    files_processed: int
    chunks_stored: int
    message: str


def _parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    # Supports: https://github.com/owner/repo, https://github.com/owner/repo.git, etc.
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(
            "Invalid GitHub URL. Expected format: https://github.com/owner/repo"
        )
    owner = match.group(1)
    repo = match.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


@router.post("/analyze", response_model=RepoAnalyzeResponse)
async def analyze_repo(body: RepoAnalyzeRequest):
    """Index a GitHub repository for Q&A via RepoSense."""
    try:
        owner, repo = _parse_github_url(body.repo_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = ingest_repo(owner, repo, body.token or None)
    except ValueError as exc:
        # GitHub API errors (404, 401, 403) surface here
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Repository indexing failed: {str(exc)}",
        ) from exc

    return RepoAnalyzeResponse(
        success=True,
        repo=f"{owner}/{repo}",
        files_processed=result["files_processed"],
        chunks_stored=result["chunks_stored"],
        message="Repository indexed successfully. You can now ask questions about this codebase.",
    )


# ── Repo-scoped Q&A ─────────────────────────────────────────────────────────


class RepoAskRequest(BaseModel):
    question: str
    repo: str  # e.g. "maharsh-tech/RAG-API"


@router.post("/ask")
async def repo_ask(body: RepoAskRequest):
    """Answer a question using only chunks from the specified repository."""
    from app.embeddings.embedder import embed_query
    from app.vectorstore.store import get_collection
    from app.llm.openrouter_client import generate_answer
    from app.core.config import TOP_K

    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    query_embedding = embed_query(body.question)
    collection = get_collection()

    # Query with repo filter so only this repo's chunks are returned
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        where={"repo": body.repo},
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer": f"No indexed content found for repository '{body.repo}'. Please analyze the repository first.",
            "citations": [],
            "confidence": "low",
        }

    # Build context with file paths
    parts = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        filepath = meta.get("document_name", "unknown")
        parts.append(f"[Source {i}: {filepath}]\n{doc}")
    context = "\n\n".join(parts)

    system_prompt = f"""You are a code assistant. Answer the user's question using ONLY the code/file context provided below from the GitHub repository '{body.repo}'. Reference specific file paths when relevant. If the answer is not in the context, say so.

Context:
{context}

Question:
{body.question}"""

    answer = generate_answer(system_prompt, body.question)

    # Build citations with file paths
    citations = []
    for doc, meta in zip(documents, metadatas):
        citations.append({
            "document_name": meta.get("document_name", "unknown"),
            "page": meta.get("repo", body.repo),
            "snippet": doc[:200].strip(),
        })

    # Confidence
    if not distances:
        confidence = "low"
    else:
        strong = sum(1 for d in distances if d < 0.5)
        confidence = "high" if strong >= 2 else ("medium" if strong >= 1 else "low")

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
    }
