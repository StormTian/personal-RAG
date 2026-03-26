"""File upload API routes for RAG system."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ...services.file_service import FileService
from ...services.history_service import HistoryService
from ...models.upload_history import UploadRecord, UploadStatus
from ..deps import get_rag_engine, get_client_id, get_security
from ...exceptions.file_exceptions import (
    InvalidFileTypeError,
    FileTooLargeError,
    FileSecurityError,
    FileProcessingError,
    DuplicateFileError,
)
from ...exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency injection for services
def get_file_service() -> FileService:
    """Get or create file service instance."""
    return FileService()


def get_history_service() -> HistoryService:
    """Get or create history service instance."""
    return HistoryService()


@router.post("/api/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload"),
    auto_reload: bool = Form(True, description="Automatically reload RAG index after upload"),
    api_key: Optional[str] = Depends(get_security),
    client_id: str = Depends(get_client_id),
    file_service: FileService = Depends(get_file_service),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    Upload a file to the document library.
    
    Args:
        file: File to upload (multipart/form-data)
        auto_reload: Whether to automatically reload the RAG index after upload
        
    Returns:
        JSON response with upload status and file information
    """
    # Validate request
    security = get_security()
    security.validate_request(api_key, client_id)
    
    # Validate file exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create upload record
    record = UploadRecord(
        original_name=file.filename,
        saved_name="",
        file_path="",
        file_size=0,
        file_type="",
        status=UploadStatus.PENDING,
        uploaded_by=client_id,
        uploaded_at=datetime.now(),
    )
    
    try:
        # Save file
        logger.info(f"Uploading file: {file.filename}")
        file_info = file_service.save_uploaded_file(
            file=file.file,
            filename=file.filename,
            metadata={
                "uploaded_by": client_id,
                "uploaded_at": datetime.now().isoformat(),
            },
        )
        
        # Update record with file info
        record.saved_name = file_info.stored_name
        record.file_path = file_info.file_path
        record.file_size = file_info.file_size
        record.file_type = file_info.file_type
        record.status = UploadStatus.SUCCESS
        
        # Save to history
        record_id = history_service.add_record(record)
        record.id = record_id
        
        logger.info(f"File uploaded successfully: {file_info.stored_name}")
        
    except InvalidFileTypeError as e:
        record.status = UploadStatus.FAILED
        record.error_message = str(e)
        history_service.add_record(record)
        raise HTTPException(status_code=415, detail=str(e))
        
    except FileTooLargeError as e:
        record.status = UploadStatus.FAILED
        record.error_message = str(e)
        history_service.add_record(record)
        raise HTTPException(status_code=413, detail=str(e))
        
    except (FileSecurityError, DuplicateFileError) as e:
        record.status = UploadStatus.FAILED
        record.error_message = str(e)
        history_service.add_record(record)
        raise HTTPException(status_code=400, detail=str(e))
        
    except FileProcessingError as e:
        record.status = UploadStatus.FAILED
        record.error_message = str(e)
        history_service.add_record(record)
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        record.status = UploadStatus.FAILED
        record.error_message = f"Unexpected error: {str(e)}"
        history_service.add_record(record)
        logger.exception(f"Failed to upload file: {file.filename}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    # Reload RAG index if requested
    reloaded = False
    library_stats = None
    
    if auto_reload:
        try:
            logger.info("Reloading RAG index...")
            rag = get_rag_engine()
            await rag.reload_async()
            reloaded = True
            library_stats = rag.stats()
            
            # Update record
            record.auto_reloaded = True
            history_service.update_record_status(
                record_id=record.id,
                status=UploadStatus.SUCCESS,
            )
            logger.info("RAG index reloaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to reload RAG index: {e}")
            record.auto_reloaded = False
            history_service.update_record_status(
                record_id=record.id,
                status=UploadStatus.SUCCESS,
            )
    
    # Build response
    response = {
        "status": "ok",
        "message": "File uploaded successfully",
        "file": {
            "original_name": record.original_name,
            "saved_name": record.saved_name,
            "path": record.file_path,
            "size": record.file_size,
            "type": record.file_type,
        },
        "reloaded": reloaded,
    }
    
    if library_stats:
        response["library_stats"] = {
            "documents": library_stats.get("documents", 0),
            "chunks": library_stats.get("chunks", 0),
            "supported_formats": library_stats.get("supported_formats", []),
        }
    
    return response


@router.get("/api/upload/history")
async def get_upload_history(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    api_key: Optional[str] = Depends(get_security),
    client_id: str = Depends(get_client_id),
    history_service: HistoryService = Depends(get_history_service),
):
    """
    Get upload history.
    
    Args:
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of upload records
    """
    # Validate request
    security = get_security()
    security.validate_request(api_key, client_id)
    
    records, total = history_service.get_recent_records(limit=limit, offset=offset)
    
    return {
        "records": [r.to_dict() for r in records],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
