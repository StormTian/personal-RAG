from fastapi import APIRouter, Query, Depends
from typing import List
from datetime import datetime

from ...services.history_service import HistoryService

router = APIRouter()


@router.get("/api/upload-history")
async def get_upload_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    history_service: HistoryService = Depends()
):
    """
    获取上传历史记录列表
    
    Args:
        limit: 每页记录数，默认50，最大100
        offset: 偏移量，默认0
        
    Returns:
        上传历史记录列表和总数
    """
    records, total = history_service.get_recent_records(limit=limit, offset=offset)
    
    formatted_records = []
    for record in records:
        formatted_records.append({
            "id": record.id,
            "original_name": record.original_name,
            "saved_name": record.saved_name,
            "size": record.file_size,
            "type": record.file_type,
            "status": record.status.value.lower(),
            "uploaded_at": record.uploaded_at.isoformat() if record.uploaded_at else None,
            "auto_reloaded": record.auto_reloaded,
            "chunks_created": record.chunks_created
        })
    
    return {
        "status": "ok",
        "records": formatted_records,
        "total": total
    }
