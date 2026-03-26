"""Document loaders with registry pattern."""

import re
from pathlib import Path
from typing import List, Optional, Type

from ..core.base import DocumentLoader, SourceDocument
from ..exceptions import ProcessingError
from ..utils.file import read_text_file, extract_word_file, extract_pdf_file, SUPPORTED_EXTENSIONS


class TextDocumentLoader(DocumentLoader):
    """Loader for text-based documents (txt, md)."""
    
    supported_extensions = {".md", ".markdown", ".txt"}
    
    def can_load(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions
    
    def load(self, path: Path) -> SourceDocument:
        suffix = path.suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(suffix, "text")
        
        try:
            raw_text = read_text_file(path)
            normalized_text = self._normalize_text(raw_text)
            
            if suffix in {".md", ".markdown"}:
                title = self._extract_title_from_markdown(normalized_text, path.stem)
            else:
                title = self._extract_title_from_text(normalized_text, path.stem)
            
            return SourceDocument(
                source=str(path.name),
                title=title,
                text=normalized_text,
                file_type=file_type,
            )
        except Exception as e:
            raise ProcessingError(
                message=f"Failed to load text document: {str(e)}",
                operation="load_text",
                details={"path": str(path)},
            ) from e
    
    def _normalize_text(self, text: str) -> str:
        """Normalize extracted text."""
        text = text.replace("\x00", "")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text
    
    def _extract_title_from_markdown(self, text: str, fallback: str) -> str:
        """Extract title from markdown heading."""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("# ").strip()
        return fallback
    
    def _extract_title_from_text(self, text: str, fallback: str) -> str:
        """Extract title from first non-empty line."""
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped
        return fallback


class WordDocumentLoader(DocumentLoader):
    """Loader for Word documents."""
    
    supported_extensions = {".doc", ".docx"}
    
    def can_load(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions
    
    def load(self, path: Path) -> SourceDocument:
        try:
            raw_text = extract_word_file(path)
            normalized_text = self._normalize_text(raw_text)
            
            if not normalized_text:
                raise ProcessingError(
                    message="File is empty after extraction",
                    operation="load_word",
                )
            
            title = self._extract_title_from_text(normalized_text, path.stem)
            
            return SourceDocument(
                source=str(path.name),
                title=title,
                text=normalized_text,
                file_type="word",
            )
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(
                message=f"Failed to load Word document: {str(e)}",
                operation="load_word",
                details={"path": str(path)},
            ) from e
    
    def _normalize_text(self, text: str) -> str:
        """Normalize extracted text."""
        text = text.replace("\x00", "")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text
    
    def _extract_title_from_text(self, text: str, fallback: str) -> str:
        """Extract title from first non-empty line."""
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped
        return fallback


class PDFDocumentLoader(DocumentLoader):
    """Loader for PDF documents."""
    
    supported_extensions = {".pdf"}
    
    def can_load(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions
    
    def load(self, path: Path) -> SourceDocument:
        try:
            raw_text = extract_pdf_file(path)
            normalized_text = self._normalize_text(raw_text)
            
            if not normalized_text:
                raise ProcessingError(
                    message="File is empty after extraction",
                    operation="load_pdf",
                )
            
            title = self._extract_title_from_text(normalized_text, path.stem)
            
            return SourceDocument(
                source=str(path.name),
                title=title,
                text=normalized_text,
                file_type="pdf",
            )
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(
                message=f"Failed to load PDF document: {str(e)}",
                operation="load_pdf",
                details={"path": str(path)},
            ) from e
    
    def _normalize_text(self, text: str) -> str:
        """Normalize extracted text."""
        text = text.replace("\x00", "")
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text
    
    def _extract_title_from_text(self, text: str, fallback: str) -> str:
        """Extract title from first non-empty line."""
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped
        return fallback


class DocumentLoaderRegistry:
    """Registry for document loaders."""
    
    def __init__(self):
        self._loaders: List[DocumentLoader] = []
        self._register_default_loaders()
    
    def _register_default_loaders(self) -> None:
        """Register default document loaders."""
        self.register(TextDocumentLoader())
        self.register(WordDocumentLoader())
        self.register(PDFDocumentLoader())
    
    def register(self, loader: DocumentLoader) -> None:
        """Register a document loader."""
        self._loaders.append(loader)
    
    def get_loader(self, path: Path) -> Optional[DocumentLoader]:
        """Get appropriate loader for file path."""
        for loader in self._loaders:
            if loader.can_load(path):
                return loader
        return None
    
    def load(self, path: Path) -> SourceDocument:
        """Load document using appropriate loader."""
        loader = self.get_loader(path)
        if loader is None:
            raise ProcessingError(
                message=f"No loader available for file: {path.suffix}",
                operation="load_document",
                details={"path": str(path), "suffix": path.suffix},
            )
        return loader.load(path)
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        extensions = set()
        for loader in self._loaders:
            extensions.update(loader.supported_extensions)
        return sorted(extensions)
