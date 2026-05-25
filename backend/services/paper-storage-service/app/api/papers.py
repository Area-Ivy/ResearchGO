"""
Paper storage API.
"""
import asyncio
import io
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pdfplumber
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from jose import jwt
from minio.error import S3Error
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.paper import Paper
from app.schemas.paper import (
    DeleteResponse,
    PaperInfo,
    PaperListResponse,
    PaperStatusResponse,
    PaperUploadResponse,
)
from app.utils.auth_client import get_current_user
from app.utils.minio_client import MINIO_BUCKET, ensure_bucket_exists, get_minio_client

load_dotenv()

logger = logging.getLogger(__name__)

VECTOR_SEARCH_SERVICE_URL = os.getenv("VECTOR_SEARCH_SERVICE_URL", "http://localhost:8004")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
INDEX_REQUEST_TIMEOUT_SECONDS = float(os.getenv("INDEX_REQUEST_TIMEOUT_SECONDS", "600"))
STALE_INDEXING_MINUTES = int(os.getenv("STALE_INDEXING_MINUTES", "30"))

router = APIRouter(prefix="/api/papers", tags=["paper-storage"])


def _serialize_datetime(value):
    return value.isoformat() if value else None


def _truncate_error(message: str, limit: int = 500) -> str:
    if not message:
        return "Unknown indexing error."
    message = str(message).strip()
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def _build_status_message(paper: Paper) -> str:
    status_value = paper.processing_status or "uploaded"
    if status_value == "indexed":
        chunks = paper.chunks_created or 0
        return f"File uploaded and indexed successfully. {chunks} chunks are ready for search."
    if status_value == "failed":
        return paper.processing_error or "File uploaded, but indexing failed."
    if status_value == "indexing":
        return "File uploaded successfully. Vector indexing is in progress."
    return "File uploaded successfully."


def _set_paper_status(object_name: str, **fields):
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.object_name == object_name).first()
        if not paper:
            logger.warning("Paper not found when updating status: %s", object_name)
            return

        for key, value in fields.items():
            setattr(paper, key, value)

        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update paper status for %s: %s", object_name, exc)
    finally:
        db.close()


def _mark_stale_indexing_jobs(db: Session):
    cutoff = datetime.utcnow() - timedelta(minutes=STALE_INDEXING_MINUTES)
    stale_papers = db.query(Paper).filter(
        Paper.processing_status == "indexing",
        Paper.updated_at < cutoff,
    ).all()

    if not stale_papers:
        return

    for paper in stale_papers:
        paper.processing_status = "failed"
        paper.processing_error = (
            f"Indexing did not finish within {STALE_INDEXING_MINUTES} minutes. "
            "Please retry the upload."
        )
        paper.chunks_created = 0
        paper.indexed_at = None

    db.commit()
    logger.warning("Marked %s stale indexing jobs as failed", len(stale_papers))


def _create_upload_response(paper: Paper) -> PaperUploadResponse:
    return PaperUploadResponse(
        object_name=paper.object_name,
        original_name=paper.original_name,
        size=paper.file_size,
        content_type=paper.content_type,
        upload_time=_serialize_datetime(paper.created_at) or datetime.utcnow().isoformat(),
        processing_status=paper.processing_status,
        processing_error=paper.processing_error,
        chunks_created=paper.chunks_created or 0,
        indexed_at=_serialize_datetime(paper.indexed_at),
        message=_build_status_message(paper),
    )


def _build_status_response(paper: Paper) -> PaperStatusResponse:
    return PaperStatusResponse(
        object_name=paper.object_name,
        processing_status=paper.processing_status,
        processing_error=paper.processing_error,
        chunks_created=paper.chunks_created or 0,
        indexed_at=_serialize_datetime(paper.indexed_at),
        updated_at=_serialize_datetime(paper.updated_at),
    )


def _build_internal_token(current_user: dict) -> str:
    expire = datetime.utcnow() + timedelta(hours=1)
    token_data = {
        "sub": current_user["username"],
        "user_id": current_user["id"],
        "is_active": current_user.get("is_active", True),
        "is_superuser": current_user.get("is_superuser", False),
        "exp": expire,
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


async def extract_text_from_pdf(pdf_data: bytes, max_pages: int = 50) -> str:
    """Extract plain text from the first pages of a PDF."""
    try:
        text_content = []
        pdf_stream = io.BytesIO(pdf_data)

        with pdfplumber.open(pdf_stream) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages)
            logger.info("Extracting text from %s pages (total=%s)", pages_to_extract, total_pages)

            for index, page in enumerate(pdf.pages[:pages_to_extract], start=1):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {index} ---\n{text}")
                except Exception as exc:
                    logger.warning("Failed to extract text from page %s: %s", index, exc)

        full_text = "\n\n".join(text_content).strip()
        logger.info("Extracted %s characters from PDF", len(full_text))
        return full_text
    except Exception as exc:
        logger.error("Error extracting text from PDF: %s", exc)
        return ""


async def index_paper_to_vector_db(
    paper_id: str,
    title: str,
    file_name: str,
    pdf_content: bytes,
    token: str,
    use_structured: bool = True,
):
    """Index a paper into the vector search service."""
    try:
        logger.info("Starting paper indexing: %s (structured=%s)", paper_id, use_structured)
        _set_paper_status(
            paper_id,
            processing_status="indexing",
            processing_error=None,
            chunks_created=0,
            indexed_at=None,
        )

        content = await extract_text_from_pdf(pdf_content)
        if not content or len(content) < 100:
            _set_paper_status(
                paper_id,
                processing_status="failed",
                processing_error="Insufficient text extracted from PDF for indexing.",
                chunks_created=0,
                indexed_at=None,
            )
            logger.warning("Skipping indexing for %s because extracted text is insufficient", paper_id)
            return

        index_request = {
            "paper_id": paper_id,
            "title": title,
            "file_name": file_name,
            "max_chunk_size": 1000,
        }

        if use_structured:
            try:
                from app.utils.paper_structure_parser import get_paper_structure_parser
                from app.utils.recursive_semantic_chunker import chunk_structured_paper

                parser = get_paper_structure_parser()
                paper_structure = await parser.parse_structure(content)
                structured_chunks = chunk_structured_paper(
                    paper_structure=paper_structure.to_dict(),
                    max_chunk_size=1000,
                    min_chunk_size=100,
                    chunk_overlap=100,
                )

                index_request["structured_chunks"] = [
                    {
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "section_type": chunk.section_type,
                        "section_title": chunk.section_title,
                        "subsection_title": chunk.subsection_title,
                        "hierarchy_path": chunk.hierarchy_path,
                        "char_count": chunk.char_count,
                        "is_complete_section": chunk.is_complete_section,
                        "metadata": {},
                    }
                    for chunk in structured_chunks
                ]
                index_request["paper_metadata"] = {
                    "title": paper_structure.title,
                    "authors": paper_structure.authors,
                    "abstract": (paper_structure.abstract or "")[:500],
                    "references_count": paper_structure.references_count,
                }
                logger.info("Structured parsing succeeded for %s with %s chunks", paper_id, len(structured_chunks))
            except Exception as exc:
                logger.warning("Structured parsing failed for %s, falling back to plain content: %s", paper_id, exc)
                index_request["content"] = content
        else:
            index_request["content"] = content

        if "structured_chunks" not in index_request:
            index_request["content"] = content

        try:
            async with httpx.AsyncClient(timeout=INDEX_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/index",
                    json=index_request,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.TimeoutException as exc:
            if use_structured:
                logger.warning(
                    "Structured indexing timed out for %s after %ss, retrying in plain mode",
                    paper_id,
                    INDEX_REQUEST_TIMEOUT_SECONDS,
                )
                await index_paper_to_vector_db(
                    paper_id=paper_id,
                    title=title,
                    file_name=file_name,
                    pdf_content=pdf_content,
                    token=token,
                    use_structured=False,
                )
                return

            _set_paper_status(
                paper_id,
                processing_status="failed",
                processing_error=(
                    f"Vector indexing timed out after {int(INDEX_REQUEST_TIMEOUT_SECONDS)} seconds. "
                    "Please retry later."
                ),
                chunks_created=0,
                indexed_at=None,
            )
            logger.error("Plain indexing timed out for %s: %s", paper_id, exc)
            return

        if response.status_code != 200:
            error_message = _truncate_error(response.text or f"Indexing failed with HTTP {response.status_code}")
            _set_paper_status(
                paper_id,
                processing_status="failed",
                processing_error=error_message,
                chunks_created=0,
                indexed_at=None,
            )
            logger.error("Failed to index paper %s: %s - %s", paper_id, response.status_code, response.text)
            return

        result = response.json()
        chunks_created = int(result.get("chunks_created", 0) or 0)
        _set_paper_status(
            paper_id,
            processing_status="indexed",
            processing_error=None,
            chunks_created=chunks_created,
            indexed_at=datetime.utcnow(),
        )
        logger.info("Paper indexed successfully: %s (chunks=%s)", paper_id, chunks_created)
    except Exception as exc:
        logger.exception("Error indexing paper %s", paper_id)
        _set_paper_status(
            paper_id,
            processing_status="failed",
            processing_error=_truncate_error(str(exc)),
            chunks_created=0,
            indexed_at=None,
        )


def _run_indexing_task(*, paper_id: str, title: str, file_name: str, pdf_content: bytes, token: str):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            index_paper_to_vector_db(
                paper_id=paper_id,
                title=title,
                file_name=file_name,
                pdf_content=pdf_content,
                token=token,
            )
        )
    except Exception:
        logger.exception("Background indexing failed for %s", paper_id)
        _set_paper_status(
            paper_id,
            processing_status="failed",
            processing_error="Background indexing task crashed unexpectedly.",
            chunks_created=0,
            indexed_at=None,
        )
    finally:
        asyncio.set_event_loop(None)
        loop.close()


@router.post("/upload", response_model=PaperUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a PDF and start background vector indexing."""
    file_name = file.filename or "paper.pdf"
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported.")

    try:
        file_content = await file.read()
        file_size = len(file_content)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        object_name = f"{timestamp}_{file_name}"

        client = get_minio_client()
        ensure_bucket_exists(client, MINIO_BUCKET)
        client.put_object(
            MINIO_BUCKET,
            object_name,
            io.BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or "application/pdf",
        )

        paper = Paper(
            user_id=current_user["id"],
            object_name=object_name,
            original_name=file_name,
            file_size=file_size,
            content_type=file.content_type or "application/pdf",
            title=Path(file_name).stem,
            processing_status="indexing",
            processing_error=None,
            chunks_created=0,
            indexed_at=None,
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        temp_token = _build_internal_token(current_user)
        background_tasks.add_task(
            _run_indexing_task,
            paper_id=object_name,
            title=paper.title or Path(file_name).stem,
            file_name=file_name,
            pdf_content=file_content,
            token=temp_token,
        )

        logger.info("Paper uploaded: %s by user %s", object_name, current_user["id"])
        return _create_upload_response(paper)
    except S3Error as exc:
        logger.error("MinIO error while uploading %s: %s", file_name, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to object storage: {exc}",
        )
    except Exception as exc:
        logger.exception("Upload error for %s", file_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload paper: {exc}",
        )


@router.get("/list", response_model=PaperListResponse)
async def list_papers(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's papers."""
    try:
        _mark_stale_indexing_jobs(db)
        query = db.query(Paper).filter(Paper.user_id == current_user["id"])
        total = query.count()
        papers = query.order_by(Paper.created_at.desc()).offset(skip).limit(limit).all()
        return PaperListResponse(total=total, papers=[PaperInfo.from_orm(paper) for paper in papers])
    except Exception as exc:
        logger.exception("List papers error for user %s", current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list papers: {exc}",
        )


@router.get("/status/{object_name}", response_model=PaperStatusResponse)
async def get_paper_status(
    object_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the latest indexing status for one uploaded paper."""
    _mark_stale_indexing_jobs(db)
    paper = db.query(Paper).filter(
        Paper.object_name == object_name,
        Paper.user_id == current_user["id"],
    ).first()

    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")

    return _build_status_response(paper)


@router.get("/download/{object_name}")
async def download_paper(
    object_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a paper file."""
    paper = db.query(Paper).filter(
        Paper.object_name == object_name,
        Paper.user_id == current_user["id"],
    ).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")

    try:
        client = get_minio_client()
        response = client.get_object(MINIO_BUCKET, object_name)
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type=paper.content_type,
            headers={"Content-Disposition": f'attachment; filename="{paper.original_name}"'},
        )
    except S3Error as exc:
        logger.error("MinIO download error for %s: %s", object_name, exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper file not found.")
    except Exception as exc:
        logger.exception("Download error for %s", object_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download paper: {exc}",
        )


@router.get("/view/{object_name}")
async def view_paper(
    object_name: str,
    token: str = None,
    db: Session = Depends(get_db),
):
    """Return the PDF bytes for inline viewing."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token.")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception as exc:
        logger.error("Token verification failed while viewing paper %s: %s", object_name, exc)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token.")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token.")

    paper = db.query(Paper).filter(
        Paper.object_name == object_name,
        Paper.user_id == user_id,
    ).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")

    try:
        client = get_minio_client()
        response = client.get_object(MINIO_BUCKET, object_name)
        pdf_data = response.read()
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{paper.original_name}"'},
        )
    except S3Error as exc:
        logger.error("MinIO view error for %s: %s", object_name, exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper file not found.")
    except Exception as exc:
        logger.exception("View error for %s", object_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view paper: {exc}",
        )


@router.delete("/delete/{object_name}", response_model=DeleteResponse)
async def delete_paper(
    object_name: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a paper, including vector index and object storage."""
    paper = db.query(Paper).filter(
        Paper.object_name == object_name,
        Paper.user_id == current_user["id"],
    ).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found.")

    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if token:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                vector_response = await client.delete(
                    f"{VECTOR_SEARCH_SERVICE_URL}/api/vector/delete/{object_name}",
                    headers={"Authorization": f"Bearer {token}"},
                )
            if vector_response.status_code == 200:
                logger.info("Deleted vector index for %s", object_name)
            else:
                logger.warning("Vector delete returned %s for %s", vector_response.status_code, object_name)
        except Exception as exc:
            logger.warning("Failed to delete vectors for %s: %s", object_name, exc)

    try:
        minio_client = get_minio_client()
        minio_client.remove_object(MINIO_BUCKET, object_name)
        db.delete(paper)
        db.commit()
        logger.info("Paper deleted: %s by user %s", object_name, current_user["id"])
        return DeleteResponse(
            success=True,
            message="Paper deleted successfully.",
            object_name=object_name,
        )
    except S3Error as exc:
        logger.error("MinIO delete error for %s: %s", object_name, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete paper file.")
    except Exception as exc:
        logger.exception("Delete error for %s", object_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete paper: {exc}",
        )


@router.get("/health")
async def health_check():
    """Health check."""
    return {"status": "healthy", "service": "paper-storage"}
