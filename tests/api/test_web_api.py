"""
API tests for web_app endpoints.
"""

import pytest
import json
from pathlib import Path
from http import HTTPStatus
from unittest.mock import Mock, patch


class TestWebAppHelpers:
    """Tests for web_app helper functions."""
    
    def test_load_asset_existing_file(self, temp_dir):
        """Test loading existing asset."""
        from web_app import load_asset
        
        asset_path = temp_dir / "test.txt"
        content = "Test content"
        asset_path.write_text(content, encoding="utf-8")
        
        result = load_asset(asset_path)
        assert result == content.encode("utf-8")
    
    def test_load_asset_missing_file(self):
        """Test loading missing asset."""
        from web_app import load_asset
        
        result = load_asset(Path("/nonexistent/path"), fallback="default")
        assert result == b"default"
    
    def test_parse_top_k_valid(self):
        """Test parsing valid top_k values."""
        from web_app import parse_top_k
        
        assert parse_top_k("3") == 3
        assert parse_top_k("5") == 5
        assert parse_top_k("1") == 1
    
    def test_parse_top_k_clamped(self):
        """Test that top_k is clamped to valid range."""
        from web_app import parse_top_k
        
        # Should clamp to minimum 1
        assert parse_top_k("0") == 1
        assert parse_top_k("-5") == 1
        
        # Should clamp to maximum 8
        assert parse_top_k("10") == 8
        assert parse_top_k("100") == 8
    
    def test_parse_top_k_invalid(self):
        """Test parsing invalid top_k values."""
        from web_app import parse_top_k
        
        with pytest.raises(ValueError):
            parse_top_k("not_a_number")
        
        with pytest.raises(ValueError):
            parse_top_k("")
    
    def test_build_answer_payload_success(self, rag_instance):
        """Test building answer payload for valid query."""
        from web_app import build_answer_payload
        
        status, data = build_answer_payload(rag_instance, "What are the features?", "3")
        
        assert status == HTTPStatus.OK
        assert "query" in data
        assert "answer_lines" in data
        assert "hits" in data
        assert data["query"] == "What are the features?"
    
    def test_build_answer_payload_empty_query(self, rag_instance):
        """Test building answer payload for empty query."""
        from web_app import build_answer_payload
        
        status, data = build_answer_payload(rag_instance, "   ", "3")
        
        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in data
        assert "请输入问题" in data["error"] or "query" in data["error"].lower()
    
    def test_build_answer_payload_invalid_top_k(self, rag_instance):
        """Test building answer payload with invalid top_k."""
        from web_app import build_answer_payload
        
        status, data = build_answer_payload(rag_instance, "test", "invalid")
        
        assert status == HTTPStatus.BAD_REQUEST
        assert "error" in data
    
    def test_build_library_payload(self, rag_instance):
        """Test building library payload."""
        from web_app import build_library_payload
        
        payload = build_library_payload(rag_instance)
        
        assert payload["status"] == "ok"
        assert "library_dir" in payload
        assert "documents" in payload
        assert "chunks" in payload
        assert "files" in payload
        assert "embedding_backend" in payload
        assert "reranker_backend" in payload
    
    def test_reload_library_success(self, rag_instance):
        """Test successful library reload."""
        from web_app import reload_library
        
        status, data = reload_library(rag_instance)
        
        assert status == HTTPStatus.OK
        assert data["status"] == "ok"
        assert "message" in data
        assert "chunks" in data
    
    def test_reload_library_error(self, rag_instance):
        """Test library reload with error."""
        from web_app import reload_library
        
        # Try to reload to a non-existent directory
        status, data = reload_library(rag_instance, Path("/nonexistent"))
        
        assert status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert "error" in data


class TestRequestHandler:
    """Tests for RAG HTTP request handler."""
    
    @pytest.fixture
    def mock_handler(self, rag_instance):
        """Create a mock request handler."""
        from web_app import RagHTTPRequestHandler, build_handler
        
        handler_class = build_handler(rag_instance)
        
        # Create a mock handler
        mock_handler = Mock(spec=handler_class)
        mock_handler.rag = rag_instance
        mock_handler.index_html = b"<html>Test</html>"
        mock_handler.app_js = b"console.log('test');"
        mock_handler.styles_css = b"body { color: red; }"
        
        return mock_handler
    
    def test_handler_attributes(self, mock_handler):
        """Test handler has required attributes."""
        assert hasattr(mock_handler, 'rag')
        assert hasattr(mock_handler, 'index_html')
        assert hasattr(mock_handler, 'app_js')
        assert hasattr(mock_handler, 'styles_css')


class TestHTTPStatusCodes:
    """Tests for HTTP status code handling."""
    
    def test_status_ok(self):
        """Test HTTP 200 OK status."""
        from http import HTTPStatus
        
        assert HTTPStatus.OK == 200
    
    def test_status_bad_request(self):
        """Test HTTP 400 Bad Request status."""
        from http import HTTPStatus
        
        assert HTTPStatus.BAD_REQUEST == 400
    
    def test_status_not_found(self):
        """Test HTTP 404 Not Found status."""
        from http import HTTPStatus
        
        assert HTTPStatus.NOT_FOUND == 404
    
    def test_status_internal_server_error(self):
        """Test HTTP 500 Internal Server Error status."""
        from http import HTTPStatus
        
        assert HTTPStatus.INTERNAL_SERVER_ERROR == 500


class TestResponseFormats:
    """Tests for response format validation."""
    
    def test_answer_response_structure(self, rag_instance):
        """Test answer response has correct structure."""
        from web_app import build_answer_payload
        
        status, data = build_answer_payload(rag_instance, "test query", "3")
        
        if status == HTTPStatus.OK:
            # Validate response structure
            assert isinstance(data, dict)
            assert "query" in data
            assert "answer_lines" in data
            assert "hits" in data
            
            # Validate hits structure
            for hit in data["hits"]:
                assert "score" in hit
                assert "retrieve_score" in hit
                assert "rerank_score" in hit
                assert "lexical_score" in hit
                assert "title_score" in hit
                assert "llm_score" in hit
                assert "source" in hit
                assert "title" in hit
                assert "text" in hit
                assert "chunk_id" in hit
    
    def test_library_response_structure(self, rag_instance):
        """Test library response has correct structure."""
        from web_app import build_library_payload
        
        data = build_library_payload(rag_instance)
        
        assert isinstance(data, dict)
        assert data["status"] == "ok"
        
        # Check required fields
        required_fields = [
            "library_dir", "documents", "chunks", "supported_formats",
            "files", "skipped", "embedding_backend", "reranker_backend",
            "retrieval_strategy", "rerank_strategy"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate files structure
        for file_info in data["files"]:
            assert "source" in file_info
            assert "title" in file_info
            assert "file_type" in file_info
            assert "chars" in file_info


@pytest.mark.asyncio
class TestAsyncAPI:
    """Tests for async API operations."""
    
    async def test_async_search(self, rag_instance):
        """Test async search operation."""
        import asyncio
        
        # Simulate async search
        def search_task():
            return rag_instance.search("test", top_k=3)
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        hits = await loop.run_in_executor(None, search_task)
        
        assert isinstance(hits, list)
    
    async def test_async_answer(self, rag_instance):
        """Test async answer operation."""
        import asyncio
        
        def answer_task():
            return rag_instance.answer("test query", top_k=3)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, answer_task)
        
        assert response.query == "test query"
        assert isinstance(response.answer_lines, list)
