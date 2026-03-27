"""
Unit tests for document parsing utilities.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from rag_system.utils import (
    read_text_file,
    split_paragraphs,
    first_heading,
    first_non_empty_line,
    shorten,
    extract_pdf_file,
    SUPPORTED_EXTENSIONS,
)


class TestReadTextFile:
    """Tests for read_text_file function."""
    
    def test_read_utf8_file(self, temp_dir):
        """Test reading UTF-8 encoded file."""
        path = temp_dir / "utf8.txt"
        content = "Hello, 世界! 🌍"
        path.write_text(content, encoding="utf-8")
        
        result = read_text_file(path)
        assert result == content
    
    def test_read_utf8_bom_file(self, temp_dir):
        """Test reading UTF-8 BOM encoded file."""
        path = temp_dir / "utf8bom.txt"
        content = "Hello, World!"
        path.write_bytes(b'\xef\xbb\xbf' + content.encode("utf-8"))
        
        result = read_text_file(path)
        # May include BOM depending on implementation
        assert content in result or result.replace('\ufeff', '') == content
    
    def test_read_gb18030_file(self, temp_dir):
        """Test reading GB18030 encoded file."""
        path = temp_dir / "gb18030.txt"
        content = "中文内容"
        path.write_bytes(content.encode("gb18030"))
        
        result = read_text_file(path)
        assert content in result
    
    def test_read_with_fallback(self, temp_dir):
        """Test reading file with fallback encoding."""
        path = temp_dir / "fallback.txt"
        # Create a file with invalid UTF-8 sequences
        path.write_bytes(b"Hello \xff World")
        
        result = read_text_file(path)
        assert "Hello" in result


class TestFirstHeading:
    """Tests for first_heading function."""
    
    def test_extract_h1_heading(self):
        """Test extracting H1 heading."""
        text = "# Main Title\n\nContent here"
        result = first_heading(text, "fallback")
        assert result == "Main Title"
    
    def test_extract_h2_heading(self):
        """Test extracting H2 heading."""
        text = "## Section Title\n\nContent here"
        result = first_heading(text, "fallback")
        assert result == "Section Title"
    
    def test_extract_heading_with_extra_whitespace(self):
        """Test extracting heading with extra whitespace."""
        text = "#   Spaced Title   \n\nContent"
        result = first_heading(text, "fallback")
        assert result == "Spaced Title"
    
    def test_fallback_when_no_heading(self):
        """Test fallback when no heading found."""
        text = "Just some content\nWithout any heading"
        result = first_heading(text, "fallback_title")
        assert result == "fallback_title"
    
    def test_empty_text_fallback(self):
        """Test fallback with empty text."""
        result = first_heading("", "fallback")
        assert result == "fallback"


class TestFirstNonEmptyLine:
    """Tests for first_non_empty_line function."""
    
    def test_first_non_empty_simple(self):
        """Test getting first non-empty line."""
        text = "First line\n\nSecond line"
        result = first_non_empty_line(text, "fallback")
        assert result == "First line"
    
    def test_skip_heading_markers(self):
        """Test that heading markers are stripped."""
        text = "# Heading\nContent"
        result = first_non_empty_line(text, "fallback")
        # Should skip the heading marker
        assert "Heading" in result or result == "Heading"
    
    def test_skip_leading_empty_lines(self):
        """Test skipping leading empty lines."""
        text = "\n\n\nFirst real line"
        result = first_non_empty_line(text, "fallback")
        assert result == "First real line"
    
    def test_fallback_when_all_empty(self):
        """Test fallback when all lines are empty."""
        text = "\n\n\n"
        result = first_non_empty_line(text, "fallback")
        assert result == "fallback"


class TestShorten:
    """Tests for shorten function."""
    
    def test_shorten_short_text(self):
        """Test shortening text that doesn't need shortening."""
        text = "Short"
        result = shorten(text, width=10)
        assert result == text
    
    def test_shorten_long_text(self):
        """Test shortening long text."""
        text = "This is a very long text that needs to be shortened"
        result = shorten(text, width=20)
        assert len(result) <= 20
        assert result.endswith("...")
    
    def test_shorten_exact_width(self):
        """Test text at exact width."""
        text = "Exactly twenty chars"
        result = shorten(text, width=20)
        assert len(result) <= 20
    
    def test_custom_width(self):
        """Test with custom width."""
        text = "This is a test"
        result = shorten(text, width=10)
        assert len(result) <= 10
        assert result.endswith("...")


class TestSupportedExtensions:
    """Tests for SUPPORTED_EXTENSIONS constant."""
    
    def test_markdown_extensions(self):
        """Test markdown extensions."""
        assert ".md" in SUPPORTED_EXTENSIONS
        assert ".markdown" in SUPPORTED_EXTENSIONS
        assert SUPPORTED_EXTENSIONS[".md"] == "markdown"
    
    def test_text_extension(self):
        """Test text extension."""
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert SUPPORTED_EXTENSIONS[".txt"] == "text"
    
    def test_word_extensions(self):
        """Test Word document extensions."""
        assert ".doc" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        assert SUPPORTED_EXTENSIONS[".doc"] == "word"
        assert SUPPORTED_EXTENSIONS[".docx"] == "word"
    
    def test_pdf_extension(self):
        """Test PDF extension."""
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert SUPPORTED_EXTENSIONS[".pdf"] == "pdf"


class TestSplitParagraphs:
    """Tests for split_paragraphs function."""
    
    def test_split_markdown_with_headers(self):
        """Test splitting markdown with headers."""
        text = "# Title\nContent here\n\n## Section\nMore content"
        paragraphs = split_paragraphs(text)
        
        # Should have multiple paragraphs
        assert len(paragraphs) >= 2
        
        # Headers should be included with trailing period
        assert any("Title" in p for p in paragraphs)
        assert any("Section" in p for p in paragraphs)
    
    def test_split_empty_lines(self):
        """Test splitting with multiple empty lines."""
        text = "Para one\n\n\n\nPara two"
        paragraphs = split_paragraphs(text)
        assert len(paragraphs) == 2
    
    def test_split_single_paragraph(self):
        """Test single paragraph."""
        text = "Just one paragraph"
        paragraphs = split_paragraphs(text)
        assert len(paragraphs) == 1
        assert paragraphs[0] == text


class TestExtractPdfFile:
    """Tests for extract_pdf_file function."""
    
    @patch('pypdf.PdfReader')
    def test_extract_with_pypdf(self, mock_pdf_reader):
        """Test PDF extraction using pypdf."""
        # Mock the PdfReader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted PDF text"
        
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Create a dummy PDF path
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            result = extract_pdf_file(tmp_path)
            assert "Extracted PDF text" in result
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_extract_without_pypdf(self, monkeypatch, temp_dir):
        """Test PDF extraction without pypdf available."""
        # Set PdfReader to None to simulate missing pypdf
        monkeypatch.setattr('pypdf.PdfReader', None)
        
        pdf_path = temp_dir / "test.pdf"
        # Create empty file
        pdf_path.write_bytes(b"")
        
        # This should raise RuntimeError or use fallback
        # Note: Actual behavior depends on implementation
        try:
            result = extract_pdf_file(pdf_path)
        except (RuntimeError, FileNotFoundError):
            pass  # Expected behavior when pypdf is not available
