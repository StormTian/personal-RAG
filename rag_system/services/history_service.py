import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from ..models.upload_history import UploadRecord, UploadStatus


class HistoryService:
    def __init__(self, db_path: str = "data/upload_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_name TEXT NOT NULL,
                    saved_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    uploaded_by TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    auto_reloaded BOOLEAN DEFAULT 0,
                    chunks_created INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
        finally:
            conn.close()

    def add_record(self, record: UploadRecord) -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO upload_history 
                (original_name, saved_name, file_path, file_size, file_type, 
                 status, uploaded_by, error_message, auto_reloaded, chunks_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.original_name,
                record.saved_name,
                record.file_path,
                record.file_size,
                record.file_type,
                record.status.value,
                record.uploaded_by,
                record.error_message,
                int(record.auto_reloaded),
                record.chunks_created
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_recent_records(self, limit: int = 50, offset: int = 0) -> Tuple[List[UploadRecord], int]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM upload_history')
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT id, original_name, saved_name, file_path, file_size, 
                       file_type, status, uploaded_by, uploaded_at, 
                       error_message, auto_reloaded, chunks_created
                FROM upload_history
                ORDER BY uploaded_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            records = []
            for row in rows:
                records.append(UploadRecord(
                    id=row[0],
                    original_name=row[1],
                    saved_name=row[2],
                    file_path=row[3],
                    file_size=row[4],
                    file_type=row[5],
                    status=UploadStatus(row[6]),
                    uploaded_by=row[7],
                    uploaded_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    error_message=row[9],
                    auto_reloaded=bool(row[10]),
                    chunks_created=row[11]
                ))
            return records, total
        finally:
            conn.close()

    def get_record_by_filename(self, filename: str) -> Optional[UploadRecord]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, original_name, saved_name, file_path, file_size, 
                       file_type, status, uploaded_by, uploaded_at, 
                       error_message, auto_reloaded, chunks_created
                FROM upload_history
                WHERE saved_name = ? OR original_name = ?
                ORDER BY uploaded_at DESC
                LIMIT 1
            ''', (filename, filename))
            
            row = cursor.fetchone()
            if row:
                return UploadRecord(
                    id=row[0],
                    original_name=row[1],
                    saved_name=row[2],
                    file_path=row[3],
                    file_size=row[4],
                    file_type=row[5],
                    status=UploadStatus(row[6]),
                    uploaded_by=row[7],
                    uploaded_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    error_message=row[9],
                    auto_reloaded=bool(row[10]),
                    chunks_created=row[11]
                )
            return None
        finally:
            conn.close()

    def update_record_status(
        self, 
        record_id: int, 
        status: UploadStatus, 
        error_message: Optional[str] = None,
        chunks_created: Optional[int] = None
    ) -> bool:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            updates = ['status = ?']
            params = [status.value]
            
            if error_message is not None:
                updates.append('error_message = ?')
                params.append(error_message)
            
            if chunks_created is not None:
                updates.append('chunks_created = ?')
                params.append(chunks_created)
            
            params.append(record_id)
            
            cursor.execute(
                f"UPDATE upload_history SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_records_by_status(self, status: UploadStatus, limit: int = 50) -> List[UploadRecord]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, original_name, saved_name, file_path, file_size, 
                       file_type, status, uploaded_by, uploaded_at, 
                       error_message, auto_reloaded, chunks_created
                FROM upload_history
                WHERE status = ?
                ORDER BY uploaded_at DESC
                LIMIT ?
            ''', (status.value, limit))
            
            rows = cursor.fetchall()
            records = []
            for row in rows:
                records.append(UploadRecord(
                    id=row[0],
                    original_name=row[1],
                    saved_name=row[2],
                    file_path=row[3],
                    file_size=row[4],
                    file_type=row[5],
                    status=UploadStatus(row[6]),
                    uploaded_by=row[7],
                    uploaded_at=datetime.fromisoformat(row[8]) if row[8] else None,
                    error_message=row[9],
                    auto_reloaded=bool(row[10]),
                    chunks_created=row[11]
                ))
            return records
        finally:
            conn.close()
