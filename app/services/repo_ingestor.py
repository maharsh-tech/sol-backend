"""
RepoSense Ingestor — orchestrates GitHub fetch → chunk → embed → store.

Reuses existing chunker, embedder, and vectorstore modules.
"""

import logging
from typing import Optional

from app.services.github_fetcher import get_repo_tree, get_file_content
from app.services.chunker import chunk_text
from app.embeddings.embedder import embed_texts
from app.vectorstore.store import add_chunks

logger = logging.getLogger(__name__)

# Process files in batches to avoid memory spikes
BATCH_SIZE = 20


def ingest_repo(
    owner: str, repo: str, token: Optional[str] = None
) -> dict:
    """
    Fetch all relevant files from a GitHub repo, chunk, embed, and store them.

    Returns:
        dict with keys: files_processed, chunks_stored, skipped
    """
    full_repo = f"{owner}/{repo}"
    logger.info("Starting ingestion for %s", full_repo)

    # 1. Get filtered file tree
    file_paths = get_repo_tree(owner, repo, token)
    logger.info("Found %d indexable files in %s", len(file_paths), full_repo)

    files_processed = 0
    chunks_stored = 0
    skipped = 0

    # 2. Process files in batches
    for i in range(0, len(file_paths), BATCH_SIZE):
        batch_paths = file_paths[i : i + BATCH_SIZE]
        all_chunks: list[dict] = []

        for path in batch_paths:
            content = get_file_content(owner, repo, path, token)
            if content is None:
                skipped += 1
                continue

            # Skip empty files
            if not content.strip():
                skipped += 1
                continue

            metadata = {
                "document_name": path,
                "repo": full_repo,
                "source_type": "github",
            }

            chunks = chunk_text(content, metadata)
            if chunks:
                all_chunks.extend(chunks)
                files_processed += 1
            else:
                skipped += 1

        # 3. Embed & store this batch
        if all_chunks:
            texts = [c["text"] for c in all_chunks]
            metas = [c["metadata"] for c in all_chunks]
            embeddings = embed_texts(texts)
            added = add_chunks(texts, embeddings, metas)
            chunks_stored += added

    logger.info(
        "Ingestion complete: %d files, %d chunks, %d skipped",
        files_processed, chunks_stored, skipped,
    )

    return {
        "files_processed": files_processed,
        "chunks_stored": chunks_stored,
        "skipped": skipped,
    }
