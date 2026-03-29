"""File upload API routes for RAG system."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, Request, BackgroundTasks
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


async def _reload_rag_index(record_id: int, history_service: HistoryService):
    """后台任务：重新加载RAG索引"""
    try:
        logger.info("后台重新加载RAG索引...")
        rag = get_rag_engine()
        await rag.reload_async()
        
        # 更新记录状态
        history_service.update_record_status(
            record_id=record_id,
            status=UploadStatus.SUCCESS,
        )
        logger.info("RAG索引重新加载完成")
    except Exception as e:
        logger.error(f"后台重新加载RAG索引失败: {e}")
        # 记录失败但不影响上传结果
        history_service.update_record_status(
            record_id=record_id,
            status=UploadStatus.SUCCESS,
        )


@router.post("/api/upload")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
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
    
    # Reload RAG index if requested (后台异步执行)
    if auto_reload:
        # 添加后台任务，不阻塞响应
        background_tasks.add_task(_reload_rag_index, record.id, history_service)
        logger.info(f"文件上传成功，RAG索引重新加载已加入后台任务队列: {file_info.stored_name}")
    
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
        "reloading": auto_reload,
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
