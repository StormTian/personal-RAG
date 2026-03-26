"""File management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from typing import List

from ...services.file_service import FileService
from ...services.history_service import HistoryService
from ..deps import get_rag_engine

router = APIRouter()


# Response Models
class FileInfoResponse(BaseModel):
    """File information response model."""
    file_id: str
    original_name: str
    stored_name: str
    file_path: str
    file_size: int
    file_size_human: str
    file_type: str
    created_at: str
    metadata: dict = Field(default_factory=dict)


class FileListResponse(BaseModel):
    """File list response model."""
    files: List[FileInfoResponse]
    total: int


class DeleteFileResponse(BaseModel):
    """Delete file response model."""
    success: bool
    message: str
    filename: str


# Dependencies
def get_file_service() -> FileService:
    """Get or create file service instance."""
    return FileService()


def get_history_service() -> HistoryService:
    """Get or create history service instance."""
    return HistoryService()


@router.get("/api/files", response_model=FileListResponse)
async def list_files(
    file_service: FileService = Depends(get_file_service)
) -> FileListResponse:
    """
    List all uploaded files.
    
    Returns a list of all files in the document library with metadata.
    """
    files = file_service.list_files()
    
    return FileListResponse(
        files=[FileInfoResponse(**f.to_dict()) for f in files],
        total=len(files)
    )


@router.delete("/api/files/{filename}", response_model=DeleteFileResponse)
async def delete_file(
    filename: str = Path(..., description="Name of the file to delete"),
    file_service: FileService = Depends(get_file_service),
    history_service: HistoryService = Depends(get_history_service),
    rag_engine=Depends(get_rag_engine)
) -> DeleteFileResponse:
    """
    Delete a file by filename.
    
    - Deletes the file from storage
    - Updates history record status to 'deleted'
    - Automatically reloads the RAG index
    
    Args:
        filename: The filename to delete (original_name or stored_name)
        
    Returns:
        DeleteFileResponse with success status
        
    Raises:
        HTTPException: If file not found or deletion fails
    """
    # Find file by listing and matching filename
    files = file_service.list_files()
    target_file = None
    target_file_id = None
    
    for file_id, file_info in file_service._files.items():
        if (file_info.original_name == filename or 
            file_info.stored_name == filename):
            target_file = file_info
            target_file_id = file_id
            break
    
    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}"
        )
    
    try:
        # 1. Delete physical file and metadata
        file_service.delete_file(target_file_id)
        
        # 2. Update history record status if exists
        history_record = history_service.get_record_by_filename(filename)
        if history_record:
            from ...models.upload_history import UploadStatus
            history_service.update_record_status(
                record_id=history_record.id,
                status=UploadStatus.DELETED,
                error_message=None
            )
        
        # 3. Auto-reload RAG index
        await rag_engine.reload_async()
        
        return DeleteFileResponse(
            success=True,
            message=f"File '{filename}' deleted successfully and index reloaded",
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
